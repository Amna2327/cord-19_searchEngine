import os
import json
from pathlib import Path
from collections import Counter, defaultdict
from tqdm import tqdm

# -------------------------------
# Configuration
# -------------------------------
BATCH_SIZE = 500 
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = os.path.abspath(os.path.dirname(__file__))
    current = start_path
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, marker)):
            return Path(current)
        current = os.path.dirname(current)
    raise FileNotFoundError(f"Could not find repo root containing {marker}")

REPO_ROOT = find_repo_root() # number of docs per forward file
CLEANED_DOCS_FOLDER = REPO_ROOT / "data" / "cleaned"
FORWARD_FOLDER = REPO_ROOT / "data" / "forward_index"
LEXICON_PATH = REPO_ROOT / "data" / "lexicon.json"
FORWARD_LOG_PATH = REPO_ROOT / "data" / "forward_index_log.json"

# Ensure folders exist
FORWARD_FOLDER.mkdir(parents=True, exist_ok=True)
CLEANED_DOCS_FOLDER.mkdir(parents=True, exist_ok=True)

# -------------------------------
# Load lexicon
# -------------------------------
if not LEXICON_PATH.exists():
    raise FileNotFoundError(f"Lexicon not found: {LEXICON_PATH}")
with open(LEXICON_PATH, "r", encoding="utf-8") as f:
    lexicon = json.load(f)

# -------------------------------
# Load forward log
# -------------------------------
if FORWARD_LOG_PATH.exists():
    with open(FORWARD_LOG_PATH, "r", encoding="utf-8") as f:
        forward_log = set(json.load(f))
else:
    forward_log = set()

# -------------------------------
# Field weights
# -------------------------------
weights = {
    "title": 5,
    "abstract": 4,
    "sections": 3,
    "authors": 2,
    "journal": 2,
    "text": 1
}

# -------------------------------
# Processing
# -------------------------------
all_files = sorted(CLEANED_DOCS_FOLDER.glob("*.json"))
print(f"[INFO] Found {len(all_files)} cleaned docs")

batch = {}
batch_number = 0
count_added = 0
count_skipped = 0
incremental_log_update = 50  # save log every N docs

for idx, file_path in enumerate(tqdm(all_files, desc="Forward Indexing")):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        paper_id = doc.get("paper_id")
        if not paper_id:
            count_skipped += 1
            continue

        if paper_id in forward_log:
            count_skipped += 1
            continue

        # ========== BUILD PER-DOC FORWARD INDEX ==========
        per_doc_index = {}
        for field, weight in weights.items():
            if field in ["title", "authors", "journal"]:
                text = doc.get("metadata", {}).get(field, "")
            else:
                text = doc.get(field, "")

            if not text:
                continue

            tokens = text.split()
            counter = Counter(tokens)
            for term, freq in counter.items():
                term_info = lexicon.get(term)
                if not term_info:
                    continue
                term_id = str(term_info["id"])
                per_doc_index.setdefault(term_id, {})
                per_doc_index[term_id].setdefault(str(weight), 0)
                per_doc_index[term_id][str(weight)] += freq
        # =================================================

        batch[paper_id] = per_doc_index
        forward_log.add(paper_id)
        count_added += 1

        # Write batch if full
        if len(batch) >= BATCH_SIZE:
            batch_file = FORWARD_FOLDER / f"forward_batch_{batch_number}.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch, f, indent=2)
            batch.clear()
            batch_number += 1

            # Incremental save of forward log
            with open(FORWARD_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(list(forward_log), f, indent=2)

    except Exception as e:
        print(f"[WARNING] Error processing {file_path.name}: {e}")
        count_skipped += 1

# Write any remaining docs in the last batch
if batch:
    batch_file = FORWARD_FOLDER / f"forward_batch_{batch_number}.json"
    with open(batch_file, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2)

# Final forward log save
with open(FORWARD_LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(list(forward_log), f, indent=2)

print("\n[✔] Forward index building complete")
print(f"[INFO] Total newly indexed docs: {count_added}")
print(f"[INFO] Total skipped docs: {count_skipped}")
print(f"[INFO] Total batches written: {batch_number + (1 if batch else 0)}")
