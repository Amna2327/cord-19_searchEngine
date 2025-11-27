import os
import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import PunktSentenceTokenizer, word_tokenize

# ----------------------------
# NLTK setup
# ----------------------------
nltk.data.path.append(os.path.expanduser(r"~\AppData\Roaming\nltk_data"))
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

# ----------------------------
# Headings to ignore in sections
# ----------------------------
IGNORE_HEADINGS = {
    "introduction", "background", "methods", "methodology", "materials and methods",
    "acknowledgements", "funding", "conflict of interest", "competing interests",
    "author contributions", "references", "bibliography", "supplementary information",
    "supplementary materials", "appendix", "appendices", "conclusion"
}

# ----------------------------
# Initialize lemmatizer and stopwords
# ----------------------------
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))
punkt_sent_tokenizer = PunktSentenceTokenizer()

# ----------------------------
# Cleaning function
# ----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = []
    for sent in punkt_sent_tokenizer.tokenize(text):
        tokens.extend(word_tokenize(sent))

    cleaned_tokens = [
        lemmatizer.lemmatize(w, pos='v') 
        for w in tokens 
        if w not in stop_words
    ]
    return " ".join(cleaned_tokens)

# ----------------------------
# Process a single JSON file (SAFE)
# ----------------------------
def preprocess_file(file_path, cleaned_folder):

    # Handle empty / invalid JSON safely
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                print(f"Skipping EMPTY file → {file_path}")
                return
            data = json.loads(raw)
    except Exception as e:
        print(f"Skipping INVALID JSON → {file_path} ({e})")
        return

    # Metadata handling
    paper_id = data.get("paper_id", "")
    metadata = data.get("metadata", {})

    cleaned_metadata = {}
    for key in ["title", "authors", "journal"]:
        value = metadata.get(key, "")
        cleaned_metadata[key] = clean_text(value) if value else ""
    cleaned_metadata["publish_time"] = metadata.get("publish_time", "")

    # Abstract
    abstract_text = ""
    abstract_raw = data.get("abstract", "")
    if isinstance(abstract_raw, list):
        abstract_text = clean_text(" ".join([p.get("text", "") for p in abstract_raw]))
    elif isinstance(abstract_raw, str):
        abstract_text = clean_text(abstract_raw)

    # Section headings
    sections_set = set()
    body_items = data.get("body_text", [])

    if isinstance(body_items, list):
        for item in body_items:
            heading = item.get("section", "")
            if heading and heading.lower() not in IGNORE_HEADINGS:
                cleaned_heading = clean_text(heading)
                if cleaned_heading:
                    sections_set.add(cleaned_heading)
    sections_text = " ".join(sections_set)

    # Full body text
    body_text_parts = []
    if isinstance(body_items, list):
        for item in body_items:
            body_text_parts.append(item.get("text", ""))
    body_text = clean_text(" ".join(body_text_parts))

    # Output JSON
    output_json = {
        "paper_id": paper_id,
        "metadata": cleaned_metadata,
        "abstract": abstract_text,
        "sections": sections_text,
        "text": body_text
    }

    # Save result
    os.makedirs(cleaned_folder, exist_ok=True)
    output_file = os.path.join(cleaned_folder, os.path.basename(file_path))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2)

    print(f"Cleaned file saved → {output_file}")

# ----------------------------
# Find repo root dynamically
# ----------------------------
def find_repo_root(start_path=None, marker=".git"):
    if start_path is None:
        start_path = os.path.abspath(os.path.dirname(__file__))

    current = start_path
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, marker)):
            return current
        current = os.path.dirname(current)

    raise FileNotFoundError(f"Could not find repo root containing {marker}")

# ----------------------------
# Main execution
# ----------------------------
if __name__== "__main__":

    REPO_ROOT = find_repo_root()
    DOCS_FOLDER = os.path.join(REPO_ROOT, "data", "docs")
    CLEANED_FOLDER = os.path.join(REPO_ROOT, "data", "cleaned")

    os.makedirs(CLEANED_FOLDER, exist_ok=True)

    # Already cleaned files → to skip duplicates
    cleaned_files = set(os.listdir(CLEANED_FOLDER))

    # Process ONLY new files
    for filename in os.listdir(DOCS_FOLDER):
        if filename.endswith(".json") and filename not in cleaned_files:
            file_path = os.path.join(DOCS_FOLDER, filename)
            preprocess_file(file_path, CLEANED_FOLDER)