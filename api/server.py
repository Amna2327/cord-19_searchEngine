"""
FastAPI backend server for CORD-19 Search Engine
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
import sys
import string
import numpy as np
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ranking import load_lexicon_and_barrels, lexical_score, hybrid_rank
from trie import load_trie

def find_repo_root(start_path=None, marker=".git"):
    """Find repository root by looking for marker or data/src folders"""
    if start_path is None:
        start_path = Path(__file__).resolve().parent.parent
    current = start_path
    while current != current.parent:
        # Check for marker (e.g., .git)
        if (current / marker).exists():
            return current
        # Fallback: check for data and src folders (project root indicator)
        if (current / "data").exists() and (current / "src").exists():
            return current
        current = current.parent
    # If we reach here, return the directory where api folder exists (parent of api)
    return Path(__file__).resolve().parent.parent

def preprocess(text):
    translator = str.maketrans("", "", string.punctuation)
    return text.lower().translate(translator).split()

# Initialize FastAPI app
app = FastAPI(title="CORD-19 Search Engine API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for loaded data
REPO_ROOT = find_repo_root()
DATA_FOLDER = REPO_ROOT / "data"
DOC_INDEX_PATH = DATA_FOLDER / "DocIndex.json"
TRIE_PATH = DATA_FOLDER / "trie.pkl"
LEXICON_PATH = DATA_FOLDER / "lexicon.json"
FAISS_INDEX_FILE = DATA_FOLDER / "faiss_index.index"
DOC_NAMES_FILE = DATA_FOLDER / "doc_names_memmap.npy"
GLOVE_MEMMAP_FILE = DATA_FOLDER / "glove_200d_memmap.npy"
WORD_INDEX_FILE = DATA_FOLDER / "glove_word_index.npy"
VECTOR_DIM = 200

# Load data structures at startup
term_info = None
barrels_folder = None
trie = None
doc_index = None
glove_vectors = None
word_index = None
index = None
doc_names = None

def query_vector(tokens):
    """Query vector (average of word vectors)"""
    if not glove_vectors or not word_index:
        return np.zeros(VECTOR_DIM, dtype='float32')
    vecs = [glove_vectors[word_index[w]] for w in tokens if w in word_index]
    if vecs:
        return np.mean(vecs, axis=0).astype('float32')
    else:
        return np.zeros(VECTOR_DIM, dtype='float32')

def semantic_score(query_vec, k=50):
    """Compute semantic scores from FAISS"""
    if index is None or doc_names is None:
        return defaultdict(float)
    
    # Check if query vector has any non-zero values
    if np.linalg.norm(query_vec) == 0:
        return defaultdict(float)

    q_vec = query_vec.reshape(1, -1).astype('float32')
    try:
        import faiss
        faiss.normalize_L2(q_vec)
        D, I = index.search(q_vec, k)
        scores = {}
        for rank, idx in enumerate(I[0]):
            doc_name = doc_names[idx]
            # Handle both string and array doc_names
            if isinstance(doc_name, (str, bytes)):
                doc_name_str = doc_name if isinstance(doc_name, str) else doc_name.decode('utf-8')
            else:
                doc_name_str = str(doc_name)
            scores[doc_name_str] = float(1 / (1 + D[0][rank]))
        return scores
    except Exception as e:
        print(f"FAISS search error: {e}")
        import traceback
        traceback.print_exc()
        return defaultdict(float)

def normalize_scores(scores):
    """Score normalization (per query) - returns scores in 0-1 range"""
    if not scores:
        return scores
    max_score = max(scores.values())
    if max_score == 0:
        return scores
    # Normalize to 0-1 range
    normalized = {doc: score / max_score for doc, score in scores.items()}
    return normalized

# Load document index
def load_doc_index():
    global doc_index
    if DOC_INDEX_PATH.exists():
        with open(DOC_INDEX_PATH, "r", encoding="utf-8") as f:
            doc_index = json.load(f)
    else:
        doc_index = {}

def get_document_path(doc_id: str) -> Optional[Path]:
    """Get the file path for a document ID - prioritizes data/docs"""
    # First try: data/docs folder (primary location)
    docs_path = DATA_FOLDER / "docs" / f"{doc_id}.json"
    if docs_path.exists():
        return docs_path
    
    # Second try: DocIndex.json mapping
    if doc_index and doc_id in doc_index:
        rel_path = doc_index[doc_id]
        # Handle both forward and backslash paths
        rel_path = rel_path.replace("\\", "/")
        abs_path = REPO_ROOT / rel_path
        if abs_path.exists():
            return abs_path
    
    # Third try: processed_docs folder
    processed_path = DATA_FOLDER / "processed_docs" / f"{doc_id}.json"
    if processed_path.exists():
        return processed_path
    
    return None

@app.on_event("startup")  # type: ignore
async def startup_event():
    """Load all necessary data structures on startup"""
    global term_info, barrels_folder, trie, doc_index, glove_vectors, word_index, index, doc_names
    
    print("Loading search engine data structures...")
    
    # Load document index
    load_doc_index()
    print(f"[OK] Loaded {len(doc_index)} document mappings")
    
    # Load lexicon and barrels
    term_info, barrels_folder = load_lexicon_and_barrels(REPO_ROOT)
    print(f"[OK] Loaded lexicon with {len(term_info)} terms")
    
    # Load trie for autocomplete
    if TRIE_PATH.exists():
        trie = load_trie(str(TRIE_PATH), str(LEXICON_PATH))
        print("[OK] Loaded trie for autocomplete")
    else:
        print("[WARNING] Trie not found, autocomplete will be unavailable")
    
    # Load FAISS index and doc names
    try:
        import faiss
        
        if FAISS_INDEX_FILE.exists() and DOC_NAMES_FILE.exists():
            index = faiss.read_index(str(FAISS_INDEX_FILE))
            doc_names = np.load(DOC_NAMES_FILE, allow_pickle=True)
            print("[OK] Loaded FAISS index")
            
            if WORD_INDEX_FILE.exists() and GLOVE_MEMMAP_FILE.exists():
                word_index = np.load(WORD_INDEX_FILE, allow_pickle=True).item()
                glove_vectors = np.memmap(
                    str(GLOVE_MEMMAP_FILE), 
                    dtype='float32', 
                    mode='r', 
                    shape=(len(word_index), VECTOR_DIM)
                )
                print("[OK] Loaded GloVe embeddings")
        else:
            print("[WARNING] FAISS index not found, semantic search will be unavailable")
    except ImportError:
        print("[WARNING] FAISS not available, semantic search will be unavailable")
    except Exception as e:
            print(f"[WARNING] Error loading FAISS index: {e}")
    
    print("[OK] Server ready!")

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 15
    alpha: Optional[float] = 0.6  # Weight for lexical vs semantic

class SearchResult(BaseModel):
    doc_id: str
    score: float
    title: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    publish_time: Optional[str] = None
    abstract: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str

class Reference(BaseModel):
    ref_id: Optional[str] = None
    bibref_id: str
    title: Optional[str] = None
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    volume: Optional[str] = None
    pages: Optional[str] = None
    issn: Optional[str] = None

class DocumentResponse(BaseModel):
    paper_id: str
    metadata: dict
    abstract: Optional[str] = None
    sections: Optional[str] = None
    text: Optional[str] = None
    references: Optional[List[Reference]] = None

@app.get("/")
async def root():
    return {
        "message": "CORD-19 Search Engine API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search",
            "autocomplete": "/api/autocomplete",
            "document": "/api/document/{doc_id}"
        }
    }

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Perform hybrid search (lexical + semantic)"""
    if not term_info:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    query = request.query.strip()
    if not query:
        return SearchResponse(results=[], total=0, query=query)
    
    print(f"Search query: '{query}'")  # Debug log
    
    # Preprocess query
    tokens = preprocess(query)
    print(f"Preprocessed tokens: {tokens}")  # Debug log
    if not tokens:
        return SearchResponse(results=[], total=0, query=query)
    
    # Lexical scores
    lex_scores = lexical_score(term_info, barrels_folder, tokens)
    print(f"Lexical scores found: {len(lex_scores)} documents")  # Debug log
    if not lex_scores:
        lex_scores = {}
    
    # Semantic scores (if available)
    sem_scores = {}
    if index is not None:
        try:
            q_vec = query_vector(tokens)
            sem_scores = semantic_score(q_vec, k=min(request.limit * 3, 100))
            print(f"Semantic scores found: {len(sem_scores)} documents")  # Debug log
        except Exception as e:
            print(f"Semantic search error: {e}")
            sem_scores = {}
    
    # Hybrid ranking
    lex_scores_norm = normalize_scores(lex_scores)
    sem_scores_norm = normalize_scores(sem_scores)
    
    alpha = request.alpha if 0 <= request.alpha <= 1 else 0.6
    ranked = hybrid_rank(lex_scores_norm, sem_scores_norm, alpha=alpha)
    print(f"Total ranked documents: {len(ranked)}")  # Debug log
    
    # Get top results with their actual scores
    top_results = ranked[:request.limit]
    
    # Debug: Print score range
    if top_results:
        scores_list = [score for _, score in top_results]
        print(f"Score range: min={min(scores_list):.4f}, max={max(scores_list):.4f}, avg={sum(scores_list)/len(scores_list):.4f}")
    
    # Helper function to extract abstract text
    def extract_abstract(doc_data):
        """Extract abstract text from various formats"""
        abstract = doc_data.get("abstract", "")
        
        # If abstract is a list of objects
        if isinstance(abstract, list):
            # Extract text from each item and join
            texts = []
            for item in abstract:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:
                        texts.append(text)
                elif isinstance(item, str):
                    texts.append(item)
            return " ".join(texts)
        # If abstract is already a string
        elif isinstance(abstract, str):
            return abstract
        return ""
    
    # Enrich with document metadata
    search_results = []
    for doc_id, score in top_results:
        doc_path = get_document_path(doc_id)
        result = SearchResult(doc_id=doc_id, score=score)
        
        if doc_path and doc_path.exists():
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                
                metadata = doc_data.get("metadata", {})
                result.title = metadata.get("title", "") or ""
                result.authors = metadata.get("authors", "") or ""
                result.journal = metadata.get("journal", "") or ""
                result.publish_time = metadata.get("publish_time", "") or ""
                
                # Extract abstract properly
                abstract_text = extract_abstract(doc_data)
                result.abstract = abstract_text[:500] if abstract_text else None  # Truncate for preview
            except Exception as e:
                print(f"Error loading document {doc_id}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Document path not found for {doc_id}: {doc_path}")  # Debug log
        
        search_results.append(result)
    
    print(f"Returning {len(search_results)} results")  # Debug log
    return SearchResponse(
        results=search_results,
        total=len(ranked),
        query=query
    )

@app.get("/api/autocomplete")
async def autocomplete(prefix: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)):
    """Get autocomplete suggestions"""
    if not trie:
        return {"suggestions": []}
    
    prefix_lower = prefix.lower().strip()
    suggestions = trie.autocomplete(prefix_lower, limit=limit)
    
    return {"suggestions": suggestions, "prefix": prefix}

@app.get("/api/document/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get full document by ID"""
    doc_path = get_document_path(doc_id)
    
    if not doc_path or not doc_path.exists():
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    def extract_text_field(data, field_name):
        """Extract text from field that might be string, list, or dict"""
        value = data.get(field_name)
        
        # If value is a list
        if isinstance(value, list):
            texts = []
            for item in value:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    if text:
                        texts.append(text)
                elif isinstance(item, str):
                    texts.append(item)
            return " ".join(texts) if texts else None
        
        # If value is a string
        elif isinstance(value, str):
            return value if value.strip() else None
        
        # If value is None or empty
        return None
    
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        
        # Extract abstract properly
        abstract = extract_text_field(doc_data, "abstract")
        
        # Extract sections
        sections = extract_text_field(doc_data, "sections")
        
        # Extract text with section structure preserved
        text = None
        body_text_items = doc_data.get("body_text")
        if isinstance(body_text_items, list) and body_text_items:
            # Format text with section headings
            formatted_parts = []
            current_section = None
            current_paragraphs = []
            
            for item in body_text_items:
                if isinstance(item, dict):
                    item_section = item.get("section", "").strip()
                    item_text = item.get("text", "").strip()
                    
                    if item_text:  # Only process if there's actual text
                        # If section changed, add previous section with heading
                        if item_section and item_section != current_section:
                            # Save previous section if exists
                            if current_section and current_paragraphs:
                                formatted_parts.append(f"##SECTION_START##{current_section}##SECTION_END##")
                                formatted_parts.append("\n\n".join(current_paragraphs))
                            
                            # Start new section
                            current_section = item_section
                            current_paragraphs = [item_text]
                        elif item_section == current_section:
                            # Same section, add to current paragraphs
                            current_paragraphs.append(item_text)
                        else:
                            # No section or empty section, continue with current
                            if current_section:
                                current_paragraphs.append(item_text)
                            else:
                                # No current section, just add as plain text
                                if current_paragraphs:
                                    formatted_parts.append("\n\n".join(current_paragraphs))
                                current_paragraphs = [item_text]
            
            # Add final section
            if current_section and current_paragraphs:
                formatted_parts.append(f"##SECTION_START##{current_section}##SECTION_END##")
                formatted_parts.append("\n\n".join(current_paragraphs))
            elif current_paragraphs:
                formatted_parts.append("\n\n".join(current_paragraphs))
            
            text = "\n\n".join(formatted_parts) if formatted_parts else None
        
        # Fallback to text field if body_text structure not available
        if not text:
            text = extract_text_field(doc_data, "text")
        if not text:
            text = extract_text_field(doc_data, "body_text")
        
        # Extract references from bib_entries
        references = []
        bib_entries = doc_data.get("bib_entries", {})
        if isinstance(bib_entries, dict):
            # Sort by BIBREF number for proper ordering
            sorted_keys = sorted(bib_entries.keys(), key=lambda x: int(x.replace("BIBREF", "")) if x.replace("BIBREF", "").isdigit() else 9999)
            for bibref_id in sorted_keys:
                entry = bib_entries[bibref_id]
                if isinstance(entry, dict):
                    # Extract authors
                    authors_str = ""
                    authors_list = entry.get("authors", [])
                    if isinstance(authors_list, list) and authors_list:
                        author_names = []
                        for author in authors_list:
                            if isinstance(author, dict):
                                parts = []
                                if author.get("first"):
                                    parts.append(author["first"])
                                if author.get("middle") and isinstance(author["middle"], list) and author["middle"]:
                                    parts.extend([str(m) for m in author["middle"] if m])
                                if author.get("last"):
                                    parts.append(author["last"])
                                if author.get("suffix"):
                                    parts.append(author["suffix"])
                                if parts:
                                    author_names.append(" ".join(parts))
                        authors_str = ", ".join(author_names) if author_names else ""
                    
                    ref = Reference(
                        ref_id=entry.get("ref_id"),
                        bibref_id=bibref_id,
                        title=entry.get("title"),
                        authors=authors_str if authors_str else None,
                        year=entry.get("year"),
                        venue=entry.get("venue"),
                        volume=entry.get("volume"),
                        pages=entry.get("pages"),
                        issn=entry.get("issn")
                    )
                    references.append(ref)
        
        # Debug log
        if text:
            print(f"Loaded full text for {doc_id}: {len(text)} characters")
        if references:
            print(f"Loaded {len(references)} references for {doc_id}")
        
        return DocumentResponse(
            paper_id=doc_data.get("paper_id", doc_id),
            metadata=doc_data.get("metadata", {}),
            abstract=abstract,
            sections=sections,
            text=text,
            references=references if references else None
        )
    except Exception as e:
        print(f"Error loading document {doc_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error loading document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

