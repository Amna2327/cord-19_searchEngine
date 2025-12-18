# build_trie.py
from pathlib import Path
import os
import json
from trie import Trie

# ------------------------------- Repo paths -------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = REPO_ROOT / "data"
LEXICON_PATH = DATA_FOLDER / "lexicon.json"
TRIE_PATH = DATA_FOLDER / "trie.pkl"

# ------------------------------- Load lexicon -------------------------------
if not LEXICON_PATH.exists():
    print(f"Lexicon not found at {LEXICON_PATH}")
    exit(1)

with open(LEXICON_PATH, "r", encoding="utf-8") as f:
    lexicon = json.load(f)

# ------------------------------- Build Trie -------------------------------
trie = Trie()
for term, info in lexicon.items():
    df = info.get("df", 0)
    trie.insert(term, df=df)

# ------------------------------- Save Pickle -------------------------------
os.makedirs(DATA_FOLDER, exist_ok=True)
with open(TRIE_PATH, "wb") as f:
    import pickle
    pickle.dump(trie, f)

print(f"✔ Trie built and saved at: {TRIE_PATH}")
print(f"✔ Total terms: {len(lexicon)}")
