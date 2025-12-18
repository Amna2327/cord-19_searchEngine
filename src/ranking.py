# ranking.py
import json
import struct
from pathlib import Path
from collections import defaultdict
import numpy as np

# -------------------------------
# Repo root discovery
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
# Load barrels and lexicon
# -------------------------------
def load_lexicon_and_barrels(repo_root=REPO_ROOT):
    DATA_FOLDER = repo_root / "data"
    BARREL_FOLDER = DATA_FOLDER / "barrels"
    LEXICON_PATH = DATA_FOLDER / "lexicon.json"

    with open(LEXICON_PATH, "r", encoding="utf-8") as f:
        lexicon = json.load(f)

    # Filter terms that actually have barrel info
    term_info = {term: info for term, info in lexicon.items() if "barrel" in info}
    return term_info, BARREL_FOLDER

# -------------------------------
# Read postings for a term
# -------------------------------
def read_postings(term_info, barrels_folder, term):
    if term not in term_info:
        return {}

    info = term_info[term]
    barrel_path = barrels_folder / info["barrel"]
    offset = info["offset"]

    postings = {}
    with open(barrel_path, "rb") as f:
        f.seek(offset)
        N_bytes = f.read(4)
        if not N_bytes:
            return {}
        N = struct.unpack(">I", N_bytes)[0]

        for _ in range(N):
            len_doc_bytes = struct.unpack(">H", f.read(2))[0]
            docID = f.read(len_doc_bytes).decode("utf-8")
            M = struct.unpack(">I", f.read(4))[0]
            section_freqs = {}
            for _ in range(M):
                section_id = struct.unpack(">I", f.read(4))[0]
                freq = struct.unpack(">f", f.read(4))[0]
                section_freqs[section_id] = freq
            postings[docID] = section_freqs

    return postings

# -------------------------------
# Lexical score computation
# -------------------------------
def lexical_score(term_info, barrels_folder, query_terms):
    """
    Compute lexical score for a list of query terms using forward index structure:
    term_id -> {weight: freq}
    """
    scores = defaultdict(float)

    for term in query_terms:
        postings = read_postings(term_info, barrels_folder, term)
        if not postings:
            continue

        df = len(postings)  # document frequency for IDF

        for docID, weight_freqs in postings.items():
            weighted_tf = sum(freq * int(weight) for weight, freq in weight_freqs.items())
            scores[docID] += weighted_tf / df  # TF * IDF

    return scores
# -------------------------------
# Hybrid ranking: combine lexical + semantic
# -------------------------------
def hybrid_rank(lexical_scores, semantic_scores, alpha=0.5):
    """
    alpha = weight for lexical
    1-alpha = weight for semantic
    """
    final_scores = {}
    all_docs = set(lexical_scores.keys()).union(semantic_scores.keys())
    for doc in all_docs:
        lex = lexical_scores.get(doc, 0)
        sem = semantic_scores.get(doc, 0)
        final_scores[doc] = alpha * lex + (1 - alpha) * sem

    # Sort descending
    ranked_docs = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked_docs

# -------------------------------
# Example usage (optional)
# -------------------------------
if __name__ == "__main__":
    term_info, barrel_folder = load_lexicon_and_barrels()
    query = ["cancer", "therapy"]
    lex_scores = lexical_score(term_info, barrel_folder, query)

    # Suppose semantic_scores comes from FAISS
    semantic_scores = {"doc1.json": 0.8, "doc2.json": 0.6}

    ranked = hybrid_rank(lex_scores, semantic_scores, alpha=0.6)
    print("Top ranked docs:", ranked[:10])