# Embed the template's fonts (EOT .fntdata) into a pptxgenjs deck
import sys, zipfile, re, shutil, os
src, fontdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
FONTS = [("Rustic Printed Stamp","font16","00000000000000000000"),("Poppins Bold","font17","00000800000000000000"),
         ("Poppins","font18","00000500000000000000"),("Gloria Hallelujah","font19","02000000000000000000"),
         ("Poppins Light","font20","00000400000000000000")]
zin = zipfile.ZipFile(src); tmp = out + ".tmp"
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == "[Content_Types].xml":
        t = data.decode("utf8")
        if 'Extension="fntdata"' not in t:
            t = t.replace("<Default ", '<Default Extension="fntdata" ContentType="application/x-fontdata"/><Default ', 1)
        data = t.encode("utf8")
    elif item.filename == "ppt/_rels/presentation.xml.rels":
        t = data.decode("utf8")
        add = "".join(f'<Relationship Id="rIdFont{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/font" Target="fonts/{f}.fntdata"/>' for i,(n,f,p) in enumerate(FONTS))
        t = t.replace("</Relationships>", add + "</Relationships>"); data = t.encode("utf8")
    elif item.filename == "ppt/presentation.xml":
        t = data.decode("utf8")
        lst = "<p:embeddedFontLst>" + "".join(f'<p:embeddedFont><p:font typeface="{n}" charset="1" panose="{p}"/><p:regular r:id="rIdFont{i}"/></p:embeddedFont>' for i,(n,f,p) in enumerate(FONTS)) + "</p:embeddedFontLst>"
        t = re.sub(r"(<p:notesSz[^>]*/>)", r"\1" + lst, t, 1)
        t = t.replace("<p:presentation ", '<p:presentation embedTrueTypeFonts="1" ', 1)
        data = t.encode("utf8")
    zout.writestr(item, data)
for n,f,p in FONTS:
    zout.write(os.path.join(fontdir, f + ".fntdata"), f"ppt/fonts/{f}.fntdata")
zout.close(); shutil.move(tmp, out); print("embedded ->", out)
