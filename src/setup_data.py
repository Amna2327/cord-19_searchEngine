import os
import zipfile
import requests
import subprocess

# -------------------------------
# CONFIG
# -------------------------------
DATA_FOLDER = "data"
DOCS_FOLDER = os.path.join(DATA_FOLDER, "docs")
ZIP_PATH = os.path.join(DATA_FOLDER, "raw_data.zip")

# DIRECT DOWNLOAD LINK (change only ID)
DRIVE_DOWNLOAD_LINK = "https://drive.google.com/uc?export=download&id=1gORkyHsHGj6m2gIfW5t1Wbu4dgZrw5Wp"

# -------------------------------
# STEP 1: Ensure folders exist
# -------------------------------
print("[1] Ensuring folder structure...")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOCS_FOLDER, exist_ok=True)

# -------------------------------
# STEP 2: Download ZIP from Google Drive
# -------------------------------
def download_file(url, destination):
    print(f"[2] Downloading dataset from Google Drive...\n    -> {url}")
    response = requests.get(url, stream=True)
    
    if response.status_code != 200:
        raise Exception("Download failed! Check the link or file permissions.")

    with open(destination, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    
    print(f"[✔] Downloaded ZIP to: {destination}")

if not os.path.exists(ZIP_PATH):
    download_file(DRIVE_DOWNLOAD_LINK, ZIP_PATH)
else:
    print("[✔] ZIP already exists, skipping download.")

# -------------------------------
# STEP 3: Extract ZIP
# -------------------------------
print("[3] Extracting ZIP contents...")

with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
    zip_ref.extractall(DOCS_FOLDER)

print(f"[✔] Extracted into: {DOCS_FOLDER}")

# -------------------------------
# STEP 4: Run build_raw_docs.py
# -------------------------------
print("[4] Rebuilding raw_docs.json dictionary...")

subprocess.run(["python", "src/build_raw_docs.py"])

print("[✔] Raw dictionary updated.")

# -------------------------------
# DONE
# -------------------------------
print("\n🎉 Setup completed successfully!")
print("Your dataset is ready in: data/docs/")
