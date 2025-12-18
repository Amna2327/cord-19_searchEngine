import os
import json
import heapq
from pathlib import Path
from tqdm import tqdm

# -------------------------------
# Repo root discovery
# -------------------------------
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = os.path.abspath(os.path.dirname(__file__))
    current = start_path
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, marker)):
            return Path(current)
        current = os.path.dirname(current)
    raise FileNotFoundError(f"Could not find repo root containing {marker}")

REPO_ROOT = find_repo_root()

# -------------------------------
# Paths
# -------------------------------
FORWARD_FOLDER = REPO_ROOT / "data" / "forward_index"
INVERTED_INDEX_PATH = REPO_ROOT / "data" / "inverted_index.jsonl"
FORWARD_LOG_PATH = REPO_ROOT / "data" / "forward_index_log.json"
INVERTED_LOG_PATH = REPO_ROOT / "data" / "inverted_log.json"

# -------------------------------
# Load logs
# -------------------------------
forward_log = set()
if FORWARD_LOG_PATH.exists():
    with open(FORWARD_LOG_PATH, "r", encoding="utf-8") as f:
        forward_log = set(json.load(f))

inverted_log = set()
if INVERTED_LOG_PATH.exists():
    with open(INVERTED_LOG_PATH, "r", encoding="utf-8") as f:
        inverted_log = set(json.load(f))

# -------------------------------
# Load forward batches into memory
# -------------------------------
all_records = []  # will store (termID, docID, weights)
all_batches = sorted(FORWARD_FOLDER.glob("forward_batch_*.json"))

for batch_path in tqdm(all_batches, desc="Loading forward batches"):
    with open(batch_path, "r", encoding="utf-8") as f:
        batch_data = json.load(f)

    for docID, per_doc_terms in batch_data.items():
        if docID not in forward_log or docID in inverted_log:
            continue
        for termID, weights in per_doc_terms.items():
            all_records.append((termID, docID, weights))
        inverted_log.add(docID)

# -------------------------------
# Chunking & sorting
# -------------------------------
CHUNK_SIZE = 100_000
chunks = []
for i in range(0, len(all_records), CHUNK_SIZE):
    chunk = all_records[i:i+CHUNK_SIZE]
    chunk.sort(key=lambda x: x[0])  # sort by termID
    chunks.append(chunk)

# -------------------------------
# Merge chunks using heap
# -------------------------------
print("[INFO] Merging chunks into final inverted index...")
heap = []
for idx, chunk in enumerate(chunks):
    if chunk:
        heapq.heappush(heap, (chunk.pop(0), idx))

final_inverted_index = {}
buffers = chunks  # reuse for remaining items

with open(INVERTED_INDEX_PATH, "w", encoding="utf-8") as out_file:
    current_term = None
    term_postings = {}

    while heap:
        (termID, docID, weights), idx = heapq.heappop(heap)
        if termID != current_term:
            if current_term is not None:
                out_file.write(json.dumps({current_term: term_postings}) + "\n")
            current_term = termID
            term_postings = {}
        term_postings[docID] = weights

        # Refill heap from the same chunk
        if buffers[idx]:
            heapq.heappush(heap, (buffers[idx].pop(0), idx))

    # write last term
    if term_postings:
        out_file.write(json.dumps({current_term: term_postings}) + "\n")

# -------------------------------
# Save inverted log
# -------------------------------
with open(INVERTED_LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(list(inverted_log), f, indent=2)

print(f"[✔] Inverted index saved at {INVERTED_INDEX_PATH}")
print(f"[INFO] Docs processed: {len(inverted_log)}")