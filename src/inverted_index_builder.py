import os
from pathlib import Path
import shutil
import heapq
from tqdm import tqdm
import orjson

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
TEMP_DIR = REPO_ROOT / "data" / "inverted_temp_chunks"
FINAL_INVERTED = REPO_ROOT / "data" / "inverted_index.jsonl"
FORWARD_LOG = REPO_ROOT / "data" / "forward_index_log.json"
INVERTED_LOG = REPO_ROOT / "data" / "inverted_index_log.json"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------
# Load logs
# -------------------------------
forward_log = set()
if FORWARD_LOG.exists():
    with open(FORWARD_LOG, "r", encoding="utf-8") as f:
        forward_log = set(orjson.loads(f.read()))

inverted_log = set()
if INVERTED_LOG.exists():
    with open(INVERTED_LOG, "r", encoding="utf-8") as f:
        inverted_log = set(orjson.loads(f.read()))

# -------------------------------
# Step 1: Write temp JSONL from forward batches
# -------------------------------
TEMP_JSONL = TEMP_DIR / "inverted_temp.jsonl"
with open(TEMP_JSONL, "w", encoding="utf-8") as temp_file:
    all_batches = sorted(FORWARD_FOLDER.glob("forward_batch_*.json"))
    for batch_path in tqdm(all_batches, desc="Writing temp JSONL"):
        with open(batch_path, "r", encoding="utf-8") as f:
            batch_data = orjson.loads(f.read())

        for docID, per_doc_terms in batch_data.items():
            if docID not in forward_log or docID in inverted_log:
                continue
            for termID, weights in per_doc_terms.items():
                record = {"termID": termID, "docID": docID, "weights": weights}
                temp_file.write(orjson.dumps(record).decode() + "\n")
            inverted_log.add(docID)

# Save updated inverted log
with open(INVERTED_LOG, "w", encoding="utf-8") as f:
    f.write(orjson.dumps(list(inverted_log)).decode())

print("[INFO] Temp JSONL created")

# -------------------------------
# Step 2: External merge sort
# -------------------------------
CHUNK_SIZE = 100_000  # lines per chunk
chunk_files = []

print("[INFO] Splitting and sorting chunks")
with open(TEMP_JSONL, "r", encoding="utf-8") as f:
    lines = []
    for i, line in enumerate(f, 1):
        lines.append(line)
        if i % CHUNK_SIZE == 0:
            lines.sort(key=lambda x: orjson.loads(x)["termID"])
            chunk_path = TEMP_DIR / f"chunk_{len(chunk_files)}.jsonl"
            with open(chunk_path, "w", encoding="utf-8") as cf:
                cf.writelines(lines)
            chunk_files.append(chunk_path)
            lines = []
    # Last chunk
    if lines:
        lines.sort(key=lambda x: orjson.loads(x)["termID"])
        chunk_path = TEMP_DIR / f"chunk_{len(chunk_files)}.jsonl"
        with open(chunk_path, "w", encoding="utf-8") as cf:
            cf.writelines(lines)
        chunk_files.append(chunk_path)

print(f"[INFO] {len(chunk_files)} sorted chunks created")

# -------------------------------
# Step 3: Merge sorted chunks into final term-centric index (optimized)
# -------------------------------
print("[INFO] Merging chunks into final inverted index (buffered)")

BUFFER_SIZE = 5000  # lines per chunk buffer
file_iters = [open(cf, "r", encoding="utf-8") for cf in chunk_files]
chunk_buffers = []

# Preload buffer for each chunk
for it in file_iters:
    buf = []
    for _ in range(BUFFER_SIZE):
        line = it.readline()
        if not line:
            break
        buf.append(orjson.loads(line))
    chunk_buffers.append(buf)

heap = []
for idx, buf in enumerate(chunk_buffers):
    if buf:
        rec = buf.pop(0)
        heapq.heappush(heap, (rec["termID"], idx, rec))

with open(FINAL_INVERTED, "w", encoding="utf-8") as out_file:
    current_term = None
    term_postings = {}

    while heap:
        termID, idx, rec = heapq.heappop(heap)
        docID = rec["docID"]
        weights = rec["weights"]

        if termID != current_term:
            if current_term is not None:
                out_file.write(orjson.dumps({current_term: term_postings}).decode() + "\n")
            current_term = termID
            term_postings = {}

        term_postings[docID] = weights

        # Refill heap from buffer or file
        if chunk_buffers[idx]:
            next_rec = chunk_buffers[idx].pop(0)
            heapq.heappush(heap, (next_rec["termID"], idx, next_rec))
        else:
            for _ in range(BUFFER_SIZE):
                line = file_iters[idx].readline()
                if not line:
                    break
                chunk_buffers[idx].append(orjson.loads(line))
            if chunk_buffers[idx]:
                next_rec = chunk_buffers[idx].pop(0)
                heapq.heappush(heap, (next_rec["termID"], idx, next_rec))

# Write last term
if term_postings:
    with open(FINAL_INVERTED, "a", encoding="utf-8") as out_file:
        out_file.write(orjson.dumps({current_term: term_postings}).decode() + "\n")

# Cleanup
for f in file_iters:
    f.close()
shutil.rmtree(TEMP_DIR)

print(f"[✔] Final inverted index saved at {FINAL_INVERTED}")