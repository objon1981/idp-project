import os
import hashlib

def save_file(file, folder):
    filename = file.filename
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    return filename

def generate_secure_key(filename):
    return hashlib.sha256(filename.encode()).hexdigest()[:16]
