# vectorize_and_index_incremental.py
import json
import numpy as np
import faiss
from pathlib import Path
import os

# ---------------- Repo root ----------------
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    cur = start_path
    while cur != cur.parent:
        if (cur / marker).exists():
            return cur
        cur = cur.parent
    raise RuntimeError("Repo root not found")

REPO_ROOT = find_repo_root()

# ---------------- Paths ----------------
CLEANED_DOCS = REPO_ROOT / "data" / "cleaned"
DATA = REPO_ROOT / "data"

DOC_VECTORS_FILE = DATA / "doc_vectors_memmap.npy"
DOC_NAMES_FILE = DATA / "doc_names_memmap.npy"
FAISS_INDEX_FILE = DATA / "faiss_index.index"

GLOVE_FILE = DATA / "glove_200d_memmap.npy"
WORD_INDEX_FILE = DATA / "glove_word_index.npy"

VECTOR_DIM = 200
BATCH_SIZE = 500  # Tune to RAM

# ---------------- Load GloVe ----------------
word_index = np.load(WORD_INDEX_FILE, allow_pickle=True).item()
glove_vectors = np.memmap(GLOVE_FILE, dtype='float32', mode='r', shape=(len(word_index), VECTOR_DIM))

def word_vec(w):
    idx = word_index.get(w)
    return glove_vectors[idx] if idx is not None else None

# ---------------- Load existing vectors ----------------
if DOC_NAMES_FILE.exists() and DOC_VECTORS_FILE.exists():
    doc_names = np.load(DOC_NAMES_FILE, allow_pickle=True).tolist()
    existing_set = set(doc_names)
    doc_vectors = np.load(DOC_VECTORS_FILE, mmap_mode='r')
    print(f"[INFO] Loaded {len(doc_names)} existing vectors.")
else:
    doc_names = []
    existing_set = set()
    doc_vectors = None
    print("[INFO] No existing vectors found, starting fresh.")

# ---------------- Identify new docs ----------------
new_files = [p for p in CLEANED_DOCS.glob("*.json") if p.name not in existing_set]
if not new_files:
    print("[INFO] No new documents to vectorize.")
else:
    print(f"[INFO] {len(new_files)} new documents detected.")

# ---------------- Prepare FAISS index ----------------
if FAISS_INDEX_FILE.exists():
    index = faiss.read_index(str(FAISS_INDEX_FILE))
    indexed_count = index.ntotal
    print(f"[INFO] Loaded existing FAISS index with {indexed_count} vectors.")
else:
    index = faiss.IndexFlatIP(VECTOR_DIM)  # Use cosine similarity
    indexed_count = 0
    print("[INFO] Created new FAISS index.")

# ---------------- Vectorize in batches ----------------
new_vectors_list = []
new_names_list = []

for start in range(0, len(new_files), BATCH_SIZE):
    batch_files = new_files[start:start+BATCH_SIZE]
    batch_vectors = []
    for fpath in batch_files:
        with open(fpath, "r", encoding="utf-8") as f:
            text = json.load(f).get("text", "")
        words = text.lower().split()
        vecs = [word_vec(w) for w in words if word_vec(w) is not None]
        doc_vec = np.mean(vecs, axis=0) if vecs else np.zeros(VECTOR_DIM, dtype='float32')
        batch_vectors.append(doc_vec.astype('float32'))
        doc_names.append(fpath.name)
    batch_vectors = np.vstack(batch_vectors)
    new_vectors_list.append(batch_vectors)
    new_names_list.extend([f.name for f in batch_files])
    print(f"[INFO] Vectorized batch {start//BATCH_SIZE + 1}/{(len(new_files)+BATCH_SIZE-1)//BATCH_SIZE}")

# ---------------- Update doc_vectors memmap ----------------
if new_vectors_list:
    all_new_vectors = np.vstack(new_vectors_list)
    if doc_vectors is None:
        np.save(DOC_VECTORS_FILE, all_new_vectors)
    else:
        merged = np.memmap(DATA / "doc_vectors.tmp.npy", dtype='float32', mode='w+',
                           shape=(doc_vectors.shape[0] + all_new_vectors.shape[0], VECTOR_DIM))
        merged[:doc_vectors.shape[0]] = doc_vectors
        merged[doc_vectors.shape[0]:] = all_new_vectors
        del merged
        os.replace(DATA / "doc_vectors.tmp.npy", DOC_VECTORS_FILE)
    np.save(DOC_NAMES_FILE, np.array(doc_names, dtype=object))
    print(f"[✔] Updated document vectors: {len(doc_names)} total.")

# ---------------- Add new vectors to FAISS ----------------
if new_vectors_list:
    all_new_vectors = np.vstack(new_vectors_list)
    faiss.normalize_L2(all_new_vectors)
    index.add(all_new_vectors)
    faiss.write_index(index, str(FAISS_INDEX_FILE))
    print(f"[✔] FAISS index updated: {index.ntotal} total vectors.")