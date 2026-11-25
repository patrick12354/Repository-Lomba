import pandas as pd
import numpy as np
from flask import Flask, request, render_template_string, flash, redirect, url_for
from sklearn.metrics import mean_absolute_percentage_error

# ==============================================================================
# Inisialisasi Aplikasi Flask
# ==============================================================================
app = Flask(__name__)
# Kunci rahasia diperlukan untuk menampilkan pesan ('flash messages')
app.secret_key = 'kunci-rahasia-fleksibel-456' 

# ==============================================================================
# Kode HTML Disimpan sebagai String
# ==============================================================================

# HTML untuk halaman utama (form dengan dua unggahan)
HTML_INDEX = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kalkulator Skor MAPE</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 2em; display: flex; justify-content: center; align-items: center; min-height: 100vh;}
        .container { background: #fff; padding: 2em 3em; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); text-align: center; max-width: 600px; width: 100%;}
        h1 { color: #2c3e50; }
        p { color: #555; line-height: 1.6; }
        .upload-form { margin-top: 2em; }
        .file-input-group { margin-bottom: 1.5em; }
        label { display: block; margin-bottom: 0.5em; font-weight: bold; color: #333; }
        input[type="file"] { border: 2px dashed #007bff; padding: 1em; border-radius: 8px; background-color: #f8f9fa; cursor: pointer; display: block; width: 95%; margin: 0 auto; }
        button { background-color: #28a745; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 1em; transition: background-color 0.3s ease; }
        button:hover { background-color: #218838; }
        .flash-message { padding: 1em; margin-bottom: 1em; border-radius: 4px; color: #fff; }
        .flash-error { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Kalkulator Skor MAPE</h1>
        <p>Unggah file kunci jawaban dan file submission Anda untuk menghitung skor MAPE.</p>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="flash-message flash-error">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form method="post" enctype="multipart/form-data" class="upload-form">
            <div class="file-input-group">
                <label for="key_file">1. Unggah File Kunci Jawaban (.csv)</label>
                <input type="file" name="key_file" id="key_file" required>
            </div>
            <div class="file-input-group">
                <label for="submission_file">2. Unggah File Submission Anda (.csv)</label>
                <input type="file" name="submission_file" id="submission_file" required>
            </div>
            <button type="submit">Hitung Skor</button>
        </form>
    </div>
</body>
</html>
"""

# HTML untuk halaman hasil (tidak perlu diubah)
HTML_RESULT = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hasil Skor</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 2em; display: flex; justify-content: center; align-items: center; min-height: 100vh;}
        .container { background: #fff; padding: 2em 3em; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.1); text-align: center; }
        h1 { color: #2c3e50; }
        .score { font-size: 3.5em; color: #28a745; font-weight: bold; margin: 0.5em 0; }
        .score-info { color: #555; }
        .error { font-size: 1.2em; color: #dc3545; font-weight: bold; margin: 0.5em 0; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 1em; border-radius: 5px;}
        a { background-color: #6c757d; color: white; padding: 10px 18px; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 1.5em; transition: background-color 0.3s ease;}
        a:hover { background-color: #5a6268; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hasil Evaluasi</h1>
        
        {% if score %}
            <p class="score-info">Skor MAPE (Mean Absolute Percentage Error) Anda adalah:</p>
            <div class="score">{{ score }}%</div>
            <p class="score-info">Semakin kecil nilainya, semakin baik. Skor 0 adalah sempurna.</p>
        {% elif error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        
        <a href="/">Unggah File Lain</a>
    </div>
</body>
</html>
"""

# ==============================================================================
# Fungsi Logika
# ==============================================================================

def calculate_mape(df_true, df_pred):
    """
    Menggabungkan dua dataframe berdasarkan ID dan menghitung MAPE.
    """
    df_true = df_true.sort_values('ID').reset_index(drop=True)
    df_pred = df_pred.sort_values('ID').reset_index(drop=True)

    if len(df_true) != len(df_pred) or not all(df_true['ID'] == df_pred['ID']):
        return None, "Error: File submission memiliki jumlah baris atau ID yang tidak cocok dengan kunci jawaban."

    merged_df = pd.merge(df_true, df_pred, on='ID', suffixes=('_true', '_pred'))

    y_true = merged_df['Suhu_Rata_Rata_C_true']
    y_pred = merged_df['Suhu_Rata_Rata_C_pred']
    
    # Handle kasus di mana y_true adalah 0
    mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true == 0, 1e-8, y_true))) * 100
        
    return mape, None

# ==============================================================================
# Rute Aplikasi Web
# ==============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Validasi unggahan file
        if 'key_file' not in request.files or 'submission_file' not in request.files:
            flash('Harap unggah kedua file (kunci jawaban dan submission).')
            return redirect(request.url)
        
        key_file = request.files['key_file']
        submission_file = request.files['submission_file']

        if key_file.filename == '' or submission_file.filename == '':
            flash('Harap pilih kedua file untuk diunggah.')
            return redirect(request.url)

        # 2. Proses file jika valid
        if key_file and submission_file:
            if not key_file.filename.endswith('.csv') or not submission_file.filename.endswith('.csv'):
                 return render_template_string(HTML_RESULT, error="Error: Kedua file harus berformat .csv")
            try:
                # Muat kedua file dari unggahan
                kunci_jawaban_df = pd.read_csv(key_file)
                submission_df = pd.read_csv(submission_file)
                
                # Validasi kolom
                if not {'ID', 'Suhu_Rata_Rata_C'}.issubset(kunci_jawaban_df.columns):
                    return render_template_string(HTML_RESULT, error="Error: File kunci jawaban harus memiliki kolom 'ID' dan 'Suhu_Rata_Rata_C'.")
                if not {'ID', 'Suhu_Rata_Rata_C'}.issubset(submission_df.columns):
                    return render_template_string(HTML_RESULT, error="Error: File submission Anda harus memiliki kolom 'ID' dan 'Suhu_Rata_Rata_C'.")
                
                # Hitung skor MAPE
                score, error = calculate_mape(kunci_jawaban_df, submission_df)
                
                if error:
                    return render_template_string(HTML_RESULT, error=error)
                
                return render_template_string(HTML_RESULT, score=f"{score:.4f}")

            except Exception as e:
                error_msg = f"Terjadi error saat memproses file Anda: {e}"
                return render_template_string(HTML_RESULT, error=error_msg)

    return render_template_string(HTML_INDEX)

# ==============================================================================
# Jalankan Aplikasi
# ==============================================================================
if __name__ == '__main__':
    print("Menjalankan server...")
    print("Buka browser Anda dan kunjungi http://127.0.0.1:5000")
    app.run(debug=True)