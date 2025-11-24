import os
import zipfile
import subprocess
import gdown

# -------------------------------
# DETERMINE REPO ROOT
# -------------------------------
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# -------------------------------
# CONFIG
# -------------------------------
DATA_FOLDER = os.path.join(repo_root, "data")
DOCS_FOLDER = os.path.join(DATA_FOLDER, "docs")
ZIP_PATH = os.path.join(DATA_FOLDER, "raw_data.zip")

# Google Drive file ID
FILE_ID = "1gORkyHsHGj6m2gIfW5t1Wbu4dgZrw5Wp"
DRIVE_DOWNLOAD_LINK = f"https://drive.google.com/uc?id={FILE_ID}"


# -------------------------------
# STEP 1: Ensure folders exist
# -------------------------------
print("[1] Ensuring folder structure...")
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DOCS_FOLDER, exist_ok=True)


# -------------------------------
# STEP 2: Download ZIP (Google Drive)
# -------------------------------
if not os.path.exists(ZIP_PATH):
    print(f"[2] Downloading dataset from Google Drive...\n    -> {DRIVE_DOWNLOAD_LINK}")
    gdown.download(DRIVE_DOWNLOAD_LINK, ZIP_PATH, quiet=False)
    print(f"[✔] Downloaded ZIP to: {ZIP_PATH}")
else:
    print("[✔] ZIP already exists, skipping download.")


# -------------------------------
# STEP 3: Extract ZIP (remove top folder)
# -------------------------------
print("[3] Extracting ZIP contents...")

with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:

    # Detect top folder in ZIP
    members = zip_ref.namelist()
    top_level_folder = members[0].split('/')[0]

    for member in members:

        # Skip directories
        if member.endswith("/"):
            continue

        # Remove the top folder:
        #   raw_data/file1.json  → file1.json
        fixed_path = member.replace(top_level_folder + "/", "", 1)

        # Build destination path
        target_path = os.path.join(DOCS_FOLDER, fixed_path)

        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Extract file
        with zip_ref.open(member) as source, open(target_path, "wb") as target:
            target.write(source.read())

print(f"[✔] Extracted into: {DOCS_FOLDER}")


# -------------------------------
# STEP 4: Build raw_docs.json
# -------------------------------
print("[4] Rebuilding raw_docs.json dictionary...")
subprocess.run(["python", os.path.join(repo_root, "src", "build_raw_docs.py")])
print("[✔] Raw dictionary updated.")


# -------------------------------
# DONE
# -------------------------------
print("\n🎉 Setup completed successfully!")
print(f"Your dataset is ready in: {DOCS_FOLDER}")
