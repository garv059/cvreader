import os
import re
import docx2txt
from flask import Flask, render_template, request, redirect, url_for, send_file
from openpyxl import Workbook
from PyPDF2 import PdfReader
import textract
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'doc'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_information(text):
    email = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phone = re.findall(r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b', text)
    return email[0] if email else None, phone[0] if phone else None

def extract_text_from_pdf(file_path):
    text = textract.process(file_path, method='pdftotext').decode('utf-8')
    return text

def extract_text_from_doc(file_path):
    # Run antiword command to extract text from .doc files
    cmd = ['antiword', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def sanitize_text(text):
    # Remove illegal characters from the text
    sanitized_text = ''.join(char for char in text if ord(char) < 128 and char.isprintable())
    return sanitized_text

def extract_text_from_file(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return docx2txt.process(file_path)
    elif file_path.endswith('.doc'):
        return extract_text_from_doc(file_path)
    else:
        return None

@app.route('/download_output', methods=['GET'])
def download_output():
    output_filename = 'uploads/output.xlsx'
    return send_file(output_filename, as_attachment=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse_cvs', methods=['POST'])
def parse_cvs():
    output_filename = 'uploads/output.xlsx'

    if os.path.exists(output_filename):
        os.remove(output_filename)
        wb = Workbook()
        ws = wb.active
        ws.append(['Email', 'Contact Number', 'Text'])
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(['Email', 'Contact Number', 'Text'])

    for file in request.files.getlist('cv_files'):
        if file and allowed_file(file.filename):
            file_path = 'uploads/' + file.filename
            file.save(file_path)
            text = extract_text_from_file(file_path)
            os.remove(file_path)

            if text:
                email, phone = extract_information(text)
                sanitized_text = sanitize_text(text)
                text_lines = sanitized_text.split('\n')
                text_concatenated = ' '.join(text_lines)
                ws.append([email, phone, text_concatenated])

    wb.save(output_filename)
    return redirect(url_for('download_output'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)

