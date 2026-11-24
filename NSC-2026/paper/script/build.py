# -*- coding: utf-8 -*-
"""Pembangkit laporan ilmiah NSC 2026 — Penyisihan Data Science.

Letak     : NSC UB/paper/script/build.py
Jalankan  : python build.py
Keluaran  : NSC UB/paper/output/{Nomor Tim}_{Nama Tim}_Data Science.{docx,pdf}

Yang perlu disunting kalau mau mengubah naskah:
  content.py       - seluruh teks (judul, penulis, abstrak, tiap paragraf, referensi)
  tables.py        - isi seluruh tabel
  make_figures.py  - seluruh gambar dan angka yang dikutip naskah
  build.py         - urutan bagian, penempatan tabel/gambar, ukuran font tabel
  build_lib.py     - lapisan bantu docx (jarang perlu disentuh)

Ketergantungan:  pip install python-docx pypdf docx2pdf
Ekspor PDF memakai Microsoft Word lewat docx2pdf, atau LibreOffice kalau ada
di PATH. Kalau keduanya tidak ada, DOCX tetap terbentuk.
"""
import copy
import os
import re
import shutil
import subprocess
import sys

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

from build_lib import (el, style_by_name, strip_numbering, clear_body, make_sectPr,
                       attach_section_break, para, add_runs, add_table,
                       add_picture_para, set_cols, add_math_runs)
import content as C
import content_lampiran as L
import tables as T

# ---------------------------------------------------------------- KONFIGURASI
HERE = os.path.dirname(os.path.abspath(__file__))     # ...\paper\script
PAPER = os.path.dirname(HERE)                         # ...\paper
PROJECT = os.path.dirname(PAPER)                      # ...\NSC UB

# Juknis 3e: nama berkas {Nomor Tim}_{Nama Tim}_{Data Science}. Nomor tim ada di
# e-mail konfirmasi pendaftaran dari nscub26@gmail.com, formatnya NSC26-DS0XX.
# Isi lewat variabel lingkungan supaya tidak perlu menyunting berkas ini:
#     $env:NOMOR_TIM = "NSC26-DS012"; python build.py
NOMOR_TIM = os.environ.get('NOMOR_TIM', 'NSC26-DS042')
NAMA_BERKAS = '%s_%s_Data Science' % (NOMOR_TIM, C.NAMA_TIM)

_TERLARANG = set('\\/:*?"<>|')
if _TERLARANG & set(NAMA_BERKAS):
    sys.exit('Nama berkas memuat karakter terlarang Windows: %s'
             % ''.join(sorted(_TERLARANG & set(NAMA_BERKAS))))

NAMA_TEMPLATE = 'conference-template-a4.docx'
BASE = os.path.join(HERE, 'base.docx')        # template hasil normalisasi
FIGDIR = os.path.join(PAPER, 'figures')
OUTDIR = os.path.join(PAPER, 'output')

# Metadata berkas. Template IEEE bawaan membawa jejak penulis aslinya
# ("IEEE", "Diana Romeo", "Paper Title"); seluruhnya ditimpa di sini.
META_PENULIS = '; '.join(n for n, _, _ in C.PENULIS)
META_JUDUL = C.JUDUL
META_SUBJEK = ('Laporan ilmiah babak penyisihan National Statistics Challenge 2026 - '
               'Cabang Lomba Data Science')
META_KATA_KUNCI = C.KATA_KUNCI
META_ORGANISASI = '%s, %s' % (C.FAKULTAS, C.UNIV.split(',')[0])
META_APLIKASI = 'python-docx'

# ------------------------------------------------------------------ BORDER NSC
# Juknis 1d mewajibkan border template dari laman resmi NSC. Berkasnya
# (template/Border Data Science (MAKE A COPY).docx) memasang satu gambar bingkai
# selebar halaman di header, sehingga terulang di setiap halaman di belakang
# teks. Yang direplikasi di sini adalah geometri itu, bukan berkasnya.
#
# Masalahnya geometris dan tidak bisa ditawar. Bingkainya digambar untuk dokumen
# Word satu kolom -- berkas panitia sendiri memakai margin kiri 113,8 pt -- dan
# dinding kayunya memakan 78 pt di atas serta 56 pt di bawah. Template IEEE
# hanya menyisakan 27 pt di atas. Ruang teks yang tersisa 2,9 % lebih kecil
# daripada ruang IEEE, dan itu memindahkan daftar pustaka ke halaman ke-11,
# melanggar batas 10 halaman pada juknis 3b.
#
# Karena itu border dipasang lewat saklar, bukan diam-diam. Nilainya:
#   'muat'  - BAWAAN. Bingkai diperbesar 3 % sehingga bagian buramnya bergeser
#             keluar halaman dan ruang teks kembali selebar ruang IEEE.
#             Badan naskah tetap 10 halaman. Harganya: bingkai terpotong
#             12,6 pt di atas, 25,3 pt di bawah, 9,0 pt di tiap sisi, jadi
#             tiang kayu sampingnya menipis. Seluruh unsurnya masih terbaca.
#   'utuh'  - bingkai apa adanya, margin diperlebar supaya tidak tertimpa.
#             Badan naskah menjadi 11 halaman, jadi ini melanggar juknis 3b
#             kecuali naskahnya dipangkas ~2,9 % lebih dulu (README §7).
#   'off'   - tanpa border sama sekali. Badan naskah 10 halaman.
#
# Angka margin di bawah bukan tebakan. Keduanya hasil pencarian atas piksel
# bingkainya sendiri, dan periksa_border() menguji ulang setiap build: kalau
# kotak teks menyentuh satu piksel non-putih, build berhenti alih-alih
# menghasilkan PDF yang teksnya tertimpa kayu.
BORDER_MODE = os.environ.get('BORDER', 'muat').lower()
BORDER_PDF = os.path.join(PAPER, 'template', 'Border Data Science (MAKE A COPY).pdf')
BORDER_PNG = os.path.join(PAPER, 'figures', 'border_nsc.png')

# skala, lalu margin (atas, bawah, kiri, kanan) dalam pt yang sudah diverifikasi
# bebas tabrakan terhadap skala itu.
BORDER_GEOM = {
    'utuh': (1.00, (78.0, 63.0, 45.0, 45.0)),
    'muat': (1.03, (68.0, 52.0, 37.0, 37.0)),
}

COL_W = 3.30    # lebar satu kolom (inci)
FULL_W = 6.85   # lebar penuh dua kolom

# Blok penulis dua kolom pada lebar teks penuh A4 dikurangi margin template.
PENULIS_W = 7.00
PENULIS_PANGSA = [0.5, 0.5]


def soffice():
    for c in ('soffice', 'libreoffice',
              r'C:\Program Files\LibreOffice\program\soffice.exe',
              r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p:
            return p
    return None


def cari_template():
    for d in (HERE, PAPER, os.path.join(PAPER, 'template'), PROJECT):
        p = os.path.join(d, NAMA_TEMPLATE)
        if os.path.exists(p):
            return p
    return None


def siapkan_base():
    """`conference-template-a4.docx` disimpan dalam OOXML Strict yang tidak dapat
    dibaca python-docx. Sekali saja dikonversi ke Transitional dan hasilnya
    disimpan sebagai base.docx, yang ikut di-commit supaya naskah tetap dapat
    dibangun ulang di mesin tanpa Word maupun LibreOffice."""
    if os.path.exists(BASE):
        return
    tpl = cari_template()
    if not tpl:
        sys.exit('Template %s tidak ditemukan.' % NAMA_TEMPLATE)
    so = soffice()
    if so:
        tmp = os.path.join(HERE, '_konversi')
        os.makedirs(tmp, exist_ok=True)
        subprocess.run([so, '--headless', '--convert-to', 'docx', '--outdir', tmp, tpl],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.move(os.path.join(tmp, os.path.basename(tpl)), BASE)
        shutil.rmtree(tmp, ignore_errors=True)
        print('base.docx dibuat dari', tpl)
        return
    try:                                    # jalur Word lewat COM
        import win32com.client
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(tpl)
        doc.SaveAs2(BASE, FileFormat=16)    # wdFormatDocumentDefault (Transitional)
        doc.Close(False)
        word.Quit()
        print('base.docx dibuat dari', tpl, '(lewat Word)')
    except Exception as e:
        sys.exit('base.docx belum ada dan konversi template gagal (%s). '
                 'Pasang LibreOffice atau Microsoft Word.' % e)


def siapkan_border_png():
    """Rasterkan halaman tunggal border PDF menjadi PNG sekali saja.

    PDF-nya memang cuma pembungkus satu gambar; merasterkannya di sini membuat
    build tidak bergantung pada Word membaca DOCX panitia, dan membuat gambarnya
    bisa dipasang dengan geometri yang kita tentukan sendiri.
    """
    if os.path.exists(BORDER_PNG):
        return BORDER_PNG
    if not os.path.exists(BORDER_PDF):
        sys.exit('Border tidak ditemukan: %s\n'
                 'Unduh dari nsc.mipa.ub.ac.id (Event - Data Science - Penyisihan) '
                 'dan taruh di paper/template/.' % BORDER_PDF)
    try:
        import fitz
    except ImportError:
        sys.exit('BORDER=%s butuh PyMuPDF untuk merasterkan bingkainya: '
                 'pip install pymupdf' % BORDER_MODE)
    d = fitz.open(BORDER_PDF)
    d[0].get_pixmap(dpi=300).save(BORDER_PNG)
    print('border dirasterkan ->', BORDER_PNG)
    return BORDER_PNG


def periksa_border(skala, margin):
    """Pastikan kotak teks jatuh di area putih bingkai, bukan di atas kayunya.

    Dikerjakan di sini, bukan dengan mata, karena satu-satunya cara melihat
    tabrakan pada PDF jadi adalah membuka 16 halaman satu per satu. Nilainya
    dicetak sebagai jarak bebas per sisi supaya perubahan margin di kemudian
    hari langsung kelihatan akibatnya.
    """
    try:
        import fitz
        import numpy as np
    except ImportError:
        print('       (pemeriksaan border dilewati: butuh pymupdf + numpy)')
        return
    T, B, L, R = margin
    pm = fitz.open(BORDER_PDF)[0].get_pixmap(dpi=300)
    a = np.frombuffer(pm.samples, dtype=np.uint8)
    a = a.reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(int)
    putih = (a > 242).all(axis=2)
    ph, pw = putih.shape
    sx, sy = 596.0 / pw, 842.0 / ph          # pt per piksel pada halaman border
    # Gambar menempati (-1,74; 0)-(601,26; 854,25) pada halaman border itu.
    ix0, iy0 = -1.74 / sx, 0.0 / sy
    iw, ih = 603.0 / sx, 854.25 / sy
    # Letaknya pada halaman kita: diperbesar `skala` terhadap titik tengah.
    PW, PH = 595.3, 841.9
    x0 = PW / 2 - (PW / 2 + 1.74) * skala
    y0 = PH / 2 - (PH / 2) * skala
    w, h = 603.0 * skala, 854.25 * skala

    def ke_px(X, Y):
        return ix0 + (X - x0) / w * iw, iy0 + (Y - y0) / h * ih

    ax, ay = ke_px(L, T)
    bx, by = ke_px(PW - R, PH - B)
    ax, ay = int(ax), int(ay)
    bx, by = int(bx + 0.999), int(by + 0.999)
    if ax < 0 or ay < 0 or bx > pw or by > ph or not putih[ay:by, ax:bx].all():
        sys.exit('Kotak teks menabrak border pada skala %.2f, margin %s.\n'
                 'Perlebar margin atau naikkan skalanya.' % (skala, margin))

    def bebas(kiri, kanan, atas, bawah):
        n = 0
        while n < 1500:
            AX, AY = ax - kiri * (n + 1), ay - atas * (n + 1)
            BX, BY = bx + kanan * (n + 1), by + bawah * (n + 1)
            if AX < 0 or AY < 0 or BX > pw or BY > ph:
                break
            if not putih[AY:BY, AX:BX].all():
                break
            n += 1
        return n

    print('       border: jarak bebas atas %.1f bawah %.1f kiri %.1f kanan %.1f pt'
          % (bebas(0, 0, 1, 0) * sy, bebas(0, 0, 0, 1) * sy,
             bebas(1, 0, 0, 0) * sx, bebas(0, 1, 0, 0) * sx))


def pasang_border(doc, skala, png):
    """Tanam bingkai di header setiap section, di belakang teks.

    Header, bukan badan, karena hanya header yang terulang di setiap halaman.
    Posisinya relatif terhadap HALAMAN (bukan kolom atau paragraf) supaya
    letaknya sama persis di 16 halaman, tidak ikut bergeser oleh section break
    kontinu yang dipakai tata letak dua kolom.
    """
    from docx.shared import Emu
    PW, PH = 595.3, 841.9
    x0 = PW / 2 - (PW / 2 + 1.74) * skala
    y0 = PH / 2 - (PH / 2) * skala
    w, h = 603.0 * skala, 854.25 * skala

    hdr = doc.sections[0].header
    hdr.is_linked_to_previous = False
    p = hdr.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run()
    run.add_picture(png, width=Emu(int(w * 12700)), height=Emu(int(h * 12700)))

    # add_picture() menyisipkan gambar sebaris (wp:inline), yang berarti ia ikut
    # aliran teks dan mendorong isi halaman ke bawah. Yang dibutuhkan adalah
    # wp:anchor behindDoc="1" berpatokan halaman. Atributnya tidak bernamespace,
    # jadi elemennya dirakit sebagai XML mentah, bukan lewat el() yang meng-qn
    # setiap nama atribut.
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsmap
    inline = run._r.find(qn('w:drawing')).find(qn('wp:inline'))
    drawing = inline.getparent()
    rid = inline.find(qn('a:graphic'))[0][0][1][0].get(qn('r:embed'))
    cx, cy = int(w * 12700), int(h * 12700)
    xml = (
        '<wp:anchor xmlns:wp="%s" xmlns:a="%s" xmlns:pic="%s" xmlns:r="%s"'
        ' behindDoc="1" distT="0" distB="0" distL="0" distR="0" simplePos="0"'
        ' locked="0" layoutInCell="1" allowOverlap="1" relativeHeight="0">'
        '<wp:simplePos x="0" y="0"/>'
        '<wp:positionH relativeFrom="page"><wp:posOffset>%d</wp:posOffset></wp:positionH>'
        '<wp:positionV relativeFrom="page"><wp:posOffset>%d</wp:posOffset></wp:positionV>'
        '<wp:extent cx="%d" cy="%d"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:wrapNone/><wp:docPr id="900" name="border_nsc"/>'
        '<a:graphic><a:graphicData uri="%s"><pic:pic>'
        '<pic:nvPicPr><pic:cNvPr id="900" name="border_nsc"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:anchor>'
    ) % (nsmap['wp'], nsmap['a'], nsmap['pic'], nsmap['r'],
         int(x0 * 12700), int(y0 * 12700), cx, cy,
         'http://schemas.openxmlformats.org/drawingml/2006/picture', rid, cx, cy)
    drawing.remove(inline)
    drawing.append(parse_xml(xml))

    # Setiap section memakai header yang sama, dan ketiga jenisnya sekaligus.
    # Template IEEE memasang w:titlePg, sehingga halaman pertama mengambil
    # header 'first' yang kosong dan bingkainya hilang justru di halaman judul.
    # Mendaftarkan default, first, dan even ke bagian header yang sama menutup
    # ketiganya tanpa bergantung pada ada-tidaknya titlePg.
    ref = doc.sections[0]._sectPr.find(qn('w:headerReference'))
    rid = ref.get(qn('r:id'))
    for s in doc.sections:
        sp = s._sectPr
        for lama in sp.findall(qn('w:headerReference')):
            sp.remove(lama)
        for i, jenis in enumerate(('default', 'first', 'even')):
            r = copy.deepcopy(ref)
            r.set(qn('w:type'), jenis)
            r.set(qn('r:id'), rid)
            sp.insert(i, r)


def fig(nama):
    p = os.path.join(FIGDIR, nama)
    if not os.path.exists(p):
        sys.exit('Gambar tidak ditemukan: %s\n'
                 'Bangkitkan dulu dengan: python make_figures.py' % p)
    return p


def tulis_metadata_docx(jalur):
    """Isi properti DOCX dan bersihkan sisa metadata template IEEE."""
    import zipfile
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
        ditulis, terakhir = set(), {}
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


def ekspor_pdf(out_docx, out_pdf):
    """Word lebih dulu (paling setia terhadap template IEEE), lalu LibreOffice."""
    try:
        from docx2pdf import convert
        convert(out_docx, out_pdf)
        if os.path.exists(out_pdf):
            return 'Word'
    except Exception as e:
        print('       (docx2pdf gagal: %s)' % e)
    so = soffice()
    if so:
        subprocess.run([so, '--headless', '--convert-to', 'pdf', '--outdir',
                        OUTDIR, out_docx], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(out_pdf):
            return 'LibreOffice'
    return None


def tulis_metadata_pdf(jalur, produser):
    import warnings
    warnings.filterwarnings('ignore')
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print('       (metadata PDF dilewati: pip install pypdf)')
        return
    from datetime import datetime
    sekarang = datetime.now().astimezone()
    ofs = sekarang.strftime('%z')
    stempel = sekarang.strftime('D:%Y%m%d%H%M%S') + "%s'%s'" % (ofs[:3], ofs[3:])
    r = PdfReader(jalur)
    w = PdfWriter()
    for hal in r.pages:
        w.add_page(hal)
    w.add_metadata({
        '/Title': META_JUDUL, '/Author': META_PENULIS, '/Subject': META_SUBJEK,
        '/Keywords': META_KATA_KUNCI, '/Creator': META_APLIKASI,
        '/Producer': produser, '/CreationDate': stempel, '/ModDate': stempel,
    })
    with open(jalur, 'wb') as f:
        w.write(f)


# ------------------------------------------------------------------- DOKUMEN
siapkan_base()
os.makedirs(OUTDIR, exist_ok=True)

doc = Document(BASE)
strip_numbering(doc, ['Heading 1', 'Heading 2', 'Heading 3',
                      'figure caption', 'table head', 'references'])

st_normal = doc.styles['Normal']
st_normal.font.name = 'Times New Roman'
st_normal.font.size = Pt(10)

body_sectPr = clear_body(doc)
set_cols(body_sectPr, 2, 360)

# Margin border dipasang SEBELUM SEC1 dibuat: seluruh section lain adalah salinan
# dalam dari body_sectPr, jadi satu suntingan di sini merambat ke 26-nya.
if BORDER_MODE != 'off':
    if BORDER_MODE not in BORDER_GEOM:
        sys.exit('BORDER harus salah satu dari: off, %s'
                 % ', '.join(sorted(BORDER_GEOM)))
    _skala, (_T, _B, _L, _R) = BORDER_GEOM[BORDER_MODE]
    _pm = body_sectPr.find(qn('w:pgMar'))
    for _k, _v in (('top', _T), ('bottom', _B), ('left', _L), ('right', _R)):
        _pm.set(qn('w:' + _k), str(int(round(_v * 20))))
    _pm.set(qn('w:header'), '0')

SEC1 = make_sectPr(body_sectPr, 1)          # judul + penulis: satu kolom

fig_n, tab_n, eq_n = [0], [0], [0]

# ------------------------------------------------------- RUJUKAN OTOMATIS
# Nomor gambar, tabel, dan rumus dihitung dari urutan pemanggilan di bawah.
# Rujukan di dalam kalimat ditulis simbolik di content.py — {G:oracle},
# {T:anatomi}, {E:recon} — lalu disubstitusi di sini. Dengan begitu menambah,
# memindahkan, atau membuang satu gambar tidak pernah meninggalkan nomor yang
# salah di badan teks; kesalahan yang paling mudah luput saat naskah dipangkas.
#
# Ketiga daftar ini adalah urutan yang DIHARAPKAN. Kalau urutan pemanggilan
# tidak cocok, build berhenti dengan pesan yang menyebut kuncinya, bukan
# diam-diam menomori salah.
URUT_GAMBAR = ['target', 'residu', 'oracle', 'bias',
               'increment', 'pembanding', 'tangga', 'anatomi']
URUT_TABEL = ['korupsi', 'anggota', 'pembanding', 'instrumen']
URUT_RUMUS = ['rh', 'es', 'oracle', 'proksi', 'agro_mean', 'agro_chu',
              'hampel', 'nnls', 'recon', 'normal', 'dmse', 'level']

# Lampiran memakai penomoran sendiri: Gambar A.1, A.2, … dan TABEL A.I, A.II, ….
# Juknis 3d membolehkan lampiran; badan naskah tetap dijaga berdiri sendiri di
# bawah 10 halaman, jadi penomoran terpisah ini juga menegaskan bahwa lampiran
# bukan bagian dari hitungan itu.
URUT_GAMBAR_LAMP = ['dekomposisi', 'proksi', 'despiking', 'dukungan', 'diurnal', 'rolling']
URUT_TABEL_LAMP = ['despiking', 'fitur', 'gagal_internal', 'tangga', 'gagal_lb',
                   'repro', 'anatomi', 'kanal']


def roman(n):
    out = ''
    for v, s in [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]:
        while n >= v:
            out, n = out + s, n - v
    return out


RUJUKAN = {}
for _i, _k in enumerate(URUT_GAMBAR, 1):
    RUJUKAN['{G:%s}' % _k] = str(_i)
for _i, _k in enumerate(URUT_TABEL, 1):
    RUJUKAN['{T:%s}' % _k] = roman(_i)
for _i, _k in enumerate(URUT_RUMUS, 1):
    RUJUKAN['{E:%s}' % _k] = str(_i)
for _i, _k in enumerate(URUT_GAMBAR_LAMP, 1):
    RUJUKAN['{G:%s}' % _k] = 'A.%d' % _i
for _i, _k in enumerate(URUT_TABEL_LAMP, 1):
    RUJUKAN['{T:%s}' % _k] = 'A.%s' % roman(_i)

# Mode lampiran: mengganti penomoran gambar dan tabel menjadi seri A. Dipasang
# sekali lewat mode_lampiran(), tepat sebelum bagian LAMPIRAN dibangun.
LAMPIRAN = [False]


def mode_lampiran():
    """Mulai lampiran: pindah halaman, lalu ganti seri penomoran ke A.

    Pemindahan halaman itu penting dan bukan kosmetik. Juknis 3b membatasi
    laporan pada 10 halaman termasuk daftar pustaka, dan juknis 3d membolehkan
    lampiran tanpa menyatakan apakah lampiran ikut dihitung. Dengan lampiran
    dimulai di halaman baru, batas antara keduanya terlihat jelas dan laporan
    tetap memenuhi pembacaan yang paling ketat.
    """
    # Pemindahannya dipasang sebagai page_break_before pada judul LAMPIRAN, bukan
    # sebagai paragraf kosong berisi w:br. Paragraf kosong itu sendiri memakan satu
    # baris, dan ketika badan naskah kebetulan berakhir persis di dasar halaman 10
    # ia terdorong ke halaman 11 lalu baru memutus, menyisakan satu halaman hampa.
    LAMPIRAN[0] = True
    fig_n[0] = 0
    tab_n[0] = 0

# Daftar pustaka dinomori menurut urutan kemunculan PERTAMA di naskah, bukan
# menurut urutan penulisan di content.py. IEEE Style menuntut itu (juknis 3c),
# dan menomorinya dengan tangan adalah cara paling mudah untuk meleset
# diam-diam: satu kalimat dipindahkan, seluruh nomor sesudahnya salah.
#
# sub_rujukan() dipanggil sekali per potongan teks dalam urutan bangun dokumen,
# dan urutan bangun itu sama dengan urutan baca. Jadi kunci yang belum pernah
# terlihat mendapat nomor berikutnya; yang sudah, memakai nomor lamanya.
PUSTAKA_URUT = {}       # slug -> nomor, menurut kemunculan pertama
PUSTAKA_BEKU = [False]  # dinyalakan setelah daftar pustaka dicetak


def nomor_pustaka(kunci):
    if kunci not in C.PUSTAKA:
        sys.exit('Sitasi ke pustaka yang tidak ada: {R:%s}\n'
                 'Tambahkan entrinya ke PUSTAKA di content.py.' % kunci)
    if kunci not in PUSTAKA_URUT:
        if PUSTAKA_BEKU[0]:
            sys.exit('Sitasi baru {R:%s} muncul SESUDAH daftar pustaka dicetak.\n'
                     'Lampiran tidak boleh memperkenalkan rujukan baru; pindahkan '
                     'sitasinya ke badan naskah, Bagian I-VII.' % kunci)
        PUSTAKA_URUT[kunci] = len(PUSTAKA_URUT) + 1
    return '[%d]' % PUSTAKA_URUT[kunci]


import re as _re
_POLA_RUJUKAN = _re.compile(r'\{[GTER]:[a-z_0-9]+\}')


def sub_rujukan(teks):
    def ganti(m):
        if m.group(0).startswith('{R:'):
            return nomor_pustaka(m.group(0)[3:-1])
        if m.group(0) not in RUJUKAN:
            sys.exit('Rujukan tidak dikenal di content.py: %s\n'
                     'Tambahkan kuncinya ke URUT_GAMBAR / URUT_TABEL / URUT_RUMUS '
                     'di build.py.' % m.group(0))
        return RUJUKAN[m.group(0)]
    _cek_kurawal(teks, 'teks naskah')
    hasil = _POLA_RUJUKAN.sub(ganti, teks)
    # Penjaga: pola di atas hanya mengenali kunci yang bersih. Kalau ada
    # yang ternoda, misalnya {G:*despiking*} setelah sebuah penyisiran
    # otomatis membubuhkan markup miring di dalam kurung kurawal, ia lolos
    # tanpa disubstitusi dan kurung kurawalnya ikut tercetak di PDF. Lebih
    # baik buildnya berhenti daripada naskahnya memuat rujukan gagal.
    sisa = re.search('\\{[GTER]:[^}]*\\}', hasil)
    if sisa:
        sys.exit('Rujukan rusak dan tidak tersubstitusi: %s. Kunci harus '
                 'polos, tanpa markup di dalam kurung kurawal.'
                 % sisa.group(0))
    return hasil


def heading1(text):
    p = para(doc, text, style=style_by_name(doc, 'Heading 1'))
    p.paragraph_format.keep_with_next = True
    return p


def heading2(text):
    p = para(doc, text, style=style_by_name(doc, 'Heading 2'))
    p.paragraph_format.keep_with_next = True
    return p


def body(text):
    return para(doc, sub_rujukan(text), style=style_by_name(doc, 'Body Text'))


def body_all(items):
    for t in items:
        body(t)


def bullets(items, num=False):
    for i, t in enumerate(items):
        p = para(doc, ('%d) ' % (i + 1) if num else '• ') + sub_rujukan(t),
                 style=style_by_name(doc, 'Body Text'))
        pf = p.paragraph_format
        pf.left_indent = Pt(12)
        pf.first_line_indent = Pt(-12)
        pf.space_after = Pt(2)


def _cek_kurawal(teks, asal):
    """Markup di dalam kurung kurawal merusak sub/superskripnya.

    Parser di build_lib.py memproses ** dan * lebih dulu, jadi ^{*oracle*}
    tidak pernah terbaca sebagai superskrip dan bintangnya ikut tercetak.
    README bagian 4 sudah melarangnya; ini yang menegakkannya.
    """
    m = re.search('[_^]\\{[^}]*[*`][^}]*\\}', teks)
    if m:
        sys.exit('Markup di dalam kurung kurawal pada %s: %s. Tanda bintang dan backtick diproses lebih dulu dan akan merusak sub/superskripnya.' % (asal, m.group(0)))

def equations(items, kunci, width=COL_W, size=9.5, num_w=0.42):
    """Blok rumus terpusat dengan nomor rata kanan, gaya IEEE.

    Dibangun sebagai tabel tanpa garis, bukan paragraf bertab: tab tengah dan
    tab kanan dalam satu paragraf ditafsirkan berbeda oleh Word dan LibreOffice
    ketika rumusnya melewati titik tengah kolom. Konsekuensinya, dua pemanggilan
    berturut-turut tanpa paragraf di antaranya akan menyatu jadi satu tabel —
    jadi kelompokkan rumus yang berdampingan ke dalam satu daftar.
    """
    t = doc.add_table(rows=len(items), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    for old in tblPr.findall(qn('w:tblLayout')):
        tblPr.remove(old)
    tblPr.append(el('w:tblLayout', **{'w:type': 'fixed'}))

    if isinstance(kunci, str):
        kunci = [kunci]
    assert len(kunci) == len(items), 'jumlah kunci rumus tidak cocok: %s' % kunci

    lebar = [width - num_w, num_w]
    for ri, teks in enumerate(items):
        eq_n[0] += 1
        if URUT_RUMUS[eq_n[0] - 1] != kunci[ri]:
            sys.exit('Urutan rumus tidak cocok pada nomor (%d): build.py memanggil '
                     '"%s" tetapi URUT_RUMUS mengharapkan "%s".'
                     % (eq_n[0], kunci[ri], URUT_RUMUS[eq_n[0] - 1]))
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
        row._tr.get_or_add_trPr().append(el('w:cantSplit'))
    for ci, col in enumerate(t.columns):
        col.width = Inches(lebar[ci])
    return para(doc, '', style=style_by_name(doc, 'Body Text'), space_after=2)


def table_block(spec, kunci, size=6.6, width=COL_W, header_rows=1):
    title, rows, widths, aligns = spec
    tab_n[0] += 1
    urut = URUT_TABEL_LAMP if LAMPIRAN[0] else URUT_TABEL
    nomor = ('A.%s' if LAMPIRAN[0] else '%s') % roman(tab_n[0])
    if urut[tab_n[0] - 1] != kunci:
        sys.exit('Urutan tabel tidak cocok pada Tabel %s: build.py memanggil "%s" '
                 'tetapi daftar urutan mengharapkan "%s".'
                 % (nomor, kunci, urut[tab_n[0] - 1]))
    cap = para(doc, 'TABEL %s.  %s' % (nomor, title.upper()),
               style=style_by_name(doc, 'table head'))
    cap.paragraph_format.keep_with_next = True
    cap.paragraph_format.space_before = Pt(8)
    cap.paragraph_format.space_after = Pt(3)
    rows = [[sub_rujukan(sel) for sel in baris] for baris in rows]
    add_table(doc, rows, widths=widths, size=size, header_rows=header_rows,
              align_cols=aligns, total_width=width)
    return para(doc, '', style=style_by_name(doc, 'Body Text'), space_after=4)


def figure_block(path, caption, kunci, width=COL_W):
    fig_n[0] += 1
    urut = URUT_GAMBAR_LAMP if LAMPIRAN[0] else URUT_GAMBAR
    nomor = ('A.%d' if LAMPIRAN[0] else '%d') % fig_n[0]
    if urut[fig_n[0] - 1] != kunci:
        sys.exit('Urutan gambar tidak cocok pada Gambar %s: build.py memanggil "%s" '
                 'tetapi daftar urutan mengharapkan "%s".'
                 % (nomor, kunci, urut[fig_n[0] - 1]))
    add_picture_para(doc, path, width)
    p = para(doc, sub_rujukan('Gambar %s.  %s' % (nomor, caption)),
             style=style_by_name(doc, 'figure caption'))
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(8)
    return p


def full_width(fn):
    """Jalankan fn() di dalam wilayah satu kolom (selebar dua kolom)."""
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
    r.font.size = Pt(18)


def ukuran_email(email, lebar_in):
    """Perkecil font surel secukupnya supaya muat satu baris."""
    muat = (lebar_in * 72) / (len(email) * 0.45)
    return max(6.5, min(9.0, int(muat * 2) / 2))


at = doc.add_table(rows=1, cols=len(C.PENULIS))
at.alignment = WD_TABLE_ALIGNMENT.CENTER
at.autofit = False
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
    lines = [(nama, 10, True, False), ('NIM %s' % nim, 9, False, False),
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

pend = para(doc, '', space_before=0, space_after=0)
pend.paragraph_format.line_spacing = Pt(11)
attach_section_break(pend, SEC1)

# ------------------------------------------------------------------- ABSTRAK
p = para(doc, '', style=style_by_name(doc, 'Abstract'))
p.paragraph_format.space_before = Pt(12)
add_runs(p, 'Abstrak—', size=9, bold=True, italic=True)
add_runs(p, sub_rujukan(C.INTISARI), size=9, bold=True)

p = para(doc, '', style=style_by_name(doc, 'Keywords'))
add_runs(p, 'Kata kunci—', size=9, bold=True, italic=True)
add_runs(p, C.KATA_KUNCI, size=9, italic=True)

# --------------------------------------------------------------- I PENDAHULUAN
heading1('I.  PENDAHULUAN')
body_all(C.PENDAHULUAN_LATAR)
body_all(C.KONTRIBUSI_PEMBUKA)
bullets(C.KONTRIBUSI_ITEMS, num=True)
body_all(C.KONTRIBUSI_PENUTUP)

# ----------------------------------------------- II AKUISISI DAN EKSPLORASI
heading1('II.  AKUISISI DAN EKSPLORASI DATA')
heading2('A.  Anatomi Dataset')
body(C.DATA_ANATOMI[0])
body_all(C.DATA_ANATOMI[1:])

heading2('B.  Bentuk Pemisahan Latih–Uji')
full_width(lambda: figure_block(
    fig('01-target-dan-jendela.png'),
    'Tugas dan cacatnya dalam satu tarikan napas. (a) Deret target sepanjang '
    'kalender; blok terarsir adalah 734 baris uji yang seluruh labelnya ditahan. '
    '(b) Suhu udara mentah pada sumbu waktu yang sama; 16 titik merah adalah nilai '
    'di luar rentang 5–45 °C, yang secara fisis mustahil pada stasiun ini dan '
    'karena itu merupakan korupsi, bukan cuaca.', 'target', width=FULL_W))
body_all(C.DATA_PEMISAHAN)

heading2('C.  Uji Derau Target dan Korupsi Prediktor')
body_all(C.DATA_KORUPSI[:3])
full_width(lambda: figure_block(
    fig('02-residu-loo.png'),
    'Sebaran residu interpolasi kuadratik tinggalkan-satu, dinormalkan terhadap '
    'simpangan baku robusnya, sumbu tegak berskala log. Garis putus-putus menandai '
    '±6 sd robus. Target berekor hampir normal; kedua prediktor memuat massa yang '
    'jelas terpisah di luar ±10 sd robus, tanda tangan lonjakan yang disuntikkan, '
    'bukan derau alami.', 'residu', width=FULL_W))
body_all(C.DATA_KORUPSI[3:])
table_block(T.T2, 'korupsi', size=6.5)

# -------------------------------------------------------- III METODE ANALISIS
heading1('III.  METODE ANALISIS')
body_all(C.METODE_PEMBUKA)

heading2('A.  Kerangka Fisis: yang Diramalkan Sebenarnya Bukan RH')
body(C.METODE_FISIS[0])
equations(C.EQ_RH, 'rh')
body(C.METODE_FISIS[1])
equations(C.EQ_ES, 'es')
body_all(C.METODE_FISIS[2:])

heading2('B.  Batas Oracle: Resolusi yang Benar-Benar Berguna')
body(C.METODE_ORACLE[0])
equations(C.EQ_ORACLE, 'oracle')
body_all(C.METODE_ORACLE[1:])
figure_block(fig('03-kurva-oracle.png'),
             'Kurva oracle. Setiap titik menyatakan RMSE yang dicapai kalau tekanan '
             'uap diketahui sempurna pada resolusi waktu tersebut. Bintang menandai '
             'tempat model kami mendarat.', 'oracle', width=COL_W)

heading2('C.  Proksi Titik Embun Bebas-Parameter')
body(C.METODE_PROKSI[0])
equations(C.EQ_PROKSI, 'proksi')
body_all(C.METODE_PROKSI[1:])

heading2('D.  Rekayasa Balik Blok Agronomi')
body_all(C.METODE_AGRO[:3])
equations(C.EQ_AGRO[:1], 'agro_mean')
body(C.METODE_AGRO[3])
equations(C.EQ_AGRO[1:], 'agro_chu')
body_all(C.METODE_AGRO[4:])

heading2('E.  Pergeseran Distribusi Latih ke Uji')
body_all(C.METODE_GESER)

heading2('F.  Desain Validasi')
body_all(C.METODE_VALIDASI)

# ------------------------------------------------------------ IV PRA-PEMROSESAN
heading1('IV.  PRA-PEMROSESAN')
heading2('A.  Despiking Hampel')
body_all(C.PRA_DESPIKE[:2])
equations(C.EQ_HAMPEL, 'hampel')
body(C.PRA_DESPIKE[2])
body_all(C.PRA_DESPIKE[3:])


heading2('B.  Rekayasa Fitur dan Batas Kebocoran')
body_all(C.PRA_FITUR)

# ----------------------------------------------------------------- V PEMODELAN
heading1('V.  PEMODELAN')
heading2('A.  Enam Anggota dan Alasan Masing-Masing Ada')
body(C.MODEL_ANGGOTA[0])
full_width(lambda: table_block(T.T6, 'anggota', size=6.5, width=FULL_W))
body_all(C.MODEL_ANGGOTA[1:])

heading2('B.  Blending: NNLS, Pita Waktu-Hari, dan Bias Diurnal')
body(C.MODEL_BLEND[0])
equations(C.EQ_NNLS, 'nnls')
body_all(C.MODEL_BLEND[1:])

heading2('C.  De-bias Level per Anggota')
body(C.MODEL_DEBIAS[0])
figure_block(fig('08-bias-anggota.png'),
             'Rerata galat bertanda setiap anggota blend pada blok validasi maju, '
             'dibanding rerata galat bertanda di dalam sampel. Satu anggota berada '
             'jauh di luar kelompok, dan bias dalam-sampelnya tetap nol.', 'bias', width=COL_W)
body_all(C.MODEL_DEBIAS[1:])

heading2('D.  Rekonsiliasi Lintasan Berbasis Increment')
body_all(C.MODEL_INCREMENT[:2])
equations(C.EQ_RECON[:1], 'recon')
body(C.MODEL_INCREMENT[3])
equations(C.EQ_RECON[1:], 'normal')
body_all(C.MODEL_INCREMENT[4:])
figure_block(fig('07-rekonsiliasi-increment.png'),
             'RMSE pada tiga blok validasi maju, sebelum dan sesudah rekonsiliasi '
             'lintasan. Perbaikannya konsisten pada ketiga blok.', 'increment', width=COL_W)

heading2('E.  Bukti Buta-Target dan Reproduksibilitas')
body_all(C.MODEL_BUTA)

# --------------------------------------------------- VI EVALUASI DAN PEMBAHASAN
heading1('VI.  EVALUASI DAN PEMBAHASAN')
heading2('A.  Pembanding Sejawat')
body(C.EVAL_PEMBANDING[0])
full_width(lambda: table_block(T.T10, 'pembanding', size=6.4, width=FULL_W))
body_all(C.EVAL_PEMBANDING[1:3])
full_width(lambda: figure_block(
    fig('14-pembanding.png'),
    'Tujuh metode pada sembilan lipatan titik-asal bergulir dan 6.480 baris '
    'luar-lipatan yang sama. (a) RMSE terkumpul; warna menandai kelas metode. '
    '(b) RMSE per lipatan untuk tiga metode teratas; ketiganya tidak pernah '
    'berpotongan, sehingga urutannya bukan hasil undian satu jendela.',
    'pembanding', width=FULL_W))
body(C.EVAL_PEMBANDING[3])

heading2('B.  Hasil Menyeluruh')
body(C.EVAL_HASIL[0])
figure_block(fig('10-tangga-leaderboard.png'),
             'Tangga skor papan peringkat publik untuk konfigurasi yang berturut-turut '
             'diadopsi. Bintang menandai satu-satunya perubahan struktural.', 'tangga', width=COL_W)
body_all(C.EVAL_HASIL[1:])

heading2('C.  Anatomi Galat yang Tersisa')
body(C.EVAL_ANATOMI[0])
full_width(lambda: figure_block(
    fig('09-anatomi-galat.png'),
    'Pembedahan galat pada baris luar-lipatan. (a) Bagian jumlah kuadrat galat per '
    'pita jam. (b) Galat bertanda pada pita yang sama; dua pita terburuk juga yang '
    'paling bias. (c) Pemisahan galat menjadi komponen offset per hari dan komponen '
    'bentuk di dalam hari, masing-masing dengan kemiringan kalibrasinya.',
    'anatomi', width=FULL_W))
body_all(C.EVAL_ANATOMI[1:])

heading2('D.  Diagnostik Pasca-Model: Kalibrasi Level dan Dispersi')
body_all(C.EVAL_INSTRUMEN[:2])
equations(C.EQ_DMSE, 'dmse')
body_all(C.EVAL_INSTRUMEN[2:4])
equations(C.EQ_LEVEL, 'level')
body(C.EVAL_INSTRUMEN[4])
table_block(T.T8, 'instrumen', size=6.8)
body_all(C.EVAL_INSTRUMEN[5:])

heading2('E.  Katalog Kegagalan')
body_all(C.EVAL_KEGAGALAN)

heading2('F.  Keterbatasan')
bullets(C.EVAL_BATAS, num=True)

# -------------------------------------------------------------- VII KESIMPULAN
heading1('VII.  KESIMPULAN')
body_all(C.KESIMPULAN)

# --------------------------------------------------------------- DAFTAR PUSTAKA
heading1('DAFTAR PUSTAKA')

# Penjaga: entri yang tidak pernah disitasi adalah cacat IEEE Style yang tidak
# terlihat dari membaca naskah, hanya dari menyilangkan daftar dengan teksnya.
# Lebih baik buildnya berhenti daripada laporan memuat pustaka hantu.
_tak_disitasi = [k for k in C.PUSTAKA if k not in PUSTAKA_URUT]
if _tak_disitasi:
    sys.exit('Pustaka tidak pernah disitasi di badan naskah: %s\n'
             'IEEE Style menuntut setiap entri dirujuk. Sitasi dengan {R:kunci} '
             'di content.py, atau buang entrinya dari PUSTAKA.'
             % ', '.join(sorted(_tak_disitasi)))

for _kunci, _i in sorted(PUSTAKA_URUT.items(), key=lambda kv: kv[1]):
    p = para(doc, '', style=style_by_name(doc, 'references'))
    add_runs(p, '[%d]\t%s' % (_i, C.PUSTAKA[_kunci]), size=7.5)
    pf = p.paragraph_format
    pf.left_indent = Pt(16)
    pf.first_line_indent = Pt(-16)

# Sesudah titik ini rujukan baru tidak boleh muncul lagi: nomornya tidak akan
# pernah tercetak di daftar yang sudah lewat.
PUSTAKA_BEKU[0] = True

# ------------------------------------------------------------------ LAMPIRAN
# Juknis 3d. Ditempatkan setelah daftar pustaka dan diberi penomoran seri A,
# supaya batas antara laporan 10 halaman dan bahan tambahan tidak kabur.
mode_lampiran()
heading1('LAMPIRAN')
doc.paragraphs[-1].paragraph_format.page_break_before = True
body_all(L.LAMPIRAN_PEMBUKA)

heading2('A.  Dekomposisi Fisis Kelembapan Relatif')
body(L.LAMP_DEKOMPOSISI[0])
figure_block(fig('04-dekomposisi-fisis.png'),
             'Dekomposisi Persamaan ({E:rh}) pada sepuluh hari yang sama. Ayunan '
             'tajam pada (a) berasal dari (b); (c) bergerak jauh lebih lambat.',
             'dekomposisi', width=COL_W)
body_all(L.LAMP_DEKOMPOSISI[1:])

heading2('B.  Proksi Titik Embun Bebas-Parameter')
body(L.LAMP_PROKSI[0])
full_width(lambda: figure_block(
    fig('13-proksi-titik-embun.png'),
    'Penduga Persamaan (4) tanpa satu pun parameter yang dipasang. (a) Sebaran '
    'gabungan terhadap target, garis putus-putus adalah identitas. (b) Kedua deret '
    'berdampingan pada sepuluh hari; proksi menangkap fase dan sebagian besar '
    'amplitudo, dan meleset terutama pada tingkat hariannya.', 'proksi', width=FULL_W))
body_all(L.LAMP_PROKSI[1:])

heading2('C.  Despiking Hampel pada Penggal Terburuk')
body(L.LAMP_DESPIKE[0])
figure_block(fig('11-despiking.png'),
             'Penapis Hampel pada penggal dengan penolakan terpadat. Empat dari 16 '
             'nilai yang ditolak berada di jendela ini; transisi diurnal yang asli '
             'tidak tersentuh.', 'despiking', width=COL_W)
table_block(T.T4, 'despiking', size=6.8)
body_all(L.LAMP_DESPIKE[1:])

heading2('D.  Audit Dukungan per Kanal')
body(L.LAMP_DUKUNGAN[0])
figure_block(fig('05-audit-dukungan.png'),
             'Rasio simpangan baku uji terhadap latih untuk setiap kanal eksogen. '
             'Ketiga kolom `water_volume_*` benar-benar konstan di jendela uji, '
             'sehingga rasionya nol.', 'dukungan', width=COL_W)
body_all(L.LAMP_DUKUNGAN[1:])

heading2('E.  Katalog Blok Fitur')
body(L.LAMP_FITUR[0])
full_width(lambda: table_block(T.T5, 'fitur', size=6.5, width=FULL_W))
body_all(L.LAMP_FITUR[1:])

heading2('F.  Struktur Diurnal Kanal Iklim Mikro')
body(L.LAMP_DIURNAL[0])
full_width(lambda: figure_block(
    fig('12-klimatologi-diurnal.png'),
    'Klimatologi diurnal pada baris latih: rerata per jam-hari dengan pita ±1 '
    'simpangan baku. RH dan suhu berlawanan fase; CO₂ berpuncak bersama RH '
    'menjelang subuh karena keduanya menjejak lapisan batas malam yang sama.',
    'diurnal', width=FULL_W))
body_all(L.LAMP_DIURNAL[1:])

heading2('G.  Protokol Validasi Titik-Asal Bergulir')
body(L.LAMP_VALIDASI[0])
figure_block(fig('06-titik-asal-bergulir.png'),
             'Sembilan lipatan titik-asal bergulir. Baris paling bawah adalah '
             'tugas yang sebenarnya; kemiripan bentuknya dengan kesembilan '
             'lipatan di atasnya adalah alasan protokol ini dipilih.',
             'rolling', width=COL_W)
body_all(L.LAMP_VALIDASI[1:])

heading2('H.  Katalog Kegagalan Selengkapnya')
body(L.LAMP_GAGAL_INTERNAL[0])
full_width(lambda: table_block(T.T9, 'gagal_internal', size=6.3, width=FULL_W))
body_all(L.LAMP_GAGAL_INTERNAL[1:])
body(L.LAMP_TANGGA[0])
table_block(T.T7, 'tangga', size=6.2)
body(L.LAMP_KEGAGALAN[0])
full_width(lambda: table_block(T.TA1, 'gagal_lb', size=6.3, width=FULL_W))
body_all(L.LAMP_KEGAGALAN[1:])

heading2('I.  Kontrak Reproduksibilitas')
body(L.LAMP_REPRO[0])
table_block(T.TA2, 'repro', size=6.4)
body_all(L.LAMP_REPRO[1:])

heading2('J.  Audit Seluruh Kanal Eksogen')
body(L.LAMP_ANATOMI[0])
table_block(T.T1, 'anatomi', size=6.8)
body_all(L.LAMP_ANATOMI[1:])
body(L.LAMP_KANAL[0])
full_width(lambda: table_block(T.TA3, 'kanal', size=6.2, width=FULL_W))
body_all(L.LAMP_KANAL[1:])

cp = doc.core_properties
cp.author = META_PENULIS
cp.last_modified_by = META_PENULIS
cp.title = META_JUDUL
cp.subject = META_SUBJEK
cp.keywords = META_KATA_KUNCI
cp.category = 'Laporan Ilmiah'
cp.comments = ''
cp.language = 'id-ID'
cp.revision = 1

if BORDER_MODE != 'off':
    _skala, _margin = BORDER_GEOM[BORDER_MODE]
    periksa_border(_skala, _margin)
    pasang_border(doc, _skala, siapkan_border_png())
    print('       border NSC dipasang, mode %r, skala %.2f' % (BORDER_MODE, _skala))

out_docx = os.path.join(OUTDIR, NAMA_BERKAS + '.docx')
out_pdf = os.path.join(OUTDIR, NAMA_BERKAS + '.pdf')
doc.save(out_docx)
tulis_metadata_docx(out_docx)
print('DOCX  ->', out_docx)
print('       badan: %d gambar, %d tabel, %d rumus, %d referensi'
      % (len(URUT_GAMBAR), len(URUT_TABEL), eq_n[0], len(PUSTAKA_URUT)))
print('       lampiran: %d gambar, %d tabel'
      % (len(URUT_GAMBAR_LAMP), len(URUT_TABEL_LAMP)))

produser = ekspor_pdf(out_docx, out_pdf)
if produser:
    tulis_metadata_pdf(out_pdf, produser)
    try:
        from pypdf import PdfReader
        n_hal = len(PdfReader(out_pdf).pages)
    except Exception:
        n_hal = None
    print('PDF   ->', out_pdf)
    print('       %.2f MB, lewat %s' % (os.path.getsize(out_pdf) / 1e6, produser))
    # Juknis 3b membatasi laporan pada 10 halaman termasuk daftar pustaka;
    # juknis 3d membolehkan lampiran tanpa menyatakan apakah ia ikut dihitung.
    # Yang diperiksa di sini adalah pembacaan yang lebih ketat: badan naskah
    # beserta daftar pustaka, yaitu segala sesuatu sebelum halaman LAMPIRAN,
    # harus muat dalam 10 halaman sendirian.
    if n_hal is not None:
        hal_lampiran = None
        try:
            from pypdf import PdfReader
            for i, hal in enumerate(PdfReader(out_pdf).pages, 1):
                if 'LAMPIRAN' in (hal.extract_text() or ''):
                    hal_lampiran = i
                    break
        except Exception:
            pass
        if hal_lampiran:
            n_badan = hal_lampiran - 1
            tanda = 'OK' if n_badan <= 10 else 'LEWAT BATAS'
            print('       %d halaman total; badan + daftar pustaka %d halaman '
                  '(batas juknis 10) -> %s' % (n_hal, n_badan, tanda))
            print('       lampiran mulai halaman %d' % hal_lampiran)
        else:
            tanda = 'OK' if n_hal <= 10 else 'LEWAT BATAS'
            print('       %d halaman (batas juknis 10) -> %s' % (n_hal, tanda))
else:
    print('PDF   -> dilewati: Word maupun LibreOffice tidak ditemukan. '
          'Buka DOCX lalu Save As PDF.')

# Folder output/ adalah yang dilihat manusia saat mengunggah, jadi isinya dijaga
# tepat dua berkas: build lama dengan nomor tim berbeda dan berkas kunci
# LibreOffice akan menumpuk kalau dibiarkan.
disimpan = {os.path.basename(out_docx), os.path.basename(out_pdf)}
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
    print('SAPU  -> %d berkas sisa dihapus dari output/' % len(disapu))
