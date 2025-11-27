import os
import json
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
LEXICON_PATH = os.path.join(REPO_ROOT, "data", "lexicon.json")
LOG_PATH = os.path.join(REPO_ROOT, "data", "processed_docs_log.json")

os.makedirs(CLEANED_DOCS_FOLDER, exist_ok=True)

# -------------------------------
# Load lexicon
# -------------------------------
if os.path.exists(LEXICON_PATH):
    with open(LEXICON_PATH, "r", encoding="utf-8") as f:
        lexicon = json.load(f)
else:
    lexicon = {}

term_id_counter = max([v["id"] for v in lexicon.values()], default=-1) + 1

# -------------------------------
# Load processed log
# -------------------------------
if os.path.exists(LOG_PATH):
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        processed_log = set(json.load(f))
else:
    processed_log = set()

# -------------------------------
# Scan cleaned docs
# -------------------------------
all_files = [f for f in os.listdir(CLEANED_DOCS_FOLDER) if f.endswith(".json")]
print(f"[INFO] Found {len(all_files)} cleaned JSON files.")

count_added = 0
count_skipped = 0

for filename in tqdm(all_files, desc="Building lexicon"):
    file_path = os.path.join(CLEANED_DOCS_FOLDER, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        paper_id = doc.get("paper_id")
        if not paper_id or paper_id in processed_log:
            continue

        # Combine all relevant fields for lexicon
        fields = ["title", "abstract", "sections", "text"]
        metadata_fields = ["authors", "journal"]
        tokens = []

        for field in fields:
            tokens.extend(doc.get(field, "").split())
        for meta in metadata_fields:
            tokens.extend(doc.get("metadata", {}).get(meta, "").split())

        unique_terms = set(tokens)
        for term in unique_terms:
            if term not in lexicon:
                lexicon[term] = {"id": term_id_counter, "df": 1}
                term_id_counter += 1
            else:
                lexicon[term]["df"] += 1

        processed_log.add(paper_id)
        count_added += 1

    except Exception as e:
        print(f"[WARNING] Skipping {filename}: {e}")
        count_skipped += 1

# -------------------------------
# Save lexicon and log
# -------------------------------
with open(LEXICON_PATH, "w", encoding="utf-8") as f:
    json.dump(lexicon, f, indent=2)

with open(LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(list(processed_log), f, indent=2)

print(f"[✔] Lexicon updated: {len(lexicon)} terms")
print(f"[INFO] New docs processed: {count_added}, Skipped: {count_skipped}")