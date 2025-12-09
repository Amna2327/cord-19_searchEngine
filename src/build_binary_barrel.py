# build_binary_barrels.py
import json
import os
from pathlib import Path
import struct
import shutil

# -------------------------------
# Repo root discovery (YOUR METHOD)
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
# Dynamic paths
# -------------------------------
DATA_FOLDER = REPO_ROOT / "data"
INVERTED_INDEX_PATH = DATA_FOLDER / "inverted_index.jsonl"
BARREL_FOLDER = DATA_FOLDER / "barrels"
LEXICON_PATH = DATA_FOLDER / "lexicon.json"

# -------------------------------
# Delete old barrels
# -------------------------------
if BARREL_FOLDER.exists():
    shutil.rmtree(BARREL_FOLDER)
BARREL_FOLDER.mkdir(parents=True, exist_ok=True)

TERMS_PER_BARREL = 10000

# -------------------------------
# Load lexicon
# -------------------------------
with open(LEXICON_PATH, "r", encoding="utf-8") as f:
    lexicon = json.load(f)

# Reverse map: termID → termString
lex_id_to_term = {str(v["id"]): k for k, v in lexicon.items() if v["id"] != -1}

# -------------------------------
# Prepare first barrel
# -------------------------------
barrel_idx = 0
terms_in_barrel = 0
current_barrel_path = BARREL_FOLDER / f"barrel_{barrel_idx}.bin"
current_barrel = open(current_barrel_path, "wb")


# -------------------------------
# Helper: write postings in binary
# -------------------------------
def write_postings_binary(f, postings):
    start_offset = f.tell()
    N = len(postings)

    # number of docs
    f.write(struct.pack(">I", N))

    for docID, weights in postings.items():
        doc_bytes = docID.encode("utf-8")

        # docID
        f.write(struct.pack(">H", len(doc_bytes)))
        f.write(doc_bytes)

        # number of weights
        f.write(struct.pack(">I", len(weights)))

        # weights
        for w in weights.values():
            f.write(struct.pack(">f", float(w)))

    return f.tell() - start_offset


# -------------------------------
# Build barrels
# -------------------------------
with open(INVERTED_INDEX_PATH, "r", encoding="utf-8") as f:
    for line in f:
        term_data = json.loads(line)

        for termID, postings in term_data.items():
            term_str = str(termID)
            term_key = lex_id_to_term.get(term_str, f"new_term_{term_str}")

            offset = current_barrel.tell()
            length = write_postings_binary(current_barrel, postings)

            # update lexicon
            lexicon[term_key] = {
                "id": lexicon.get(term_key, {}).get("id", -1),
                "df": len(postings),
                "barrel": f"barrel_{barrel_idx}.bin",
                "offset": offset,
                "length": length
            }

            terms_in_barrel += 1
            if terms_in_barrel >= TERMS_PER_BARREL:
                current_barrel.close()
                barrel_idx += 1
                terms_in_barrel = 0
                current_barrel_path = BARREL_FOLDER / f"barrel_{barrel_idx}.bin"
                current_barrel = open(current_barrel_path, "wb")

current_barrel.close()

# -------------------------------
# Save lexicon
# -------------------------------
with open(LEXICON_PATH, "w", encoding="utf-8") as f:
    json.dump(lexicon, f, indent=2)

print("[✔] Repo root:", REPO_ROOT)
print("[✔] Barrels rebuilt at:", BARREL_FOLDER)
print("[✔] Lexicon updated:", LEXICON_PATH)