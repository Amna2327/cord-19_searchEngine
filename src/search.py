import numpy as np
import faiss
from pathlib import Path
from ranking import load_lexicon_and_barrels, lexical_score, hybrid_rank
import string
from collections import defaultdict

# -------------------------------
# Dynamic repo root
# -------------------------------
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    current = start_path
    while current != current.parent:
        if (current / marker).exists():
            return current
        current = current.parent
    raise FileNotFoundError(f"Repo root containing {marker} not found")

REPO_ROOT = find_repo_root()

# -------------------------------
# Paths
# -------------------------------
DATA_FOLDER = REPO_ROOT / "data"
FAISS_INDEX_FILE = DATA_FOLDER / "faiss_index.index"
DOC_NAMES_FILE = DATA_FOLDER / "doc_names_memmap.npy"
GLOVE_MEMMAP_FILE = DATA_FOLDER / "glove_200d_memmap.npy"
WORD_INDEX_FILE = DATA_FOLDER / "glove_word_index.npy"

# -------------------------------
# Load FAISS index and doc names
# -------------------------------
index = faiss.read_index(str(FAISS_INDEX_FILE))
doc_names = np.load(DOC_NAMES_FILE, allow_pickle=True)

# -------------------------------
# Load lexicon and barrels
# -------------------------------
term_info, barrels_folder = load_lexicon_and_barrels(REPO_ROOT)

# -------------------------------
# Load GloVe memory-mapped
# -------------------------------
word_index = np.load(WORD_INDEX_FILE, allow_pickle=True).item()
VECTOR_DIM = 200  # or derive from memmap shape
glove_vectors = np.memmap(GLOVE_MEMMAP_FILE, dtype='float32', mode='r', shape=(len(word_index), VECTOR_DIM))

# -------------------------------
# Preprocessing
# -------------------------------
translator = str.maketrans("", "", string.punctuation)
def preprocess(text):
    return text.lower().translate(translator).split()

# -------------------------------
# Query vector (average of word vectors)
# -------------------------------
def query_vector(tokens):
    vecs = [glove_vectors[word_index[w]] for w in tokens if w in word_index]
    if vecs:
        return np.mean(vecs, axis=0).astype('float32')
    else:
        return np.zeros(VECTOR_DIM, dtype='float32')

# -------------------------------
# Compute semantic scores from FAISS
# -------------------------------
def semantic_score(query_vec, k=50):
    """
    Returns a dictionary of docID -> semantic score
    using FAISS index similarity.
    """
    if np.linalg.norm(query_vec) == 0:
        return defaultdict(float)

    q_vec = query_vec.reshape(1, -1)
    faiss.normalize_L2(q_vec)

    D, I = index.search(q_vec, k)
    scores = {}
    for rank, idx in enumerate(I[0]):
        # Similarity normalization (optional: 1/(1+D) or just cosine similarity)
        scores[doc_names[idx]] = 1 / (1 + D[0][rank])
    return scores

# -------------------------------
# Score normalization (per query)
# -------------------------------
def normalize_scores(scores):
    if not scores:
        return scores

    max_score = max(scores.values())
    if max_score == 0:
        return scores

    return {doc: score / max_score for doc, score in scores.items()}

# -------------------------------
# Main interactive search
# -------------------------------
if __name__ == "__main__":
    print("Hybrid search ready. Type your query or 'exit'.")

    while True:
        query = input("\nEnter query: ").strip()
        if query.lower() == "exit":
            break
        if not query:
            print("Empty query, try again.")
            continue

        tokens = preprocess(query)

        # Lexical scores
        lex_scores = lexical_score(term_info, barrels_folder, tokens)
        if not lex_scores:
            lex_scores = defaultdict(float)

        # Semantic scores
        q_vec = query_vector(tokens)
        sem_scores = semantic_score(q_vec, k=50)

        # Hybrid ranking
        lex_scores = normalize_scores(lex_scores)
        sem_scores = normalize_scores(sem_scores)

        ranked = hybrid_rank(lex_scores, sem_scores, alpha=0.6)

        if not ranked:
            print("No results found for this query.")
            continue

        # Display top results
        print("\nTop 15 hybrid results:")
        for doc, score in ranked[:15]:
            print(f"{doc} -> score: {score:.4f}")