import os
import pandas as pd # type: ignore
from loguru import logger # type: ignore
from pdfminer.high_level import extract_text # type: ignore
from docx import Document # type: ignore
import yaml # type: ignore

def load_config(path="config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def extract_text_from_pdf(file_path):
    return extract_text(file_path)

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext == ".xlsx":
        df = pd.read_excel(file_path)
        return df.to_csv(index=False)
    else:
        return ""

def save_output(output_path, content):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Saved processed file to {output_path}")
