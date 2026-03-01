import zipfile
import os
import shutil
import uuid

BASE_DIR = os.path.abspath("C:/temp")  # Short root path

def extract_zip(file_path):
    # Create short unique folder
    extract_folder = os.path.join(BASE_DIR, str(uuid.uuid4()))

    if os.path.exists(extract_folder):
        shutil.rmtree(extract_folder)

    os.makedirs(extract_folder, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            # Skip extremely long paths
            if len(member.filename) > 200:
                continue

            zip_ref.extract(member, extract_folder)

    return extract_folder