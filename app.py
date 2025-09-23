import os
import csv
import pickle
from flask import Flask, render_template, request, send_from_directory, jsonify

app = Flask(__name__)

DATA_CSV_DIR = 'data_csv'
DATA_PDF_DIR = 'data_pdf'
INDEX_FILE = 'data_index.pkl'

def index_data():
    data = []
    for filename in os.listdir(DATA_CSV_DIR):
        if filename.endswith('.csv'):
            with open(os.path.join(DATA_CSV_DIR, filename), encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['source_file'] = filename
                    data.append(row)
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump(data, f)
    return data

def load_indexed_data():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        return index_data()

@app.route('/')
def home():
    return render_template('index.html', results=None, indexed=os.path.exists(INDEX_FILE))

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').lower()
    data = load_indexed_data()
    results = []
    for row in data:
        if any(query in str(value).lower() for value in row.values()):
            results.append(row)
    return render_template('index.html', results=results, indexed=True)

@app.route('/refresh_index', methods=['POST'])
def refresh_index():
    index_data()
    return jsonify({'status': 'ok'})

@app.route('/pdf/<idpel>')
def show_pdf(idpel):
    pdf_filename = f"{idpel}.pdf"
    pdf_path = os.path.join(DATA_PDF_DIR, pdf_filename)
    if os.path.exists(pdf_path):
        return send_from_directory(DATA_PDF_DIR, pdf_filename)
    else:
        return "PDF tidak ditemukan", 404

@app.route('/edit', methods=['POST'])
def edit():
    idpel = request.form['idpel']
    keterangan = request.form['keterangan']
    lokasi = request.form['lokasi']
    source_file = request.form['source_file']
    updated = False
    file_path = os.path.join(DATA_CSV_DIR, source_file)
    rows = []
    with open(file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        # Tambah kolom jika belum ada
        if 'keterangan' not in fieldnames:
            fieldnames.append('keterangan')
        if 'lokasi' not in fieldnames:
            fieldnames.append('lokasi')
        for row in reader:
            if row.get('IDPEL') == idpel:
                row['keterangan'] = keterangan
                row['lokasi'] = lokasi
                updated = True
            rows.append(row)
    if updated:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        # Re-index
        index_data()
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'not found'}), 404

if __name__ == '__main__':
    if not os.path.exists(INDEX_FILE):
        index_data()
    app.run(debug=True)