import os
import json
from collections import Counter
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
CLEANED_DOCS_FOLDER = os.path.join(REPO_ROOT, "data", "cleaned")  # <- cleaned docs folder
LEXICON_PATH = os.path.join(REPO_ROOT, "data", "lexicon.json")
FORWARD_INDEX_PATH = os.path.join(REPO_ROOT, "data", "forward_index.json")
LOG_PATH = os.path.join(REPO_ROOT, "data", "processed_docs_log.json")

os.makedirs(CLEANED_DOCS_FOLDER, exist_ok=True)

# -------------------------------
# Load lexicon
# -------------------------------
with open(LEXICON_PATH, "r", encoding="utf-8") as f:
    lexicon = json.load(f)

# -------------------------------
# Weights per section/field
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
# Load forward index
# -------------------------------
if os.path.exists(FORWARD_INDEX_PATH):
    with open(FORWARD_INDEX_PATH, "r", encoding="utf-8") as f:
        forward_index = json.load(f)
else:
    forward_index = {}

# -------------------------------
# Load processed log
# -------------------------------
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        processed_log = set(json.load(f))
else:
    processed_log = set()

# -------------------------------
# Process all cleaned docs
# -------------------------------
all_files = [f for f in os.listdir(CLEANED_DOCS_FOLDER) if f.endswith(".json")]
print(f"[INFO] Found {len(all_files)} cleaned JSON files.")

count_added = 0
count_skipped = 0

for filename in tqdm(all_files, desc="Building forward index"):
    file_path = os.path.join(CLEANED_DOCS_FOLDER, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)

        paper_id = doc.get("paper_id")
        if not paper_id or paper_id in forward_index:
            # Skip if missing paper_id or already in forward index
            count_skipped += 1
            continue

        if paper_id not in processed_log:
            # Only process if doc is in processed log (incremental)
            count_skipped += 1
            continue

        forward_index.setdefault(paper_id, {})

        # Iterate over all weighted fields
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
                term_id = str(lexicon.get(term, {}).get("id", -1))
                if term_id == "-1":
                    continue

                term_data = forward_index[paper_id].setdefault(term_id, {})
                term_data[str(weight)] = term_data.get(str(weight), 0) + freq

        count_added += 1

    except Exception as e:
        print(f"[WARNING] Skipping {filename}: {e}")
        count_skipped += 1

# -------------------------------
# Save forward index
# -------------------------------
with open(FORWARD_INDEX_PATH, "w", encoding="utf-8") as f:
    json.dump(forward_index, f, indent=2)

print(f"[✔] Forward index updated for {len(forward_index)} documents")
print(f"[INFO] New docs processed: {count_added}, Skipped: {count_skipped}")
