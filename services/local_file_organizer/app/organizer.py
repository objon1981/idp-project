import os
import shutil
from loguru import logger
import yaml

def load_config(path="config.yaml"):
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def get_category(file_name, file_types):
    ext = os.path.splitext(file_name)[1].lower()
    for category, extensions in file_types.items():
        if ext in extensions:
            return category
    return "others"

def organize_file(src_path, dest_root, file_types):
    if not os.path.isfile(src_path):
        return

    file_name = os.path.basename(src_path)
    category = get_category(file_name, file_types)
    dest_dir = os.path.join(dest_root, category)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file_name)

    shutil.move(src_path, dest_path)
    logger.info(f"Moved {src_path} to {dest_path}")
