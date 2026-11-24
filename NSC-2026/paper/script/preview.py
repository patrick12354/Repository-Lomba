# -*- coding: utf-8 -*-
"""Render setiap halaman PDF keluaran menjadi PNG untuk diperiksa mata.

Letak     : NSC UB/paper/script/preview.py
Jalankan  : python preview.py            (seluruh halaman)
            python preview.py 3 4        (hanya halaman 3 dan 4)
Keluaran  : NSC UB/paper/preview/hal-NN.png

Dipakai untuk memeriksa hal-hal yang tidak terlihat dari kode: gambar yang
terpotong, tabel yang melebar keluar kolom, baris tunggal yang menggantung di
akhir kolom, keterangan gambar yang terpisah dari gambarnya, dan jumlah halaman.
Folder preview/ adalah artefak sekali pakai dan tidak perlu ikut di-commit.
"""
import os
import sys
import glob

import fitz  # PyMuPDF

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
OUTDIR = os.path.join(PAPER, 'output')
PREVIEW = os.path.join(PAPER, 'preview')

DPI = 110  # cukup untuk membaca judul dan melihat tata letak


def main():
    pdfs = sorted(glob.glob(os.path.join(OUTDIR, '*.pdf')))
    if not pdfs:
        sys.exit('Tidak ada PDF di %s. Jalankan build.py dulu.' % OUTDIR)
    src = pdfs[0]
    halaman = [int(a) for a in sys.argv[1:]] or None

    os.makedirs(PREVIEW, exist_ok=True)
    for f in glob.glob(os.path.join(PREVIEW, '*.png')):
        os.remove(f)

    doc = fitz.open(src)
    print('%s — %d halaman' % (os.path.basename(src), len(doc)))
    for i, page in enumerate(doc, 1):
        if halaman and i not in halaman:
            continue
        pix = page.get_pixmap(dpi=DPI)
        p = os.path.join(PREVIEW, 'hal-%02d.png' % i)
        pix.save(p)
        print('  %s  %6.1f KB' % (os.path.basename(p), os.path.getsize(p) / 1024))
    doc.close()


if __name__ == '__main__':
    main()
