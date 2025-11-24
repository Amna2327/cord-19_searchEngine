import os
import json

# -------------------------------
# Determine repo root (one level above src/)
# -------------------------------
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# -------------------------------
# Paths
# -------------------------------
data_folder = os.path.join(repo_root, "data")
docs_folder = os.path.join(data_folder, "docs")
raw_docs_file = os.path.join(data_folder, "raw_docs.json")

# Ensure folders exist
os.makedirs(docs_folder, exist_ok=True)
os.makedirs(data_folder, exist_ok=True)

# -------------------------------
# Load existing raw_docs.json if exists
# -------------------------------
if os.path.exists(raw_docs_file):
    with open(raw_docs_file, "r", encoding="utf-8") as f:
        raw_docs = json.load(f)
else:
    raw_docs = {}

# -------------------------------
# Scan all JSONs in docs folder
# -------------------------------
print(f"[INFO] Scanning {docs_folder} for JSON documents...")
count_skipped = 0
count_added = 0

for filename in os.listdir(docs_folder):
    if filename.endswith(".json"):
        filepath = os.path.join("data/docs", filename)  # store relative path
        try:
            with open(os.path.join(docs_folder, filename), "r", encoding="utf-8") as f:
                doc = json.load(f)
            paper_id = doc.get("paper_id")
            if paper_id:
                raw_docs[paper_id] = filepath
                count_added += 1
            else:
                count_skipped += 1
        except Exception as e:
            print(f"[WARNING] Skipping {filename}: {e}")
            count_skipped += 1

# -------------------------------
# Save updated dictionary
# -------------------------------
with open(raw_docs_file, "w", encoding="utf-8") as f:
    json.dump(raw_docs, f, indent=2)

print(f"[✔] Raw docs dictionary built/updated: {len(raw_docs)} entries")
print(f"[INFO] Files skipped: {count_skipped}, Files added: {count_added}")