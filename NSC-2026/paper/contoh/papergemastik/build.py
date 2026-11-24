# -*- coding: utf-8 -*-
"""
Pembangkit technical report GEMASTIK XIX - SENDI.

Letak:     Project/paper/
Jalankan:  python build.py
Keluaran:  Project/paper/keluaran/*.docx dan *.pdf

Yang perlu disunting kalau mau mengubah naskah:
  content.py  - seluruh teks (judul, penulis, abstrak, tiap paragraf, referensi)
  tables.py   - isi seluruh tabel
  build.py    - urutan bagian, penempatan tabel/gambar, ukuran font tabel
  build_lib.py- lapisan bantu docx (jarang perlu disentuh)

Ketergantungan:  pip install python-docx
Ekspor PDF memakai LibreOffice (soffice) kalau tersedia di PATH.
"""
import copy
import os
import shutil
import subprocess
import sys

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from build_lib import (el, style_by_name, strip_numbering, clear_body, make_sectPr,
                       attach_section_break, para, add_runs, add_table, add_picture_para,
                       set_cell_text, set_cols, set_tabstops, add_math_runs)
import content as C
import tables as T

# ---------------------------------------------------------------- KONFIGURASI
HERE = os.path.dirname(os.path.abspath(__file__))          # ...\Project\paper
PROJECT = os.path.dirname(HERE)                            # ...\Project
REPO = os.path.dirname(PROJECT)                            # ...\DataMining

# Penamaan berkas mengikuti Pedoman GEMASTIK XIX halaman 29, Bab III bagian C
# butir 2.g, yang mensyaratkan persis:
#
#     GEMASTIK XIX Penambangan Data - <ID Tim> - <Nama Tim> - <Judul Karya>.pdf
#
# JUDUL_KARYA diisi "SENDI" dan bukan judul penuh naskah. Alasannya dua. Judul
# penuh memuat titik dua, yang terlarang pada nama berkas Windows, sehingga
# tidak dapat dipakai apa adanya. Dan judul penuh membuat panjang path mendekati
# batas 260 karakter, yang berisiko saat berkas dipindah atau diunggah. SENDI
# adalah nama karyanya sekaligus bagian judul sebelum titik dua.
ID_TIM = os.environ.get('ID_TIM', '260010041911738')
NAMA_TIM = 'Rizzz'
JUDUL_KARYA = 'SENDI'
NAMA_BERKAS = ('GEMASTIK XIX Penambangan Data - %s - %s - %s'
               % (ID_TIM, NAMA_TIM, JUDUL_KARYA))

_TERLARANG = set('\\/:*?"<>|')
if _TERLARANG & set(NAMA_BERKAS):
    sys.exit('Nama berkas memuat karakter terlarang Windows: %s'
             % ''.join(sorted(_TERLARANG & set(NAMA_BERKAS))))

NAMA_TEMPLATE = 'conference-template-a4.docx'
BASE = os.path.join(HERE, 'base.docx')             # template hasil normalisasi
FIGDIR = os.path.join(PROJECT, 'reports', 'figures')
OUTDIR = os.path.join(HERE, 'keluaran')


def cari_template():
    """Template dicari di folder ini dulu, lalu naik dua tingkat."""
    for d in (HERE, PROJECT, REPO):
        p = os.path.join(d, NAMA_TEMPLATE)
        if os.path.exists(p):
            return p
    return None


# Metadata berkas. Template IEEE bawaan membawa jejak penulis aslinya
# ("IEEE", "Diana Romeo", "Paper Title") - seluruhnya ditimpa di sini supaya
# properti berkas menampilkan tim penulis yang sebenarnya.
META_PENULIS = '; '.join(n for n, _, _ in C.PENULIS)
META_JUDUL = C.JUDUL
META_SUBJEK = ('Technical Report babak penyisihan GEMASTIK XIX 2026 - '
               'Kompetisi III Penambangan Data')
META_KATA_KUNCI = C.KATA_KUNCI
META_ORGANISASI = '%s, %s' % (C.FAKULTAS, C.UNIV.split(',')[0])
META_APLIKASI = 'python-docx'      # toolchain yang benar-benar membangun berkas

COL_W = 3.30   # lebar satu kolom (inci)
FULL_W = 6.85  # lebar penuh dua kolom

# Blok penulis memakai lebar teks penuh (A4 dikurangi margin kiri-kanan template,
# 11906 - 2 x 893 twip = 7,03 inci) dan kolom yang tidak sama lebar. Dengan tiga
# kolom sama lebar, "Timotius Christopher Patrick Sihombing" pada 10 pt tebal
# menuntut 175 pt sedangkan satu kolom hanya menyediakan 164 pt, sehingga
# "Sihombing" jatuh ke baris kedua. Pangsa di bawah memberi kolom pertama
# 181 pt dan dua kolom lainnya 161 pt; keduanya masih di atas 156 pt yang
# dibutuhkan baris afiliasi terpanjang, yaitu "Universitas Airlangga, Surabaya,
# Indonesia" pada 9 pt.
PENULIS_W = 7.00
PENULIS_PANGSA = [0.359, 0.3205, 0.3205]


def soffice():
    for c in ('soffice', 'libreoffice',
              r'C:\Program Files\LibreOffice\program\soffice.exe',
              r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p:
            return p
    return None


def siapkan_base():
    """conference-template-a4.docx disimpan dalam OOXML Strict yang tidak dapat
    dibaca python-docx. Sekali saja dikonversi ke Transitional lewat LibreOffice
    dan hasilnya disimpan sebagai base.docx."""
    if os.path.exists(BASE):
        return
    tpl = cari_template()
    if not tpl:
        sys.exit('Template %s tidak ditemukan di %s, %s, maupun %s'
                 % (NAMA_TEMPLATE, HERE, PROJECT, REPO))
    so = soffice()
    if not so:
        sys.exit('base.docx belum ada dan LibreOffice tidak ditemukan untuk '
                 'mengonversi template. Pasang LibreOffice, atau salin base.docx '
                 'dari paket generator.')
    tmp = os.path.join(HERE, '_konversi')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([so, '--headless', '--convert-to', 'docx', '--outdir', tmp,
                    tpl], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.move(os.path.join(tmp, os.path.basename(tpl)), BASE)
    shutil.rmtree(tmp, ignore_errors=True)
    print('base.docx dibuat dari', tpl)


def fig(nama):
    p = os.path.join(FIGDIR, nama)
    if not os.path.exists(p):
        sys.exit('Gambar tidak ditemukan: %s\n'
                 'Bangkitkan dulu dengan: python scripts/build_figures.py' % p)
    return p


def tulis_metadata_docx(jalur):
    """Isi properti inti DOCX dan bersihkan sisa metadata template."""
    import zipfile
    from datetime import datetime, timezone

    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/'
        '2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/'
        'officeDocument/2006/docPropsVTypes">'
        '<Template>%s</Template><TotalTime>0</TotalTime>'
        '<Application>%s</Application><Company>%s</Company>'
        '<AppVersion>15.0000</AppVersion></Properties>'
    ) % (NAMA_TEMPLATE, META_APLIKASI, META_ORGANISASI)

    tmp = jalur + '.tmp'
    with zipfile.ZipFile(jalur) as zin, \
            zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        ditulis = set()
        # Entri terakhir yang menang kalau ada duplikat: itu yang ditulis
        # python-docx, bukan sisa dari template.
        terakhir = {}
        for item in zin.infolist():
            terakhir[item.filename] = item
        for item in zin.infolist():
            if item.filename in ditulis or terakhir[item.filename] is not item:
                continue
            ditulis.add(item.filename)
            data = zin.read(item.filename)
            if item.filename == 'docProps/app.xml':
                data = app_xml.encode('utf-8')
            zout.writestr(item, data)
    os.replace(tmp, jalur)


def tulis_metadata_pdf(jalur):
    """Timpa metadata PDF. Butuh pypdf; dilewati kalau belum terpasang."""
    import warnings
    warnings.filterwarnings('ignore')
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print('       (metadata PDF dilewati: pip install pypdf)')
        return
    from datetime import datetime

    sekarang = datetime.now().astimezone()
    ofs = sekarang.strftime('%z')                       # mis. +0700
    stempel = sekarang.strftime('D:%Y%m%d%H%M%S') + "%s'%s'" % (ofs[:3], ofs[3:])
    r = PdfReader(jalur)
    w = PdfWriter()
    for hal in r.pages:
        w.add_page(hal)
    w.add_metadata({
        '/Title': META_JUDUL,
        '/Author': META_PENULIS,
        '/Subject': META_SUBJEK,
        '/Keywords': META_KATA_KUNCI,
        '/Creator': META_APLIKASI,
        '/Producer': 'LibreOffice',
        '/CreationDate': stempel,
        '/ModDate': stempel,
    })
    with open(jalur, 'wb') as f:
        w.write(f)


siapkan_base()
os.makedirs(OUTDIR, exist_ok=True)

doc = Document(BASE)

strip_numbering(doc, ['Heading 1', 'Heading 2', 'Heading 3',
                      'figure caption', 'table head', 'references'])

# Normal -> 10pt Times
st_normal = doc.styles['Normal']
st_normal.font.name = 'Times New Roman'
st_normal.font.size = Pt(10)

body_sectPr = clear_body(doc)
set_cols(body_sectPr, 2, 360)

SEC1 = make_sectPr(body_sectPr, 1)   # judul + penulis: satu kolom

fig_n = [0]
tab_n = [0]
eq_n = [0]


def heading1(text):
    p = para(doc, text, style=style_by_name(doc, 'Heading 1'))
    p.paragraph_format.keep_with_next = True
    return p


def heading2(text):
    p = para(doc, text, style=style_by_name(doc, 'Heading 2'))
    p.paragraph_format.keep_with_next = True
    return p


def body(text):
    return para(doc, text, style=style_by_name(doc, 'Body Text'))


def body_all(items):
    for t in items:
        body(t)


def bullets(items, num=False):
    for i, t in enumerate(items):
        p = para(doc, ('%d) ' % (i + 1) if num else '• ') + t,
                 style=style_by_name(doc, 'Body Text'))
        pf = p.paragraph_format
        pf.left_indent = Pt(12)
        pf.first_line_indent = Pt(-12)
        pf.space_after = Pt(2)


def equations(items, width=COL_W, size=9.5, num_w=0.42):
    """Blok rumus terpusat dengan nomor rata kanan, gaya IEEE.

    Dibangun sebagai tabel tanpa garis, bukan paragraf bertab. Tab tengah dan
    tab kanan dalam satu paragraf ditafsirkan berbeda oleh Word dan LibreOffice
    ketika rumusnya melewati titik tengah kolom, sehingga sebagian nomor
    berhenti di tengah alih-alih di tepi kanan. Tabel dua kolom menghilangkan
    ketergantungan itu sepenuhnya.

    Satu pemanggilan menghasilkan satu tabel dengan satu baris per rumus.
    Memanggilnya dua kali berturut-turut akan membuat kedua tabel menyatu di
    Word, jadi kelompokkan rumus yang berdekatan ke dalam satu daftar.

    Nomornya dihitung otomatis mengikuti urutan pemanggilan, sama seperti nomor
    tabel dan gambar. Rujukan di dalam kalimat tetap ditulis manual di
    content.py, jadi menyisipkan rumus di tengah menuntut penelusuran ulang
    kata "Persamaan" di sana.
    """
    t = doc.add_table(rows=len(items), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    for old in tblPr.findall(qn('w:tblLayout')):
        tblPr.remove(old)
    tblPr.append(el('w:tblLayout', **{'w:type': 'fixed'}))

    lebar = [width - num_w, num_w]
    for ri, teks in enumerate(items):
        eq_n[0] += 1
        for ci in range(2):
            cell = t.cell(ri, ci)
            cell.width = Inches(lebar[ci])
            cell.text = ''
            p = cell.paragraphs[0]
            pf = p.paragraph_format
            pf.space_before = Pt(4)
            pf.space_after = Pt(4)
            pf.line_spacing = 1.0
            pf.alignment = (WD_ALIGN_PARAGRAPH.CENTER if ci == 0
                            else WD_ALIGN_PARAGRAPH.RIGHT)
            if ci == 0:
                add_math_runs(p, teks, size=size)
            else:
                add_runs(p, '(%d)' % eq_n[0], size=size)
                for r in p.runs:
                    r.font.name = 'Times New Roman'
            tcPr = cell._tc.get_or_add_tcPr()
            b = el('w:tcBorders')
            for sisi in ('top', 'bottom', 'left', 'right'):
                b.append(el('w:' + sisi, **{'w:val': 'none', 'w:sz': 0, 'w:space': 0}))
            tcPr.append(b)
            mar = el('w:tcMar')
            for sisi in ('top', 'bottom', 'left', 'right'):
                mar.append(el('w:' + sisi, **{'w:w': 0, 'w:type': 'dxa'}))
            tcPr.append(mar)
            cell.vertical_alignment = 1
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(el('w:cantSplit'))
    for ci, col in enumerate(t.columns):
        col.width = Inches(lebar[ci])
    return para(doc, '', style=style_by_name(doc, 'Body Text'), space_after=2)


def table_block(spec, size=7.2, width=COL_W, header_rows=1, show_caption=True,
                subcaption=None):
    title, rows, widths, aligns = spec
    if subcaption:
        cap = para(doc, subcaption, style=style_by_name(doc, 'table head'))
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_before = Pt(6)
        cap.paragraph_format.space_after = Pt(3)
        for r in cap.runs:
            r.font.italic = True
    if show_caption:
        tab_n[0] += 1
        cap = para(doc, 'TABEL %s.  %s' % (roman(tab_n[0]), title.upper()),
                   style=style_by_name(doc, 'table head'))
        cap.paragraph_format.keep_with_next = True
        cap.paragraph_format.space_before = Pt(8)
        cap.paragraph_format.space_after = Pt(3)
    add_table(doc, rows, widths=widths, size=size, header_rows=header_rows,
              align_cols=aligns, total_width=width)
    tail = para(doc, '', style=style_by_name(doc, 'Body Text'), space_after=4)
    return tail


def figure_block(path, caption, width=COL_W):
    fig_n[0] += 1
    add_picture_para(doc, path, width)
    p = para(doc, 'Gambar %d.  %s' % (fig_n[0], caption),
             style=style_by_name(doc, 'figure caption'))
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    return p


def roman(n):
    vals = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def full_width(fn):
    """Jalankan fn() dalam wilayah satu kolom (span penuh)."""
    # tutup section 2-kolom pada paragraf kosong tipis
    p = para(doc, '', space_before=0, space_after=0)
    p.paragraph_format.line_spacing = Pt(1)
    for r in p.runs:
        r.font.size = Pt(1)
    attach_section_break(p, make_sectPr(body_sectPr, 2))
    last = fn()
    attach_section_break(last, make_sectPr(body_sectPr, 1))


# ---------------------------------------------------------------- HALAMAN AWAL
tp = para(doc, C.JUDUL, style=style_by_name(doc, 'paper title'))
tp.paragraph_format.space_after = Pt(10)
for r in tp.runs:
    r.font.size = Pt(19)

def ukuran_email(email, lebar_in):
    """Perkecil font email secukupnya supaya muat satu baris.

    Alamat penulis panjangnya berbeda-beda dan yang terpanjang membungkus ke
    baris kedua, menyisakan potongan ".id" menggantung sendirian. Lebar rata
    huruf kecil Times New Roman miring sekitar 0,45 em, jadi ukuran terbesar
    yang masih muat dapat ditaksir langsung dari jumlah karakternya. Hasilnya
    dibulatkan turun ke kelipatan 0,5 pt dan ditahan di rentang yang masih
    terbaca saat dicetak.
    """
    muat = (lebar_in * 72) / (len(email) * 0.45)
    return max(6.5, min(8.5, int(muat * 2) / 2))


# blok penulis: tabel 3 kolom tanpa garis
at = doc.add_table(rows=1, cols=3)
at.alignment = WD_TABLE_ALIGNMENT.CENTER
at.autofit = False

# Margin sel dinolkan supaya seluruh lebar kolom terpakai untuk teks. Tanpa
# ini alamat terpanjang kehilangan sekitar 0,16 inci dan tetap membungkus.
tblPr = at._tbl.tblPr
mar = el('w:tblCellMar')
for sisi in ('top', 'left', 'bottom', 'right'):
    mar.append(el('w:' + sisi, **{'w:w': 0, 'w:type': 'dxa'}))
tblPr.append(mar)

for ci, (nama, nim, email) in enumerate(C.PENULIS):
    lebar_kolom = PENULIS_W * PENULIS_PANGSA[ci]
    cell = at.cell(0, ci)
    cell.width = Inches(lebar_kolom)
    cell.text = ''
    lines = [(nama, 10, True, False), (('NIM %s' % nim), 9, False, False),
             (C.PRODI, 9, False, False), (C.FAKULTAS, 9, False, False),
             (C.UNIV, 9, False, False),
             (email, ukuran_email(email, lebar_kolom), False, True)]
    first = True
    for txt, sz, bold, ital in lines:
        p = cell.paragraphs[0] if first else cell.add_paragraph()
        first = False
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(txt)
        r.font.size = Pt(sz)
        r.font.bold = bold
        r.font.italic = ital
        r.font.name = 'Times New Roman'
for ci, col in enumerate(at.columns):
    col.width = Inches(PENULIS_W * PENULIS_PANGSA[ci])
for row in at.rows:
    for cell in row.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        b = el('w:tcBorders')
        for side in ('top', 'bottom', 'left', 'right'):
            b.append(el('w:' + side, **{'w:val': 'none', 'w:sz': 0, 'w:space': 0}))
        tcPr.append(b)

# Paragraf kosong tipis ini membawa pemutus section satu kolom sekaligus
# menjadi satu-satunya jarak antara baris surel penulis dan kepala abstrak.
# Pada 2 pt keduanya nyaris bersentuhan, jadi tingginya dinaikkan ke 11 pt.
pend = para(doc, '', space_before=0, space_after=0)
pend.paragraph_format.line_spacing = Pt(11)
attach_section_break(pend, SEC1)

# ------------------------------------------------------------------- INTISARI
p = para(doc, '', style=style_by_name(doc, 'Abstract'))
# Jarak ke blok penulis di atasnya. Gaya Abstract bawaan template tidak
# menyediakan spasi sebelum, sehingga baris surel dan kepala abstrak nyaris
# bersentuhan pada keluaran PDF.
p.paragraph_format.space_before = Pt(12)
add_runs(p, 'Abstrak—', size=9, bold=True, italic=True)
add_runs(p, C.INTISARI, size=9, bold=True)

p = para(doc, '', style=style_by_name(doc, 'Keywords'))
add_runs(p, 'Kata kunci—', size=9, bold=True, italic=True)
add_runs(p, C.KATA_KUNCI, size=9, italic=True)

# --------------------------------------------------------------- I PENDAHULUAN
heading1('I.  PENDAHULUAN')
heading2('A.  Latar Belakang')
body_all(C.PENDAHULUAN_LATAR)
body_all(C.KONTRIBUSI)
heading2('B.  Tujuan')
body_all(C.PENDAHULUAN_TUJUAN)
bullets(C.TUJUAN_ITEMS, num=True)
heading2('C.  Manfaat')
body_all(C.PENDAHULUAN_MANFAAT)
heading2('D.  Batasan')
body_all(C.PENDAHULUAN_BATASAN)
bullets(C.BATASAN_ITEMS, num=True)

# ------------------------------------------------------------ II KAJIAN TERKAIT
heading1('II.  KAJIAN TERKAIT YANG RELEVAN')
letters = 'ABCDEFGHIJKL'
for i, (judul, paras) in enumerate(C.KAJIAN):
    heading2('%s.  %s' % (letters[i], judul))
    body_all(paras)
body(C.KAJIAN_ANTARA)

heading2('G.  Penilaian Sentimen Berbasis Leksikon')
body_all(C.KAJIAN_LEKSIKON)
equations(C.EQ_LEKSIKON_1)
body_all(C.KAJIAN_LEKSIKON_2)
equations(C.EQ_LEKSIKON_2)
body_all(C.KAJIAN_LEKSIKON_3)
equations(C.EQ_LEKSIKON_3)
body_all(C.KAJIAN_LEKSIKON_4)

heading2('H.  TF-IDF dengan Regresi Logistik')
body_all(C.KAJIAN_TFIDF)
equations(C.EQ_TFIDF_1)
body_all(C.KAJIAN_TFIDF_2)
equations(C.EQ_TFIDF_2)
body_all(C.KAJIAN_TFIDF_3)
equations(C.EQ_TFIDF_3)
body_all(C.KAJIAN_TFIDF_4)

heading2('I.  Arsitektur Transformer dan IndoBERT')
body(C.KAJIAN_TRANSFORMER[0])
figure_block(fig('14-encoder-indobert.png'),
             'Susunan *encoder* Transformer yang dipakai IndoBERT, dari judul berita '
             'sampai tiga kelas sentimen. Blok encoder ditumpuk dua belas kali.',
             width=2.35)
body(C.KAJIAN_TRANSFORMER[1])
equations(C.EQ_TRANSFORMER_1)
body_all(C.KAJIAN_TRANSFORMER_2)
equations(C.EQ_TRANSFORMER_2)
body_all(C.KAJIAN_TRANSFORMER_3)
equations(C.EQ_TRANSFORMER_3)
body_all(C.KAJIAN_TRANSFORMER_4)
equations(C.EQ_TRANSFORMER_4)
body_all(C.KAJIAN_TRANSFORMER_5)

body(C.KAJIAN_PENUTUP)

# ------------------------------------------------------------ III SOLUSI USULAN
heading1('III.  SOLUSI USULAN')
heading2('A.  Deskripsi Solusi')
body(C.SOL_DESKRIPSI[0])
figure_block(fig('08-arsitektur.png'),
             'Arsitektur enam lapis SENDI, dari pengumpulan berita sampai evaluasi.',
             width=2.95)
body_all(C.SOL_DESKRIPSI[1:])

heading2('B.  Dataset')
body_all(C.SOL_DATASET)
table_block(T.T1)
table_block(T.T2, size=7.0)

heading2('C.  Metode')
body_all(C.SOL_METODE_PENGUMPULAN)
table_block(T.T3, size=6.8)

heading2('D.  Perbedaan dengan Solusi Sebelumnya')
body(C.SOL_PERBEDAAN[0])
table_block(T.T4, size=7.0)
body(C.SOL_PERBEDAAN[1])

heading2('E.  Metrik Evaluasi')
body(C.SOL_METRIK[0])
table_block(T.T5, size=7.0)
body_all(C.SOL_METRIK[1:])

# ----------------------------------------------------------------- IV HASIL
heading1('IV.  HASIL EKSPERIMEN DAN PENGUJIAN')
body(C.HASIL_PEMBUKA)

heading2('A.  Komposisi Korpus')
body_all(C.HASIL_KORPUS)
full_width(lambda: figure_block(
    fig('01-sebaran-korpus.png'),
    'Sebaran judul unik per bulan sepanjang Januari 2022 - Agustus 2026. '
    'Kepadatan korpus meningkat tajam pada 2025-2026.', width=FULL_W))

heading2('B.  Deteksi Kode Saham')
body(C.HASIL_NER[0])
table_block(T.T6, size=6.8)
body(C.HASIL_NER[1])

heading2('C.  Klasifikasi Sentimen pada Holdout Out-of-Time')
body_all(C.HASIL_SENTIMEN[:2])
table_block(T.T7, size=6.8)
table_block(T.T7B, size=6.8, show_caption=False,
            subcaption='(lanjutan Tabel VII) Uji bootstrap berpasangan atas selisih weighted-F1')
body_all(C.HASIL_SENTIMEN[2:])

heading2('D.  Hubungan Sentimen dan Abnormal Return')
body_all(C.HASIL_ASOSIASI)

heading2('E.  Event Study')
body(C.HASIL_EVENT[0])
table_block(T.T8, size=6.8)
table_block(T.T8B, size=6.8, show_caption=False)
body_all(C.HASIL_EVENT[1:])
figure_block(fig('03-caar-event-study.png'),
             'CAAR berita positif dan negatif pada *event window* [-1, +5].',
             width=COL_W)

heading2('F.  Ketimpangan Cakupan Berita')
body(C.HASIL_CAKUPAN[0])
table_block(T.T9, size=6.6)
body_all(C.HASIL_CAKUPAN[1:3])
table_block(T.T9B, size=7.0, show_caption=False)
body(C.HASIL_CAKUPAN[3])
figure_block(fig('09-lorenz-cakupan.png'),
             'Kurva Lorenz cakupan berita antaremiten pada subhimpunan sebutan '
             'insidental, dibandingkan garis pemerataan sempurna.', width=COL_W)

heading2('G.  Backtest In-Period dan Out-of-Sample')
body(C.HASIL_BACKTEST[0])
table_block(T.T10, size=7.0)
body(C.HASIL_BACKTEST[1])
figure_block(fig('10-out-of-sample.png'),
             '*Total return* strategi SENDI dibandingkan IHSG pada periode '
             '2022-2024 dan *out-of-sample* 2025-2026.', width=COL_W)

heading2('H.  Ketahanan, Ablasi, dan Sensitivitas Biaya')
body(C.HASIL_KETAHANAN[0])
table_block(T.T11, size=6.6)
body_all(C.HASIL_KETAHANAN[1:])
figure_block(fig('05-sensitivitas-biaya.png'),
             '*Total return* sebagai fungsi biaya transaksi per putaran. Tidak ada '
             'titik impas pada rentang yang diuji.', width=COL_W)

heading2('I.  Audit Pengaitan dan Reliabilitas Anotasi')
body_all(C.HASIL_ANOTASI[:3])
table_block(T.T12, size=7.0)
body(C.HASIL_ANOTASI[3])

heading2('J.  Penilai Sentimen terhadap Rujukan Manusia')
body(C.HASIL_PENILAI[0])
def _t13_fig():
    table_block(T.T13, size=7.2, width=FULL_W)
    return figure_block(
        fig('12-model-vs-manusia.png'),
        'Sisi kiri memuat *macro-F1* setiap penilai terhadap rujukan manusia pada '
        'himpunan uji terkunci (n = 400), dengan garis putus-putus menandai penebak '
        'konstan. Sisi kanan memuat *confusion matrix* ternormalisasi untuk leksikon, '
        'IndoBERT tingkat aspek, dan IndoBERT tingkat dokumen.', width=FULL_W)


full_width(_t13_fig)
body_all(C.HASIL_PENILAI[1:4])
table_block(T.T14, size=6.6)
body(C.HASIL_PENILAI[4])

# --------------------------------------------------------------- V ANALISIS
heading1('V.  ANALISIS ATAS HASIL EKSPERIMEN DAN PENGUJIAN')
heading2('A.  Sebab Struktural Kegagalan NER Umum')
body_all(C.AN_NER)
heading2('B.  Disambiguasi yang Tidak Memberi Keunggulan')
body_all(C.AN_DISAMBIGUASI)
heading2('C.  Transformer yang Tidak Mengungguli TF-IDF')
body_all(C.AN_TRANSFORMER[:3])
table_block(T.T15, size=6.8)
body(C.AN_TRANSFORMER[3])
heading2('D.  Pengujian Dugaan Tersebut lewat Perbaikan Label')
body_all(C.AN_UJI_LABEL[:2])
table_block(T.T16, size=7.0)
body(C.AN_UJI_LABEL[2])
table_block(T.T17, size=6.8)
body_all(C.AN_UJI_LABEL[3:])
heading2('E.  Akurasi Rendah tetapi Hubungan Agregat Signifikan')
body_all(C.AN_AGREGAT)
heading2('F.  Asimetri yang Berbalik Arah')
body_all(C.AN_ASIMETRI)
heading2('G.  Empat Hipotesis Kerugian Strategi dan Dua yang Tereliminasi')
body_all(C.AN_STRATEGI)
heading2('H.  Implikasi')
body_all(C.AN_IMPLIKASI[:2])
full_width(lambda: figure_block(
    fig('13-penyaring-harian.png'),
    'Keluaran penilai leksikon pada satu hari bursa, diambil apa adanya dari basis '
    'data proyek. Sisi kiri memuat corong penyaringan 13 Agustus 2026, dari 348 judul '
    'unik menjadi 54 judul bersentimen berarah. Sisi kanan memuat delapan baris '
    'teratas beserta istilah leksikon yang memicu setiap penilaian.', width=FULL_W))
body_all(C.AN_IMPLIKASI[2:])

# -------------------------------------------------------------- VI KESIMPULAN
heading1('VI.  KESIMPULAN')
body_all(C.KESIMPULAN)
heading2('A.  Saran Pengembangan')
bullets(C.SARAN, num=True)
heading2('B.  Ketersediaan Data dan Kode')
body(C.KETERSEDIAAN)

# --------------------------------------------------------------- REFERENSI
heading1('REFERENSI')
for i, ref in enumerate(C.REFERENSI, 1):
    p = para(doc, '', style=style_by_name(doc, 'references'))
    add_runs(p, '[%d]\t%s' % (i, ref), size=8)
    pf = p.paragraph_format
    pf.left_indent = Pt(16)
    pf.first_line_indent = Pt(-16)

cp = doc.core_properties
cp.author = META_PENULIS
cp.last_modified_by = META_PENULIS
cp.title = META_JUDUL
cp.subject = META_SUBJEK
cp.keywords = META_KATA_KUNCI
cp.category = 'Technical Report'
cp.comments = ''
cp.language = 'id-ID'
cp.revision = 1

out_docx = os.path.join(OUTDIR, NAMA_BERKAS + '.docx')
doc.save(out_docx)
tulis_metadata_docx(out_docx)
print('DOCX  ->', out_docx)
print('       %d gambar, %d tabel, %d rumus' % (fig_n[0], tab_n[0], eq_n[0]))

so = soffice()
if so:
    subprocess.run([so, '--headless', '--convert-to', 'pdf', '--outdir', OUTDIR,
                    out_docx], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out_pdf = os.path.join(OUTDIR, NAMA_BERKAS + '.pdf')
    tulis_metadata_pdf(out_pdf)
    mb = os.path.getsize(out_pdf) / 1e6
    print('PDF   ->', out_pdf)
    print('       %.2f MB (batas lomba 10 MB)' % mb)
else:
    print('PDF   -> dilewati: LibreOffice tidak ditemukan. '
          'Buka DOCX di Word lalu Save As PDF.')

# LibreOffice meninggalkan berkas kunci dan berkas sementara di folder keluaran,
# dan build lama dengan nama berbeda ikut menumpuk di sana. Folder ini dilihat
# manusia saat mengunggah ke laman lomba, jadi isinya dijaga tepat dua berkas.
disimpan = {NAMA_BERKAS + '.docx', NAMA_BERKAS + '.pdf'}
disapu = []
for nama in os.listdir(OUTDIR):
    if nama in disimpan:
        continue
    try:
        os.remove(os.path.join(OUTDIR, nama))
        disapu.append(nama)
    except OSError:
        print('       (gagal menghapus %s, hapus manual)' % nama)
if disapu:
    print('SAPU  -> %d berkas sisa dihapus dari keluaran/' % len(disapu))
