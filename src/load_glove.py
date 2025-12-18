# load_glove.py
import numpy as np
from pathlib import Path
import os

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
# Paths
# -------------------------------
GLOVE_TXT_FILE = REPO_ROOT / "data" / "glove.6B.200d.txt"
GLOVE_MEMMAP_FILE = REPO_ROOT / "data" / "glove_200d_memmap.npy"
WORD_INDEX_FILE = REPO_ROOT / "data" / "glove_word_index.npy"

VECTOR_DIM = 200

# -------------------------------
# Load or create memory-mapped GloVe vectors
# -------------------------------
if GLOVE_MEMMAP_FILE.exists() and WORD_INDEX_FILE.exists():
    print(f"Loading GloVe memmap vectors from {GLOVE_MEMMAP_FILE}...")
    word_index = np.load(WORD_INDEX_FILE, allow_pickle=True).item()
    glove_vectors = np.memmap(GLOVE_MEMMAP_FILE, dtype='float32', mode='r', shape=(len(word_index), VECTOR_DIM))
    print(f"Loaded {len(word_index)} word vectors (memory-mapped).")
else:
    print(f"{GLOVE_MEMMAP_FILE} not found. Creating memory-mapped GloVe vectors...")
    
    # First pass: count words
    num_lines = sum(1 for _ in open(GLOVE_TXT_FILE, 'r', encoding='utf-8'))
    
    # Create memmap file
    glove_vectors = np.memmap(GLOVE_MEMMAP_FILE, dtype='float32', mode='w+', shape=(num_lines, VECTOR_DIM))
    word_index = {}
    
    with open(GLOVE_TXT_FILE, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            parts = line.strip().split()
            word = parts[0]
            vector = np.array(parts[1:], dtype=np.float32)
            glove_vectors[idx] = vector
            word_index[word] = idx
            if (idx + 1) % 50000 == 0:
                print(f"Processed {idx+1} lines...")

    # Flush memmap to disk
    glove_vectors.flush()
    np.save(WORD_INDEX_FILE, word_index)
    print(f"Saved {len(word_index)} word vectors to memory-mapped file.")

# -------------------------------
# Helper function to get vector for a word
# -------------------------------
def get_vector(word):
    idx = word_index.get(word)
    if idx is not None:
        return glove_vectors[idx]
    else:
        return np.zeros(VECTOR_DIM, dtype=np.float32)