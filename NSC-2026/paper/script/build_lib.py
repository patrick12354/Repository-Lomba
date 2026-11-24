"""Helper layer untuk membangun technical report di atas template IEEE A4."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

W = qn  # alias


def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), str(v))
    return e


def style_by_name(doc, name):
    for s in doc.styles:
        if s.name == name:
            return s
    raise KeyError(name)


def strip_numbering(doc, names):
    for n in names:
        st = style_by_name(doc, n)
        ppr = st._element.find(qn('w:pPr'))
        if ppr is None:
            continue
        for np in ppr.findall(qn('w:numPr')):
            ppr.remove(np)


def clear_body(doc):
    body = doc.element.body
    sect = body.find(qn('w:sectPr'))
    for child in list(body):
        if child is not sect:
            body.remove(child)
    return sect


def set_cols(sectPr, num, space=360):
    for c in sectPr.findall(qn('w:cols')):
        sectPr.remove(c)
    c = el('w:cols', **{'w:num': num, 'w:space': space, 'w:equalWidth': 'true', 'w:sep': 'false'})
    # cols harus muncul setelah pgMar
    sectPr.append(c)


def make_sectPr(template_sectPr, num_cols):
    sp = copy.deepcopy(template_sectPr)
    for t in sp.findall(qn('w:type')):
        sp.remove(t)
    t = el('w:type', **{'w:val': 'continuous'})
    sp.insert(0, t)
    set_cols(sp, num_cols)
    return sp


def attach_section_break(paragraph, sectPr):
    """Paragraf ini menjadi paragraf terakhir dari section dengan sectPr tsb."""
    p = paragraph._p
    ppr = p.get_or_add_pPr()
    for old in ppr.findall(qn('w:sectPr')):
        ppr.remove(old)
    ppr.append(sectPr)


# ---------- paragraf ----------

def para(doc, text='', style=None, size=None, bold=None, italic=None,
         align=None, space_before=None, space_after=None, first_line=None,
         keep_with_next=False, line=None):
    p = doc.add_paragraph(style=style)
    if text:
        add_runs(p, text, size=size, bold=bold, italic=italic)
    pf = p.paragraph_format
    if align is not None:
        pf.alignment = align
    if space_before is not None:
        pf.space_before = Pt(space_before)
    if space_after is not None:
        pf.space_after = Pt(space_after)
    if first_line is not None:
        pf.first_line_indent = Pt(first_line)
    if line is not None:
        pf.line_spacing = line
    if keep_with_next:
        pf.keep_with_next = True
    return p


def add_runs(p, text, size=None, bold=None, italic=None):
    """Markup ringan: **tebal**, *miring*, _{subskrip}, ^{superskrip}.

    Subskrip dan superskrip hanya dikenali dalam bentuk berkurung kurawal,
    sehingga nama kolom seperti `water_volume_line1` dan `soil_temp_line1`
    tetap ditulis apa adanya.
    """
    import re
    pola = (r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|_\{[^}]*\}|\^\{[^}]*\})')
    for tok in re.split(pola, text):
        if not tok:
            continue
        b, i = bold, italic
        sub = sup = mono = False
        s = tok
        if tok.startswith('**') and tok.endswith('**') and len(tok) > 4:
            s, b = tok[2:-2], True
        elif tok.startswith('*') and tok.endswith('*') and len(tok) > 2:
            s, i = tok[1:-1], True
        elif tok.startswith('`') and tok.endswith('`') and len(tok) > 2:
            # Nama kolom dan bendera ditulis di antara backtick di seluruh
            # naskah. Sebelumnya token ini tidak dikenali, jadi kedua tandanya
            # ikut tercetak; sekarang isinya dirender monospace tanpa tanda.
            s, mono = tok[1:-1], True
        elif tok.startswith('_{') and tok.endswith('}'):
            s, sub = tok[2:-1], True
        elif tok.startswith('^{') and tok.endswith('}'):
            s, sup = tok[2:-1], True
        r = p.add_run(s)
        if mono:
            r.font.name = 'Consolas'
            rpr = r._element.get_or_add_rPr()
            rf = rpr.find(qn('w:rFonts'))
            if rf is None:
                rf = OxmlElement('w:rFonts')
                rpr.append(rf)
            for atr in ('w:ascii', 'w:hAnsi', 'w:cs'):
                rf.set(qn(atr), 'Consolas')
        if size is not None:
            r.font.size = Pt(size - 0.5 if mono else size)
        if b is not None:
            r.font.bold = b
        if i is not None:
            r.font.italic = i
        r.font.subscript = sub
        r.font.superscript = sup
    return p


def set_tabstops(paragraph, stops):
    """stops: [(posisi_inci, 'left'|'center'|'right'), ...]."""
    pf = paragraph.paragraph_format
    ppr = paragraph._p.get_or_add_pPr()
    for old in ppr.findall(qn('w:tabs')):
        ppr.remove(old)
    tabs = el('w:tabs')
    for pos, jenis in stops:
        tabs.append(el('w:tab', **{'w:val': jenis, 'w:pos': int(round(pos * 1440))}))
    ppr.append(tabs)
    return paragraph


def add_math_runs(p, text, size=None):
    """Markup rumus. *miring* untuk variabel, _{...} subskrip, ^{...} superskrip.

    Nama fungsi (softmax, GELU, exp) sengaja tetap tegak, sesuai kebiasaan
    penulisan matematika, jadi yang dimiringkan harus ditandai satu per satu.
    """
    import re

    pola = re.compile(r'(\*[^*]+\*|_\{[^}]*\}|\^\{[^}]*\}|_[A-Za-z0-9]|\^[A-Za-z0-9])')
    for tok in pola.split(text):
        if not tok:
            continue
        italic = False
        sub = sup = False
        s = tok
        if tok.startswith('*') and tok.endswith('*') and len(tok) > 2:
            s, italic = tok[1:-1], True
        elif tok.startswith('_'):
            s, sub = (tok[2:-1] if tok[1] == '{' else tok[1:]), True
        elif tok.startswith('^'):
            s, sup = (tok[2:-1] if tok[1] == '{' else tok[1:]), True
        r = p.add_run(s)
        r.font.name = 'Times New Roman'
        if size is not None:
            r.font.size = Pt(size)
        if italic or sub or sup:
            r.font.italic = True
        if sub:
            r.font.subscript = True
        if sup:
            r.font.superscript = True
    return p


# ---------- tabel ----------

def set_cell_text(cell, text, size=7.5, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT,
                  italic=False):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.alignment = align
    add_runs(p, text, size=size, bold=bold or None, italic=italic or None)
    for r in p.runs:
        r.font.name = 'Times New Roman'
        rpr = r._element.get_or_add_rPr()
        rf = rpr.find(qn('w:rFonts'))
        if rf is None:
            rf = el('w:rFonts')
            rpr.insert(0, rf)
        rf.set(qn('w:ascii'), 'Times New Roman')
        rf.set(qn('w:hAnsi'), 'Times New Roman')


def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.find(qn('w:tcBorders'))
    if borders is None:
        borders = el('w:tcBorders')
        tcPr.append(borders)
    for name, val in (('top', top), ('bottom', bottom), ('left', left), ('right', right)):
        if val is None:
            continue
        for old in borders.findall(qn('w:' + name)):
            borders.remove(old)
        b = el('w:' + name, **{'w:val': 'single' if val else 'none',
                               'w:sz': val if val else 0, 'w:space': 0, 'w:color': '000000'})
        borders.append(b)


def add_table(doc, rows, widths=None, size=7.5, header_rows=1, align_cols=None,
              total_width=3.30, caption_align=None):
    """rows: list of list of str. Baris pertama = header (kecuali header_rows=0)."""
    ncol = len(rows[0])
    t = doc.add_table(rows=len(rows), cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    for old in tblPr.findall(qn('w:tblLayout')):
        tblPr.remove(old)
    tblPr.append(el('w:tblLayout', **{'w:type': 'fixed'}))
    if widths is None:
        widths = [1.0 / ncol] * ncol
    tot = sum(widths)
    widths = [w / tot * total_width for w in widths]
    for row in t.rows:
        for idx, cell in enumerate(row.cells):
            cell.width = Inches(widths[idx])
    for idx, col in enumerate(t.columns):
        col.width = Inches(widths[idx])

    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci)
            a = WD_ALIGN_PARAGRAPH.LEFT
            if align_cols and ci < len(align_cols):
                a = {'l': WD_ALIGN_PARAGRAPH.LEFT, 'c': WD_ALIGN_PARAGRAPH.CENTER,
                     'r': WD_ALIGN_PARAGRAPH.RIGHT}[align_cols[ci]]
            if ri < header_rows:
                a = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_text(cell, val, size=size, bold=(ri < header_rows), align=a)
            # garis horizontal saja (gaya IEEE)
            top = 6 if ri == 0 else (6 if ri == header_rows else 0)
            bottom = 6 if ri == len(rows) - 1 else 0
            set_cell_borders(cell, top=top, bottom=bottom, left=0, right=0)
            cell.vertical_alignment = 1
            tcPr = cell._tc.get_or_add_tcPr()
            mar = el('w:tcMar')
            for side, v in (('top', 20), ('bottom', 20), ('left', 60), ('right', 60)):
                mar.append(el('w:' + side, **{'w:w': v, 'w:type': 'dxa'}))
            tcPr.append(mar)
    # cegah baris terpisah antar halaman/kolom
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(el('w:cantSplit'))
    # Cegah SELURUH tabel terpisah antar kolom. cantSplit hanya menjaga satu
    # baris tetap utuh; tanpa keepNext pada setiap paragraf kecuali baris
    # terakhir, Word tetap boleh memotong tabel di antara dua barisnya, dan
    # tabel pendek yang terbelah dua kolom terbaca seperti dua tabel berbeda.
    for row in t.rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    if header_rows:
        for ri in range(header_rows):
            trPr = t.rows[ri]._tr.get_or_add_trPr()
            trPr.append(el('w:tblHeader'))
    return t


def add_picture_para(doc, path, width_in, align=WD_ALIGN_PARAGRAPH.CENTER):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = align
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(path, width=Inches(width_in))
    return p
