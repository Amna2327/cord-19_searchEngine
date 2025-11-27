import os
import json

# -------------------------------
# Dynamically find repo root by locating .git
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
# Repo root detection
# -------------------------------
repo_root = find_repo_root()

# -------------------------------
# Paths (dynamic & OS-safe)
# -------------------------------
data_folder = os.path.join(repo_root, "data")
docs_folder = os.path.join(data_folder, "docs")
raw_docs_file = os.path.join(data_folder, "raw_docs.json")

# Create required structure
os.makedirs(data_folder, exist_ok=True)
os.makedirs(docs_folder, exist_ok=True)

# -------------------------------
# Load existing raw_docs.json (if present)
# -------------------------------
if os.path.exists(raw_docs_file):
    with open(raw_docs_file, "r", encoding="utf-8") as f:
        raw_docs = json.load(f)
else:
    raw_docs = {}

# -------------------------------
# Scan docs/ and update mapping
# -------------------------------
print(f"[INFO] Scanning {docs_folder} for JSON files...")

count_added = 0
count_skipped = 0

for filename in os.listdir(docs_folder):
    if filename.endswith(".json"):

        # Build TRUE dynamic relative path
        full_path = os.path.join(docs_folder, filename)
        relative_path = os.path.relpath(full_path, repo_root)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"[WARNING] Empty JSON skipped → {filename}")
                    count_skipped += 1
                    continue
                doc = json.loads(content)

            paper_id = doc.get("paper_id", None)
            if paper_id:
                raw_docs[paper_id] = relative_path
                count_added += 1
            else:
                print(f"[WARNING] Skipping (no paper_id) → {filename}")
                count_skipped += 1

        except Exception as e:
            print(f"[WARNING] Failed to load {filename}: {e}")
            count_skipped += 1

# -------------------------------
# Save updated mapping
# -------------------------------
with open(raw_docs_file, "w", encoding="utf-8") as f:
    json.dump(raw_docs, f, indent=2)

print(f"[✔] raw_docs.json updated: {len(raw_docs)} total entries")
print(f"[INFO] Added: {count_added}, Skipped: {count_skipped}")
