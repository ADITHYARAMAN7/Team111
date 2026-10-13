"""finalize.py - replace equation placeholders in draft.docx with native OMML
(Office Math) and write the final Word file."""
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "draft.docx")
OUT = os.path.join(HERE, "..", sys.argv[1] if len(sys.argv) > 1 else "Tomato_Doctor_IEEE.docx")
M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'

doc = json.load(open(os.path.join(HERE, "paper.json"), encoding="utf-8"))
eqs = {b["num"]: b["omml"] for b in doc["blocks"] if b["type"] == "equation"}

with zipfile.ZipFile(SRC) as z:
    files = {n: z.read(n) for n in z.namelist()}
xml = files["word/document.xml"].decode("utf-8")
if "xmlns:m=" not in xml[:3000]:
    xml = xml.replace("<w:document ", f"<w:document {M_NS} ", 1)

done = 0
for num, omml in eqs.items():
    pat = re.compile(r"<w:r>(?:(?!</w:r>).)*?@@EQ" + re.escape(num) + r"@@</w:t></w:r>", re.S)
    xml, n = pat.subn(lambda _: f"<m:oMathPara><m:oMath>{omml}</m:oMath></m:oMathPara>", xml)
    if n != 1:
        sys.exit(f"equation {num}: {n} placeholders replaced")
    done += n
assert "@@EQ" not in xml
files["word/document.xml"] = xml.encode("utf-8")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in files.items():
        z.writestr(name, data)
print(f"replaced {done} equations -> {os.path.abspath(OUT)}")
