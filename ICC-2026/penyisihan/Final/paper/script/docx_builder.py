"""Pengisi templat panitia ICC CDW 2026 (template/icc2026_template.docx) dari struktur konten di content.py.

Jangan edit teks paper di sini. Teks ada di content.py; file ini hanya tahu cara
menaruh blok (heading, paragraf, gambar, tabel, referensi) ke dalam templat.

Format tiap jenis blok DISALIN dari paragraf contoh di templat (pPr + ukuran huruf), bukan
ditulis ulang, supaya hasilnya sama persis dengan templat:
  judul 24pt tengah, nama tim 11pt miring, penulis 11pt + afiliasi miring bernomor superscript,
  abstrak/kata kunci tebal 9pt dengan label "Abstrak—", heading "I." kapital kecil tengah,
  subheading "A." miring, isi 10pt rata kiri-kanan, caption 9pt tengah ("Gambar 1.", "Tabel 1."),
  tabel 9pt berbingkai hitam dengan isian hijau muda, daftar pustaka 8pt "[1]".
Halaman Letter, margin kiri-kanan 0,65" dan atas-bawah 0,7", dua kolom 3,5" jarak 0,2"; banner "Innovation Case
Competition Campus Data Week 2026" hanya di halaman 1, nomor halaman kanan bawah.

Markup inline yang didukung di dalam string paragraf:
  **tebal**   *miring*   {cite:kunci1,kunci2}   {fig:kunci}   {tab:kunci}
"""
import copy
import re
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template" / "icc2026_template.docx"

# Letter 12240 twip - 2 x 936 margin; kolom templat 5040 twip, jarak 288
PAGE_W_PT = (12240 - 2 * 936) / 20
COL_W_PT = 5040 / 20
TABLE_FILL = "E2EFD9"          # isian sel tabel contoh templat (gaya "Table1")


class Registry:
    """Penomoran otomatis sitasi (urutan kemunculan), gambar, dan tabel."""

    def __init__(self, refs, figs, tabs, lbl_fig="Gambar", lbl_tab="Tabel"):
        self.lbl_fig, self.lbl_tab = lbl_fig, lbl_tab
        self.refs = refs              # dict kunci -> string referensi
        self.cite_order = []
        self.figs = figs              # daftar kunci gambar sesuai urutan di dokumen
        self.tabs = tabs

    def cite(self, keys):
        nums = []
        for k in keys:
            k = k.strip()
            if k not in self.refs:
                raise KeyError(f"referensi tidak dikenal: {k}")
            if k not in self.cite_order:
                self.cite_order.append(k)
            nums.append(self.cite_order.index(k) + 1)
        return ", ".join(f"[{n}]" for n in sorted(nums))

    def fig(self, k):
        return f"{self.lbl_fig} {self.figs.index(k) + 1}"

    def tab(self, k):
        # templat: "Table 1", angka Arab
        return f"{self.lbl_tab} {self.tabs.index(k) + 1}"


TOKEN = re.compile(r"(\*\*.+?\*\*|\*.+?\*|\{cite:[^}]+\}|\{fig:[^}]+\}|\{tab:[^}]+\})")


def add_runs(p, text, reg, base_bold=False, base_italic=False, size=None, small_caps=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        bold, italic = base_bold, base_italic
        if part.startswith("**"):
            part, bold = part[2:-2], True
        elif part.startswith("*") and not part.startswith("{"):
            part, italic = part[1:-1], True
        elif part.startswith("{cite:"):
            part = reg.cite(part[6:-1].split(","))
        elif part.startswith("{fig:"):
            part = reg.fig(part[5:-1])
        elif part.startswith("{tab:"):
            part = reg.tab(part[5:-1])
        r = p.add_run(part)
        if bold:
            r.bold = True
        if italic:
            r.italic = True
        if size:
            r.font.size = Pt(size)
        if small_caps:
            r.font.small_caps = True


def _run(p, text, size=None, bold=False, italic=False, sup=False):
    r = p.add_run(text)
    if size:
        r.font.size = Pt(size)
    if bold:
        r.bold = True
    if italic:
        r.italic = True
    if sup:
        r.font.superscript = True
    return r


class Builder:
    def __init__(self, meta, refs, figs, tabs):
        self.doc = docx.Document(TEMPLATE)
        self.lbl = dict(fig=meta.get("label_gambar", "Gambar"), tab=meta.get("label_tabel", "Tabel"),
                        pustaka=meta.get("label_pustaka", "Daftar Pustaka"))
        self.reg = Registry(refs, figs, tabs, self.lbl["fig"], self.lbl["tab"])
        self.meta = meta
        self.n_h1 = self.n_h2 = self.n_h3 = 0
        body = self.doc.element.body
        kids = list(body.iterchildren())
        # indeks elemen templat (lihat README bagian templat)
        title, team, authors, abstract, keywords = kids[0], kids[2], kids[3], kids[4], kids[8]
        self.sect_body = kids[-1]
        assert self.sect_body.tag == qn("w:sectPr") and authors.find(".//" + qn("w:sectPr")) is not None, \
            "struktur templat berubah; cek indeks elemen di docx_builder.Builder"
        # prototipe format tiap jenis blok, diambil dari paragraf contoh templat
        P = lambda i: copy.deepcopy(kids[i].find(qn("w:pPr")))
        self.proto = dict(h1=P(10), h2=P(18), body=P(13), fig=P(25), cap=P(30), tabcap=P(32),
                          eq=P(37), unh=P(44), ref=P(46))
        self.proto_tbl = copy.deepcopy(kids[33])
        # buang isi contoh (bookmark kosong + paragraf 10..akhir); sisakan paragraf kosong 5 dan 9 seperti templat
        for k in kids[6:8] + kids[10:-1]:
            body.remove(k)
        # nomor halaman: hanya section pertama yang memulai dari 1, section lain melanjutkan
        pg = self.sect_body.find(qn("w:pgNumType"))
        if pg is not None:
            self.sect_body.remove(pg)
        self._default_font()

        self._set_text(title, meta["judul"])
        self._set_text(team, meta.get("tim", ""))
        self._authors(authors, meta["penulis"])
        self._label_para(abstract, meta["label_abstrak"], meta["abstrak"])
        self._label_para(keywords, meta["label_kata_kunci"], meta["kata_kunci"])

    def _default_font(self):
        """Templat (ekspor Google Docs) mengandalkan bawaan Word: Times New Roman 10pt. Tulis eksplisit."""
        rpr = self.doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
        f = OxmlElement("w:rFonts")
        for a in ("ascii", "hAnsi", "cs", "eastAsia"):
            f.set(qn(f"w:{a}"), "Times New Roman")
        rpr.insert(0, f)
        for tag in ("w:sz", "w:szCs"):
            e = OxmlElement(tag); e.set(qn("w:val"), "20"); rpr.append(e)

    # ---------- bagian kepala ----------
    def _clear_runs(self, p_el):
        for r in p_el.findall(qn("w:r")):
            p_el.remove(r)
        return Paragraph(p_el, self.doc._body)

    def _set_text(self, p_el, text):
        """Ganti teks, pertahankan format run pertama templat."""
        runs = p_el.findall(qn("w:r"))
        rpr = runs[0].find(qn("w:rPr"))
        p = self._clear_runs(p_el)
        r = p.add_run(text)
        if rpr is not None:
            r._r.insert(0, copy.deepcopy(rpr))

    def _authors(self, p_el, penulis):
        """Satu paragraf seperti templat: 'Nama¹*, Nama¹' <br><br> '¹Afiliasi, Negara' per baris (11pt).
        Penulis pertama diberi asterisk sebagai corresponding author."""
        p = self._clear_runs(p_el)
        afil = []
        for a in penulis:
            s = ", ".join(x for x in (f"Program Studi {a['prodi']}" if a.get("prodi") else None,
                                      a.get("kampus"), a.get("kota")) if x)
            if s not in afil:
                afil.append(s)
        for i, a in enumerate(penulis):
            s = ", ".join(x for x in (f"Program Studi {a['prodi']}" if a.get("prodi") else None,
                                      a.get("kampus"), a.get("kota")) if x)
            _run(p, ("" if i == 0 else ", ") + a["nama"], 11)
            _run(p, str(afil.index(s) + 1) + ("*" if i == 0 else ""), 11, sup=True)
        r = _run(p, "", 11)
        r.add_break(); r.add_break()
        for j, s in enumerate(afil):
            _run(p, str(j + 1), 11, italic=True, sup=True)
            r = _run(p, s, 11, italic=True)
            if j < len(afil) - 1:
                r.add_break()

    def _label_para(self, p_el, label, text):
        """Abstrak/kata kunci persis templat: label tebal-miring + em dash tebal, isi tebal 9pt, diakhiri titik."""
        p = self._clear_runs(p_el)
        _run(p, label, 9, bold=True, italic=True)
        _run(p, "—", 9, bold=True)
        _run(p, " ")
        text = text.rstrip()
        add_runs(p, text if text.endswith(".") else text + ".", self.reg, base_bold=True, size=9)

    # ---------- badan ----------
    def _new_p(self, kind):
        p_el = OxmlElement("w:p")
        p_el.append(copy.deepcopy(self.proto[kind]))
        self.sect_body.addprevious(p_el)
        return Paragraph(p_el, self.doc._body)

    def h1(self, text):
        self.n_h1 += 1; self.n_h2 = 0
        add_runs(self._new_p("h1"), text, self.reg)

    def h2(self, text):
        self.n_h2 += 1; self.n_h3 = 0
        add_runs(self._new_p("h2"), text, self.reg)

    def h3(self, text):
        """Templat: 'A.1. Judul', gaya subheading tanpa penomoran otomatis."""
        self.n_h3 += 1
        p = self._new_p("h2")
        ppr = p._p.find(qn("w:pPr"))
        ppr.remove(ppr.find(qn("w:numPr")))
        add_runs(p, f"{chr(64 + self.n_h2)}.{self.n_h3}. {text}", self.reg)

    def para(self, text):
        add_runs(self._new_p("body"), text, self.reg)

    def bullet(self, text):
        p = self._new_p("body")
        pf = p.paragraph_format
        pf.first_line_indent = Pt(-8.5)
        pf.left_indent = Pt(14.2)
        pf.tab_stops.add_tab_stop(Pt(14.2))
        add_runs(p, "•\t" + text, self.reg)

    def equation(self, text, num):
        """Persamaan satu baris persis templat: tab tengah 2790 + nomor rata kanan 5040."""
        p = self._new_p("eq")
        p.add_run("\t" + text)
        p.add_run("\t(" + str(num) + ")")

    def figure(self, key, path, caption, full=False, height_pt=None):
        if full:
            self._section_break(cols=2)            # tutup section 2 kolom sebelum gambar lebar
        p = self._new_p("fig")
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Pt(PAGE_W_PT if full else COL_W_PT))
        cap = self._new_p("cap")
        cap.paragraph_format.space_after = Pt(8)
        add_runs(cap, f"{self.reg.fig(key)}. {caption}", self.reg, size=9)
        if full:
            self._section_break(cols=1)            # tutup section 1 kolom, lanjut 2 kolom

    def image(self, path):
        """Gambar selebar kolom tanpa caption bernomor (lampiran)."""
        p = self._new_p("fig")
        p.paragraph_format.space_before = Pt(6)
        p.add_run().add_picture(str(path), width=Pt(COL_W_PT))

    def _section_break(self, cols):
        """Paragraf kecil pembawa sectPr kontinu. Salinan sectPr badan templat (header halaman 2+ kosong)."""
        p = self._new_p("body")
        pf = p.paragraph_format
        pf.space_after = pf.space_before = Pt(0)
        pf.first_line_indent = Pt(0)
        ppr = p._p.find(qn("w:pPr"))
        rpr = ppr.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr"); ppr.append(rpr)
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); rpr.append(sz)
        s = copy.deepcopy(self.sect_body)
        if cols == 1:
            c = s.find(qn("w:cols"))
            for ch in list(c):
                c.remove(ch)
            for a in list(c.attrib):
                del c.attrib[a]
            c.set(qn("w:space"), "720")
        ppr.append(s)

    def table(self, key, caption, header, rows, widths_pt, full=False, font_pt=9, align=None):
        if full:
            self._section_break(cols=2)
        cap = self._new_p("tabcap")
        cap.paragraph_format.space_before = Pt(6)
        cap.paragraph_format.keep_with_next = True
        add_runs(cap, f"{self.reg.tab(key)}. {caption}", self.reg, size=9)
        t = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        self.sect_body.addprevious(t._tbl)
        self._style_table(t, widths_pt)
        for i, row in enumerate([header] + rows):
            for j, val in enumerate(row):
                c = t.cell(i, j)
                c.width = Pt(widths_pt[j])
                self._cell_fmt(c)
                p = c.paragraphs[0]
                a = (align or "l" + "c" * (len(header) - 1))[j]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (i == 0 or a == "c") else WD_ALIGN_PARAGRAPH.LEFT
                add_runs(p, str(val), self.reg, base_bold=(i == 0), size=font_pt)
        # baris header diulang, baris tidak dipecah antar-halaman
        # keep_with_next hanya pada header + baris pertama: caption tidak terpisah dari tabelnya, tetapi
        # tabel panjang boleh berlanjut ke kolom berikutnya (tidak menyisakan ruang kosong)
        for k, r in enumerate(t.rows):
            trpr = r._tr.get_or_add_trPr()
            trpr.append(OxmlElement("w:cantSplit"))
            if k == 0:
                trpr.append(OxmlElement("w:tblHeader"))
            if k < (len(t.rows) - 1 if full else min(2, len(t.rows) - 1)):   # tabel lebar tetap utuh
                for c in r.cells:
                    for p in c.paragraphs:
                        p.paragraph_format.keep_with_next = True
        # jarak setelah tabel
        sp = self._new_p("cap"); sp.paragraph_format.space_after = Pt(4)
        if full:
            self._section_break(cols=1)

    def _style_table(self, t, widths_pt):
        """tblPr disalin dari tabel contoh templat (gaya Table1, margin sel 115 twip), lebar & grid eksplisit.
        Word membaca tcW, Google Docs membaca tblGrid; keduanya diisi supaya tidak meluber."""
        tbl = t._tbl
        tblpr = copy.deepcopy(self.proto_tbl.find(qn("w:tblPr")))
        tbl.replace(tbl.tblPr, tblpr)
        tw = [int(round(w * 20)) for w in widths_pt]
        tblpr.find(qn("w:tblW")).set(qn("w:w"), str(sum(tw)))
        tblpr.find(qn("w:jc")).set(qn("w:val"), "center")
        ind = tblpr.find(qn("w:tblInd"))
        if ind is not None:
            tblpr.remove(ind)
        for g, w in zip(tbl.tblGrid.findall(qn("w:gridCol")), tw):
            g.set(qn("w:w"), str(w))
        # margin sel templat (115 twip kiri/kanan) terlalu lebar untuk tabel berisi teks di kolom 3,5";
        # kolom sempit seperti "KC" pecah per huruf. Dikecilkan jadi 57 twip, atas/bawah tetap 0.
        mar = OxmlElement("w:tblCellMar")
        for side, v in (("top", 0), ("left", 57), ("bottom", 0), ("right", 57)):
            e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); mar.append(e)
        tblpr.find(qn("w:tblLayout")).addnext(mar)

    @staticmethod
    def _cell_fmt(cell):
        """Bingkai hitam 4 sisi + isian hijau muda, seperti sel contoh templat."""
        tcpr = cell._tc.get_or_add_tcPr()
        b = OxmlElement("w:tcBorders")
        for side in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{side}")
            for k, v in (("val", "single"), ("sz", "4"), ("space", "0"), ("color", "000000")):
                e.set(qn(f"w:{k}"), v)
            b.append(e)
        tcpr.append(b)
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), TABLE_FILL)
        tcpr.append(sh)

    def unnumbered(self, text):
        """Judul tanpa nomor (Lampiran), gaya sama dengan judul Daftar Pustaka."""
        add_runs(self._new_p("unh"), text, self.reg, small_caps=True)

    def references(self):
        p = self._new_p("unh")
        add_runs(p, self.lbl["pustaka"], self.reg, small_caps=True)
        for i, k in enumerate(self.reg.cite_order, 1):
            add_runs(self._new_p("ref"), f"[{i}]\t" + self.reg.refs[k], self.reg, size=8)
        unused = set(self.reg.refs) - set(self.reg.cite_order)
        if unused:
            print("  [peringatan] referensi tidak disitasi:", ", ".join(sorted(unused)))

    def save(self, path):
        self.doc.save(path)
