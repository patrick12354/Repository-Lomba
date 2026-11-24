"""Build paper: figur -> DOCX (templat ICC CDW 2026) -> PDF (dirender MS Word) -> preview PNG + cek otomatis.

Pemakaian (dari folder paper/script):
    ../.venv/bin/python build.py              # build penuh
    ../.venv/bin/python build.py --no-fig     # lewati regenerasi figur (lebih cepat)
    ../.venv/bin/python build.py --soffice    # render PDF pakai LibreOffice (kalau Word tidak ada)

Output: ../output/<NAMA_TIM>_ICC2026_Semifinal.docx dan .pdf, preview/hal-XX.png untuk dicek visual.
"""
import re
import subprocess
import sys
from pathlib import Path

import content
import figures
from docx_builder import Builder

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "output"
PREVIEW = HERE / "preview"
NAMA_TIM = content.META["tim"]
NAMA = f"{NAMA_TIM}_ICC2026_Semifinal"

# kunci figur di content.py -> file PNG dari figures.py
FIG = {"masalah": "f_masalah", "pohon": "f_pohon_masalah", "llm": "f_llm", "posisi": "f_positioning",
       "arsitektur": "f_arsitektur", "siklus": "f_siklus", "mri": "f_mri", "kohort": "f_kohort",
       "segmentasi": "f_segmentasi", "contoh_seg": "f_contoh_seg", "penilaian": "f_penilaian",
       "bkt": "f_bkt", "mockup": "f_mockup", "gantt": "f_gantt", "llm_uji": "f_llm_uji"}

# kata/frasa yang sering menandai tulisan AI (skill ai-paraphrase); hanya peringatan
AI_WORDS = ["krusial", "menggarisbawahi", "lanskap", "memainkan peran penting", "tak terpisahkan", "selaras dengan",
            "wawasan berharga", "bukti nyata", "tidak hanya", "bukan sekadar", "secara signifikan", "memastikan bahwa",
            "sangat penting", "berbagai aspek", "era digital", "revolusioner", "inovatif", "holistik", "komprehensif",
            "seamless", "robust", "memanfaatkan potensi", "menjadi kunci", "di tengah", "lebih lanjut", "selain itu"]


def semua_teks():
    t = [content.META["judul"], content.META["abstrak"], content.META["kata_kunci"]] + list(content.REFS.values())
    for b in content.BODY:
        t += [x for x in b[1:] if isinstance(x, str)]
        if b[0] == "table":
            t += [c for row in b[4] for c in row] + b[3]
    return t


def lint():
    teks = "\n".join(semua_teks())
    if "—" in teks or "–" in teks:
        for line in teks.splitlines():
            if "—" in line or "–" in line:
                print("  EM/EN DASH:", line[:120])
        sys.exit("BUILD GAGAL: ada em dash / en dash di content.py (dilarang).")
    low = teks.lower()
    hit = [w for w in AI_WORDS if w in low]
    if hit:
        print("  [gaya] kata pantauan AI ditemukan:", ", ".join(hit))


def build_docx(path):
    figs = [b[1] for b in content.BODY if b[0] == "fig"]
    figs += [b[1] for b in getattr(content, "LAMPIRAN", []) if b[0] == "img"]
    tabs = [b[1] for b in content.BODY if b[0] == "table"]
    bd = Builder(content.META, content.REFS, figs, tabs)
    for b in content.BODY:
        k = b[0]
        if k == "h1": bd.h1(b[1])
        elif k == "h2": bd.h2(b[1])
        elif k == "p": bd.para(b[1])
        elif k == "bullet": bd.bullet(b[1])
        elif k == "eq": bd.equation(b[1], b[2])
        elif k == "fig":
            bd.figure(b[1], figures.OUT / f"{FIG[b[1]]}.png", b[2], full=len(b) > 3 and b[3])
        elif k == "table":
            bd.table(b[1], b[2], b[3], b[4], b[5], full=len(b) > 6 and b[6], align=b[7] if len(b) > 7 else None)
        else:
            raise ValueError(k)
    for b in getattr(content, "LAMPIRAN", []):
        if b[0] == "unh": bd.unnumbered(b[1])
        elif b[0] == "p": bd.para(b[1])
        elif b[0] == "img": bd.figure(b[1], HERE / b[2], b[3])
        else:
            raise ValueError(b[0])
    bd.references()
    bd.save(path)


def pdf_word(docx, pdf):
    # Word menyimpan cache per path: file yang sama dibuka ulang = versi lama yang dirender.
    # Render dari salinan bernama unik supaya selalu membaca isi terbaru.
    import shutil, tempfile, time
    tmp = Path(tempfile.gettempdir()) / f"icc_render_{int(time.time() * 1000)}.docx"
    shutil.copy(docx, tmp)
    try:
        _pdf_word(tmp, pdf)
    finally:
        tmp.unlink(missing_ok=True)


def _pdf_word(docx, pdf):
    script = f'''
    tell application "Microsoft Word"
        open POSIX file "{docx}"
        set d to active document
        save as d file name "{pdf}" file format format PDF
        close d saving no
    end tell'''
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=300)


def pdf_soffice(docx, pdf):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(pdf.parent), str(docx)],
                   check=True, capture_output=True, timeout=300)


def periksa_pdf(pdf):
    import pymupdf
    PREVIEW.mkdir(exist_ok=True)
    for f in PREVIEW.glob("hal-*.png"):
        f.unlink()
    d = pymupdf.open(pdf)
    teks = ""
    for i, pg in enumerate(d):
        pg.get_pixmap(dpi=110).save(PREVIEW / f"hal-{i + 1:02d}.png")
        teks += pg.get_text()
    print(f"  PDF: {len(d)} halaman, preview di {PREVIEW.relative_to(HERE.parent)}/")
    masalah = [s for s in ["{cite:", "{fig:", "{tab:", "**", "Error!", "[Nama"] if s in teks]
    if masalah:
        print("  [cek pdf] ditemukan:", masalah, "(placeholder penulis '[Nama' memang disengaja sampai diisi)")


def main():
    OUT.mkdir(exist_ok=True)
    lint()
    if "--no-fig" not in sys.argv:
        print("figur ...")
        figures.build_all()
    docx, pdf = OUT / f"{NAMA}.docx", OUT / f"{NAMA}.pdf"
    print("docx ...")
    build_docx(docx)
    print("pdf ...")
    (pdf_soffice if "--soffice" in sys.argv else pdf_word)(docx, pdf)
    periksa_pdf(pdf)
    print("selesai:", docx.name, pdf.name)


if __name__ == "__main__":
    main()
