import os
import json
from collections import Counter
from pathlib import Path
from tqdm import tqdm

# -------------------------------
# Dynamically find repo root
# -------------------------------
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = os.path.abspath(os.path.dirname(__file__))
    current = start_path
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, marker)):
            return current
        current = os.path.dirname(current)
    raise FileNotFoundError(f"Could not find repo root containing {marker}")


# -------------------------------
# Paths
# -------------------------------
REPO_ROOT = find_repo_root()

CLEANED_DOCS_FOLDER = os.path.join(REPO_ROOT, "data", "cleaned")
FORWARD_FOLDER = os.path.join(REPO_ROOT, "data", "forward_index")
os.makedirs(FORWARD_FOLDER, exist_ok=True)

LEXICON_PATH = os.path.join(REPO_ROOT, "data", "lexicon.json")
LEXICON_LOG_PATH = os.path.join(REPO_ROOT, "data", "lexicon_log.json")
FORWARD_LOG_PATH = os.path.join(REPO_ROOT, "data", "forward_index_log.json")


# -------------------------------
# Load lexicon
# -------------------------------
with open(LEXICON_PATH, "r", encoding="utf-8") as f:
    lexicon = json.load(f)


# -------------------------------
# Load logs
# -------------------------------
if os.path.exists(LEXICON_LOG_PATH):
    with open(LEXICON_LOG_PATH, "r", encoding="utf-8") as f:
        lexicon_log = set(json.load(f))
else:
    lexicon_log = set()

if os.path.exists(FORWARD_LOG_PATH):
    with open(FORWARD_LOG_PATH, "r", encoding="utf-8") as f:
        forward_log = set(json.load(f))
else:
    forward_log = set()


# -------------------------------
# Weights per field
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
# Process cleaned docs (improved file scanning)
# -------------------------------
all_files = list(Path(CLEANED_DOCS_FOLDER).glob("*.json"))
print(f"[INFO] Found {len(all_files)} cleaned docs")

count_added = 0
count_skipped = 0
incremental_log_update = 50  # save log every N files

for idx, file_path in enumerate(tqdm(all_files, desc="Forward Indexing")):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        paper_id = doc.get("paper_id")
        if not paper_id:
            count_skipped += 1
            continue

        forward_file = os.path.join(FORWARD_FOLDER, f"{paper_id}.json")

        # ---- Key Logic ----
        if paper_id not in lexicon_log:
            count_skipped += 1
            continue

        if paper_id in forward_log or os.path.exists(forward_file):
            count_skipped += 1
            continue
        # -------------------

        # ========== BUILD FORWARD INDEX (PER DOC) ==========
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
        # ===================================================

        # Save this doc's forward index
        with open(forward_file, "w", encoding="utf-8") as f:
            json.dump(per_doc_index, f, indent=2)

        forward_log.add(paper_id)
        count_added += 1

        # Incremental save of forward log every N files
        if (idx + 1) % incremental_log_update == 0:
            with open(FORWARD_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(list(forward_log), f, indent=2)

    except Exception as e:
        print(f"[WARNING] Error in {file_path.name}: {e}")
        count_skipped += 1


# -------------------------------
# Save final forward log
# -------------------------------
with open(FORWARD_LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(list(forward_log), f, indent=2)

print(f"\n[✔] Forward index updated")
print(f"[INFO] Newly indexed docs: {count_added}")
print(f"[INFO] Skipped docs: {count_skipped}")