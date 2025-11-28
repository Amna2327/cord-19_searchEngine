import os
import json
from collections import defaultdict
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
FORWARD_INDEX_PATH = os.path.join(REPO_ROOT, "data", "forward_index.json")
INVERTED_INDEX_PATH = os.path.join(REPO_ROOT, "data", "inverted_index.json")
INVERTED_LOG_PATH = os.path.join(REPO_ROOT, "data", "inverted_log.json")

# -------------------------------
# Load forward index
# -------------------------------
if not os.path.exists(FORWARD_INDEX_PATH):
    print("[ERROR] forward_index.json not found. Build forward index first.")
    exit(1)

with open(FORWARD_INDEX_PATH, "r", encoding="utf-8") as f:
    forward_index = json.load(f)

# -------------------------------
# Load existing inverted index
# -------------------------------
if os.path.exists(INVERTED_INDEX_PATH):
    with open(INVERTED_INDEX_PATH, "r", encoding="utf-8") as f:
        inverted_index = json.load(f)
else:
    inverted_index = {}

# -------------------------------
# Load inverted log
# -------------------------------
if os.path.exists(INVERTED_LOG_PATH):
    with open(INVERTED_LOG_PATH, "r", encoding="utf-8") as f:
        inverted_log = set(json.load(f))
else:
    inverted_log = set()

# -------------------------------
# Incremental build inverted index
# -------------------------------
count_added_docs = 0
count_skipped_docs = 0

for doc_id, terms_data in tqdm(forward_index.items(), desc="Updating inverted index"):
    
    # Skip DOCS already indexed
    if doc_id in inverted_log:
        count_skipped_docs += 1
        continue

    # Process NEW DOCS only
    for term_id, weight_dict in terms_data.items():

        # ensure term exists
        if term_id not in inverted_index:
            inverted_index[term_id] = {}

        # ensure doc entry exists
        if doc_id not in inverted_index[term_id]:
            inverted_index[term_id][doc_id] = {}

        # Add/merge weights
        for weight, freq in weight_dict.items():
            inverted_index[term_id][doc_id][weight] = \
                inverted_index[term_id][doc_id].get(weight, 0) + freq

    # Mark doc as processed
    inverted_log.add(doc_id)
    count_added_docs += 1

# -------------------------------
# Save updated inverted index
# -------------------------------
with open(INVERTED_INDEX_PATH, "w", encoding="utf-8") as f:
    json.dump(inverted_index, f, indent=2)

# -------------------------------
# Save updated log
# -------------------------------
with open(INVERTED_LOG_PATH, "w", encoding="utf-8") as f:
    json.dump(list(inverted_log), f, indent=2)

print("--------------------------------------------------")
print(f"[✔] Incremental inverted index build complete.")
print(f"[✔] New documents added: {count_added_docs}")
print(f"[✔] Documents skipped (already processed): {count_skipped_docs}")
print(f"[✔] Total terms in inverted index: {len(inverted_index)}")
print("--------------------------------------------------")
