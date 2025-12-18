<<<<<<< HEAD
# build_trie.py
from pathlib import Path
import os
import json
=======
from pathlib import Path
import os
import json
import pickle
>>>>>>> eda65d3b3a5408269ab54414d3eb2511177d59a6
from trie import Trie

# ------------------------------- Repo paths -------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = REPO_ROOT / "data"
LEXICON_PATH = DATA_FOLDER / "lexicon.json"
<<<<<<< HEAD
TRIE_PATH = DATA_FOLDER / "trie.pkl"
=======

# ------------------------------- Output path (atomic-aware) -------------------------------
TRIE_OUTPUT_DIR = os.environ.get("TRIE_OUTPUT_DIR")
if TRIE_OUTPUT_DIR:
    TRIE_PATH = Path(TRIE_OUTPUT_DIR) / "trie.pkl"
else:
    TRIE_PATH = DATA_FOLDER / "trie.pkl"

# Ensure output directory exists
TRIE_PATH.parent.mkdir(parents=True, exist_ok=True)
>>>>>>> eda65d3b3a5408269ab54414d3eb2511177d59a6

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
<<<<<<< HEAD
os.makedirs(DATA_FOLDER, exist_ok=True)
with open(TRIE_PATH, "wb") as f:
    import pickle
    pickle.dump(trie, f)

print(f"✔ Trie built and saved at: {TRIE_PATH}")
print(f"✔ Total terms: {len(lexicon)}")
=======
with open(TRIE_PATH, "wb") as f:
    pickle.dump(trie, f)

print(f"[✔] Trie built at: {TRIE_PATH}")
print(f"[✔] Total terms: {len(lexicon)}")
>>>>>>> eda65d3b3a5408269ab54414d3eb2511177d59a6
