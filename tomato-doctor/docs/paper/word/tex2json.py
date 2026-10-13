"""
tex2json.py - converts docs/paper/main.tex into a structured JSON document
(blocks + styled runs) that build_docx.js turns into an IEEE-format .docx.
It reads the LaTeX source itself so the Word text is identical to the PDF.
Display equations are emitted as OMML (Office Math) for native, editable
Word equations.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "..", "main.tex")

src = open(TEX, encoding="utf-8").read()


def strip_comments(s):
    out = []
    for line in s.split("\n"):
        m = re.search(r"(?<!\\)%", line)
        out.append(line[: m.start()] if m else line)
    return "\n".join(out)


src = strip_comments(src)

# ------------------------------------------------------------------ numbering (same order as LaTeX)
bib_keys = re.findall(r"\\bibitem\{([^}]+)\}", src)
CITE = {k: i + 1 for i, k in enumerate(bib_keys)}

body_all = src[src.index("\\maketitle"): src.index("\\begin{thebibliography}")]
LABELS = {}
sec_n = sub_n = fig_n = tab_n = eq_n = alg_n = 0
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV"]
for m in re.finditer(r"\\section\{|\\subsection\{|\\begin\{(figure\*?|table|equation|align|algorithm)\}|\\label\{([^}]+)\}|\\\\(?=\s*\n?\s*P\(e\^\{-)", body_all):
    tok = m.group(0)
    if tok == "\\section{":
        sec_n += 1
        sub_n = 0
        last = ("sec", ROMAN[sec_n - 1])
    elif tok == "\\subsection{":
        sub_n += 1
        last = ("sub", f"{ROMAN[sec_n - 1]}-{chr(64 + sub_n)}")
    elif m.group(1):
        env = m.group(1)
        if env.startswith("figure"):
            fig_n += 1
            last = ("fig", str(fig_n))
        elif env == "table":
            tab_n += 1
            last = ("tab", ROMAN[tab_n - 1])
        elif env in ("equation", "align"):
            eq_n += 1
            last = ("eq", str(eq_n))
        elif env == "algorithm":
            alg_n += 1
            last = ("alg", str(alg_n))
    elif tok.startswith("\\\\"):        # second line of the align environment
        eq_n += 1
        last = ("eq", str(eq_n))
    elif m.group(2):
        lab = m.group(2)
        kind, num = last
        if kind == "sub":
            num = num.split("-")[0] if lab.startswith("sec:") else num
        LABELS[lab] = num

# ------------------------------------------------------------------ inline conversion
GREEK = {"alpha": "α", "beta": "β", "theta": "θ", "lambda": "λ", "tau": "τ", "pi": "π", "sigma": "σ", "kappa": "κ",
         "omega": "ω", "mu": "μ", "Delta": "Δ", "delta": "δ", "gamma": "γ", "epsilon": "ε", "rho": "ρ", "phi": "φ"}
MSYM = {"geq": "≥", "leq": "≤", "ge": "≥", "le": "≤", "times": "×", "to": "→", "rightarrow": "→", "mid": "|",
        "propto": "∝", "in": "∈", "notin": "∉", "neg": "¬", "cdot": "·", "pm": "±", "approx": "≈", "sum": "∑",
        "prod": "∏", "infty": "∞", "ldots": "…", "dots": "…", "star": "⋆", "dagger": "†", "ddagger": "‡",
        "emptyset": "∅", "cup": "∪", "Rightarrow": "⇒", "gets": "←", "circ": "°", "prime": "′", "lbrace": "{", "rbrace": "}",
        "bigl": "", "bigr": "", "left": "", "right": "", "quad": " ", "qquad": "  ", ",": "\u2009", ";": " ",
        "!": "", " ": " ", "{": "{", "}": "}", "%": "%", "_": "_"}
UPRIGHT_FUN = {"max", "min", "arg", "log", "ln", "exp", "clip"}
RELS = set("=<>≤≥∈∉∝→⇒≈←")


def read_group(s, i):
    """s[i] == '{' -> (content, index after closing brace)."""
    assert s[i] == "{", s[i:i + 30]
    depth, j = 0, i
    while j < len(s):
        if s[j] == "\\":
            j += 2
            continue
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced: " + s[i:i + 60])


def run(t, **st):
    r = {"t": t}
    r.update({k: v for k, v in st.items() if v})
    return r


def cite_text(keys):
    nums = sorted(CITE[k.strip()] for k in keys.split(","))
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            parts.append(f"[{nums[i]}]–[{nums[j]}]")
        else:
            parts += [f"[{n}]" for n in nums[i:j + 1]]
        i = j + 1
    return ", ".join(parts)


def math_runs(m, st):
    """TeX math (inline) -> styled runs (italic variables, upright operators)."""
    out = []

    def emit(t, **k):
        s2 = dict(st)
        s2.update(k)
        out.append(run(t, **s2))

    i = 0
    while i < len(m):
        c = m[i]
        if c in " \n\t":
            i += 1
            continue
        if c in "^_":
            i += 1
            while m[i] == " ":
                i += 1
            if m[i] == "{":
                g, i = read_group(m, i)
            elif m[i] == "\\":
                mm = re.match(r"\\([A-Za-z]+|.)", m[i:])
                g, i = mm.group(0), i + len(mm.group(0))
            else:
                g, i = m[i], i + 1
            key = "sup" if c == "^" else "sub"
            if g.strip() == "\\circ":
                emit("°", i_=False)
                continue
            for r in math_runs(g, {**st, key: True}):
                out.append(r)
            continue
        if c == "\\":
            mm = re.match(r"\\([A-Za-z]+|.)", m[i:])
            name = mm.group(1)
            i += len(mm.group(0))
            if name in ("mathrm", "text", "textsf", "operatorname", "mathsf", "textrm"):
                g, i = read_group(m, i)
                rs = inline_runs(g, {**st, "i": False})
                if rs and g[:1] == " ":
                    rs[0]["t"] = " " + rs[0]["t"]
                if rs and g[-1:] == " ":
                    rs[-1]["t"] += " "
                out += rs
            elif name in ("textsc",):
                g, i = read_group(m, i)
                emit(g, sc=True, i=False)
            elif name == "unk":
                emit("unknown", sc=True, i=False)
            elif name == "EIG":
                emit((" " if out and (out[-1].get("sub") or out[-1].get("sup")) else "") + "EIG", i=False)
            elif name == "mathcal":
                g, i = read_group(m, i)
                emit({"H": "ℋ", "E": "ℰ"}.get(g, g), i=False)
            elif name == "bar":
                g, i = read_group(m, i) if m[i] == "{" else (m[i + 1], i + 2) if m[i] == " " else (m[i], i + 1)
                emit(g.strip() + "\u0304", i=True)
            elif name in GREEK:
                emit(GREEK[name], i=True)
            elif name in UPRIGHT_FUN:
                emit(name + (" " if name in ("log", "ln", "arg") else ""), i=False)
            elif name == "frac":
                a, i = read_group(m, i)
                b, i = read_group(m, i)
                emit("(", i=False)
                out.extend(math_runs(a, st))
                emit(")/(", i=False)
                out.extend(math_runs(b, st))
                emit(")", i=False)
            elif name in MSYM:
                sym = MSYM[name]
                if sym in RELS:
                    emit(sym if (st.get("sub") or st.get("sup")) else f" {sym} ", i=False)
                elif sym:
                    emit(sym, i=False)
            elif name in ("label",):
                _, i = read_group(m, i)
            else:
                print("WARN math cmd", name, file=sys.stderr)
            continue
        if c in "{}":
            i += 1
            continue
        if c.isalpha():
            emit(c, i=True)
        elif c in "=<>":
            emit(f" {c} ", i=False)
        elif c == "," and not (st.get("sup") or st.get("sub")):
            emit(", ", i=False)
        elif c in "+-":
            prev = "".join(r["t"] for r in out).rstrip()
            sym = "−" if c == "-" else "+"
            if not prev or prev[-1] in "([{,=" or st.get("sup") or st.get("sub"):
                emit(sym, i=False)
            else:
                emit(f" {sym} ", i=False)
        else:
            emit(c, i=False)
        i += 1
    # merge adjacent runs with identical style
    merged = []
    for r in out:
        if merged and {k: v for k, v in merged[-1].items() if k != "t"} == {k: v for k, v in r.items() if k != "t"}:
            merged[-1]["t"] += r["t"]
        else:
            merged.append(r)
    return merged


ACCENTS = {("'", "e"): "é", ('"', "a"): "ä", ('"', "o"): "ö", ("'", "a"): "á"}


def inline_runs(s, st=None):
    st = dict(st or {})
    out = []
    i = 0
    buf = ""

    def flush():
        nonlocal buf
        if buf:
            out.append(run(buf, **st))
            buf = ""

    while i < len(s):
        c = s[i]
        if c == "\\":
            mm = re.match(r"\\([A-Za-z]+|.)", s[i:])
            name = mm.group(1)
            i += len(mm.group(0))
            if name in ("emph", "textit", "textbf", "textsc", "textsf", "texttt", "ta", "mbox", "url", "textrm", "textup"):
                g, i = read_group(s, i)
                flush()
                key = {"emph": "i", "textit": "i", "textbf": "b", "textsc": "sc", "textsf": "sf", "texttt": "tt",
                       "ta": "ta", "url": "tt"}.get(name)
                if name == "mbox":
                    g = g.replace("-", "\u2011")
                if name == "url":
                    out.append(run(g, **{**st, "tt": True, "url": True}))
                else:
                    out += inline_runs(g, {**st, key: True} if key else st)
            elif name == "cite":
                g, i = read_group(s, i)
                buf += cite_text(g)
            elif name in ("ref", "eqref"):
                g, i = read_group(s, i)
                n = LABELS.get(g, "??")
                buf += f"({n})" if name == "eqref" else n
            elif name == "label":
                _, i = read_group(s, i)
            elif name == "unk":
                flush()
                out.append(run("unknown", **{**st, "sc": True}))
            elif name == "EIG":
                buf += "EIG"
            elif name in ("'", '"'):
                if s[i] == "{":
                    g, i = read_group(s, i)
                else:
                    g, i = s[i], i + 1
                buf += ACCENTS.get((name, g), g)
            elif name in ("%", "&", "_", "#", "$", "{", "}"):
                buf += name
            elif name == ",":
                buf += "\u2009"
            elif name in (" ", "\n"):
                buf += " "
            elif name == "\\":
                buf += " "
            elif name == "IEEEauthorrefmark":
                g, i = read_group(s, i)
                buf += {"1": "*", "2": "†"}.get(g, "")
            elif name == "quad":
                buf += " "
            elif name in ("hfill", "noindent", "centering", "small", "footnotesize", "scriptsize", "normalsize"):
                pass
            else:
                print("WARN text cmd", name, s[i - 20:i + 20].replace("\n", " "), file=sys.stderr)
            continue
        if c == "$":
            j = s.index("$", i + 1)
            flush()
            out += math_runs(s[i + 1:j], {**st, "math": True})
            i = j + 1
            continue
        if c == "~":
            buf += "\u00a0"
        elif s.startswith("---", i):
            buf += "—"
            i += 2
        elif s.startswith("--", i):
            buf += "–"
            i += 1
        elif s.startswith("``", i):
            buf += "“"
            i += 1
        elif s.startswith("''", i):
            buf += "”"
            i += 1
        elif c == "`":
            buf += "‘"
        elif c == "'":
            buf += "’"
        elif c in "{}":
            pass
        elif c in "\n\t":
            buf += " "
        else:
            buf += c
        i += 1
    flush()
    # collapse whitespace across runs
    res = []
    for r in out:
        r["t"] = re.sub(r"[ ]{2,}", " ", r["t"])
        if res and res[-1]["t"].endswith(" ") and r["t"].startswith(" "):
            r["t"] = r["t"][1:]
        if r["t"]:
            res.append(r)
    if res:
        res[0]["t"] = res[0]["t"].lstrip()
        res[-1]["t"] = res[-1]["t"].rstrip()
    return [r for r in res if r["t"]]


# ------------------------------------------------------------------ OMML for display equations
def x(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def m_r(t, upright=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if upright else ""
    return f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{x(t)}</m:t></m:r>'


def omml(m):
    """Small TeX -> OMML converter for the paper's display equations."""
    toks = tokenize(m)
    xml, _ = omml_seq(toks, 0, stop=None)
    return xml


def tokenize(m):
    toks, i = [], 0
    while i < len(m):
        c = m[i]
        if c in " \n\t":
            i += 1
            continue
        if c == "&":
            toks.append(("cmd", "quad"))
            i += 1
            continue
        if c == "\\":
            mm = re.match(r"\\([A-Za-z]+|.)", m[i:])
            name = mm.group(1)
            i += len(mm.group(0))
            if name in ("begin", "end"):
                g, i = read_group(m, i)
                toks.append(("env_" + name, g))
            elif name in ("mathrm", "text", "frac", "bar", "mathcal"):
                toks.append(("cmd", name))
            else:
                toks.append(("cmd", name))
            continue
        if c == "{":
            g, i = read_group(m, i)
            toks.append(("grp", g))
            continue
        toks.append(("ch", c))
        i += 1
    return toks


def atom_xml(toks, k):
    """One atom starting at toks[k] -> (xml, next k)."""
    kind, v = toks[k]
    if kind == "grp":
        return omml(v), k + 1
    if kind == "amp":
        return m_r("&", True) + m_r("\u2002", True), k + 1
    if kind == "ch":
        if v.isalpha():
            return m_r(v), k + 1
        if v == "-":
            return m_r("−", True), k + 1
        return m_r(v, True), k + 1
    if kind == "cmd":
        if v in ("mathrm", "text"):
            g = toks[k + 1][1]
            txt = re.sub(r"\\textsc\{([^}]*)\}", lambda mm: mm.group(1).upper(), g)
            txt = txt.replace("\\,", " ").replace("\\ ", " ").replace("~", " ").replace("'", "’")
            return m_r(txt, True), k + 2
        if v == "frac":
            num = omml(toks[k + 1][1])
            den = omml(toks[k + 2][1])
            return f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>", k + 3
        if v == "bar":
            e = omml(toks[k + 1][1]) if toks[k + 1][0] == "grp" else m_r(toks[k + 1][1])
            return f'<m:acc><m:accPr><m:chr m:val="&#772;"/></m:accPr><m:e>{e}</m:e></m:acc>', k + 2
        if v in GREEK:
            return m_r(GREEK[v]), k + 1
        if v == "EIG":
            return m_r("EIG", True), k + 1
        if v in UPRIGHT_FUN:
            return m_r(v, True), k + 1
        if v == "quad":
            return m_r("\u2003\u2003", True), k + 1
        if v in (",", ";", "!", "bigl", "bigr", "left", "right", "label"):
            return "", k + 1
        if v in MSYM:
            return m_r(MSYM[v], True), k + 1
        print("WARN omml cmd", v, file=sys.stderr)
        return "", k + 1
    return "", k + 1


def omml_seq(toks, k, stop):
    xml = ""
    while k < len(toks):
        kind, v = toks[k]
        if kind == "cmd" and v == "label":
            k += 2
            continue
        if kind == "env_begin" and v == "cases":
            rows, k = cases_rows(toks, k + 1)
            row_xml = "".join(f"<m:e>{r}</m:e>" for r in rows)
            xml += f'<m:d><m:dPr><m:begChr m:val="{{"/><m:endChr m:val=""/></m:dPr><m:e><m:eqArr>{row_xml}</m:eqArr></m:e></m:d>'
            continue
        if kind == "cmd" and v in ("sum", "prod"):
            chr_ = "∑" if v == "sum" else "∏"
            k += 1
            sub = ""
            if k < len(toks) and toks[k] == ("ch", "_"):
                sub = omml(toks[k + 1][1]) if toks[k + 1][0] == "grp" else atom_xml(toks, k + 1)[0]
                k += 2
            # operand: following atoms up to a top-level relation, '+', '-', ',' or '.'
            j = k
            while j < len(toks) and not (toks[j][0] == "ch" and toks[j][1] in "=+-,.") and toks[j][0] != "env_end":
                j += 1
            e, _ = omml_seq(toks[k:j], 0, None)
            xml += (f'<m:nary><m:naryPr><m:chr m:val="{chr_}"/><m:limLoc m:val="undOvr"/><m:supHide m:val="1"/></m:naryPr>'
                    f"<m:sub>{sub}</m:sub><m:sup/><m:e>{e}</m:e></m:nary>")
            k = j
            continue
        base, k2 = atom_xml(toks, k)
        sub = sup = None
        while k2 < len(toks) and toks[k2] in (("ch", "_"), ("ch", "^")):
            arg = omml(toks[k2 + 1][1]) if toks[k2 + 1][0] == "grp" else atom_xml(toks, k2 + 1)[0]
            if toks[k2][1] == "_":
                sub = arg
            else:
                sup = arg
            k2 += 2
        if sub is not None and sup is not None:
            xml += f"<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>"
        elif sub is not None:
            xml += f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"
        elif sup is not None:
            xml += f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"
        else:
            xml += base
        k = k2
    return xml, k


def cases_rows(toks, k):
    rows, cur = [], []
    while toks[k] != ("env_end", "cases"):
        if toks[k] == ("cmd", "\\"):
            rows.append(cur)
            cur = []
        else:
            cur.append(("amp", "&") if toks[k] == ("cmd", "quad") else toks[k])
        k += 1
    rows.append(cur)
    out = []
    for r in rows:
        if not r:
            continue
        xml, _ = omml_seq(r, 0, None)
        out.append(xml)
    return out, k + 1


# ------------------------------------------------------------------ block parsing
def paragraphs(text):
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if para:
            out.append({"type": "p", "runs": inline_runs(para)})
    return out


def parse_tabular(env_body):
    spec, rest = re.match(r"\s*\\begin\{tabular\}\{(.*?)\}\n(.*)\\end\{tabular\}", env_body, re.S).groups()
    rest = rest.replace("\\toprule", "@@TOP@@").replace("\\midrule", "@@MID@@").replace("\\bottomrule", "@@BOT@@")
    rows, rule_after_header, mid_rows = [], None, []
    for raw in re.split(r"\\\\", rest):
        cell_src = raw.strip()
        flags = re.findall(r"@@(TOP|MID|BOT)@@", cell_src)
        cell_src = re.sub(r"@@(TOP|MID|BOT)@@", "", cell_src).strip()
        if "MID" in flags:
            mid_rows.append(len(rows))
        if not cell_src:
            continue
        mc = re.match(r"\\multicolumn\{(\d+)\}\{.*?\}\{(.*)\}\s*$", cell_src, re.S)
        if mc:
            rows.append({"note": True, "cells": [inline_runs(mc.group(2).replace("\\scriptsize", ""))]})
            continue
        cells = re.split(r"(?<!\\)&", cell_src)
        rows.append({"cells": [inline_runs(c.strip()) for c in cells]})
    aligns = []
    for m in re.finditer(r">\{[^}]*\}p\{[^}]*\}|p\{[^}]*\}|[lcr]", spec):
        t = m.group(0)
        aligns.append("left" if t.startswith((">", "p", "l")) else {"c": "center", "r": "right"}[t])
    return {"aligns": aligns, "rows": rows, "mid_rows": mid_rows}


def parse_algorithm(body):
    cap = re.search(r"\\caption\{(.*?)\}\n", body).group(1)
    alg = body[body.index("\\begin{algorithmic}"): body.index("\\end{algorithmic}")]
    alg = alg.split("\n", 1)[1]
    lines, level, n = [], 0, 0
    # tokenise into commands
    pat = re.compile(r"\\(Require|Ensure|State|If|EndIf|For|EndFor|Return|Comment)")
    pieces, pos = [], 0
    for m in pat.finditer(alg):
        if m.start() > pos:
            pieces.append(("text", alg[pos:m.start()]))
        name = m.group(1)
        pos = m.end()
        if name in ("If", "For", "Comment"):
            g, pos = read_group(alg, pos)
            pieces.append((name, g))
        else:
            pieces.append((name, None))
    if pos < len(alg):
        pieces.append(("text", alg[pos:]))
    cur = None

    def new_line(runs, numbered=True, lvl=None):
        nonlocal n
        if numbered:
            n += 1
        lines.append({"n": n if numbered else None, "level": level if lvl is None else lvl, "runs": runs, "comment": None})
        return lines[-1]

    for kind, val in pieces:
        if kind == "Require":
            cur = new_line([run("Input: ", b=True)], False, 0)
        elif kind == "Ensure":
            cur = new_line([run("Output: ", b=True)], False, 0)
        elif kind == "State":
            cur = new_line([])
        elif kind == "Return":
            if cur is None or cur["runs"]:
                cur = new_line([])
            cur["runs"].append(run("return ", b=True))
        elif kind == "If":
            cur = new_line([run("if ", b=True)] + inline_runs(val) + [run(" then", b=True)])
            level += 1
        elif kind == "For":
            cur = new_line([run("for ", b=True)] + inline_runs(val) + [run(" do", b=True)])
            level += 1
        elif kind in ("EndIf", "EndFor"):
            level -= 1
            cur = new_line([run("end if" if kind == "EndIf" else "end for", b=True)])
            cur = None
        elif kind == "Comment":
            cur["comment"] = inline_runs(val)
        elif kind == "text":
            t = val.strip()
            if not t:
                continue
            rs = inline_runs(t)
            if cur is not None and cur["runs"] and cur["runs"][-1]["t"].endswith("then") and level > 0:
                # inline body after "then" (e.g. "then break") belongs to the if-line
                cur["runs"].append(run(" "))
                cur["runs"] += rs
                level -= 1
                cur["inline_then"] = True
                level += 1
            elif cur is not None:
                if cur["runs"] and not cur["runs"][-1]["t"].endswith(" "):
                    cur["runs"].append(run(" "))
                cur["runs"] += rs
    return {"caption": inline_runs(cap), "lines": lines}


def parse_figure(body, wide):
    cap = re.search(r"\\caption\{", body)
    cap_txt, _ = read_group(body, cap.end() - 1)
    label = re.search(r"\\label\{([^}]+)\}", body).group(1)
    items = []
    for m in re.finditer(r"\\subfloat\[|\\includegraphics(\[[^\]]*\])?\{([^}]+)\}|\\input\{([^}]+)\}", body):
        if m.group(0).startswith("\\subfloat["):
            j = body.index("]", m.end())
            # find matching ] for nested brackets
            depth, j = 1, m.end()
            while depth:
                if body[j] == "[":
                    depth += 1
                elif body[j] == "]":
                    depth -= 1
                j += 1
            items.append({"subcaption": inline_runs(body[m.end():j - 1])})
        elif m.group(2):
            path = m.group(2)
            name = os.path.splitext(os.path.basename(path))[0]
            img = f"assets/{name}.png" if path.endswith(".pdf") else "../" + path
            if items and "img" not in items[-1]:
                items[-1]["img"] = img
            else:
                items.append({"img": img})
        elif m.group(3):
            name = os.path.splitext(os.path.basename(m.group(3)))[0]
            items.append({"img": f"assets/{name}.png"})
    layout = "row" if wide and len(items) > 1 else "stack"
    return {"type": "figure", "wide": wide, "number": LABELS[label], "caption": inline_runs(cap_txt), "items": items, "layout": layout}


def parse_body(text):
    blocks = []
    pat = re.compile(r"\\section\*?\{|\\subsection\{|\\begin\{(abstract|IEEEkeywords|enumerate|itemize|equation|align|figure\*?|table|algorithm)\}")
    pos = 0
    sec_i = sub_i = 0
    while True:
        m = pat.search(text, pos)
        blocks += paragraphs(text[pos: m.start()] if m else text[pos:])
        if not m:
            break
        tok = m.group(0)
        if tok.startswith("\\section"):
            g, pos = read_group(text, m.end() - 1)
            if tok == "\\section*{":
                blocks.append({"type": "h1", "num": None, "runs": inline_runs(g)})
            else:
                sec_i += 1
                sub_i = 0
                blocks.append({"type": "h1", "num": ROMAN[sec_i - 1], "runs": inline_runs(g)})
            lm = re.match(r"\s*\\label\{[^}]+\}", text[pos:])
            if lm:
                pos += lm.end()
            continue
        if tok == "\\subsection{":
            g, pos = read_group(text, m.end() - 1)
            sub_i += 1
            blocks.append({"type": "h2", "num": chr(64 + sub_i), "runs": inline_runs(g)})
            continue
        env = m.group(1)
        end_tok = f"\\end{{{env}}}"
        end = text.index(end_tok, m.end())
        body = text[m.end(): end]
        pos = end + len(end_tok)
        if env == "abstract":
            blocks.append({"type": "abstract", "runs": inline_runs(body.strip())})
        elif env == "IEEEkeywords":
            blocks.append({"type": "keywords", "runs": inline_runs(body.strip())})
        elif env in ("enumerate", "itemize"):
            items = [it.strip() for it in re.split(r"\\item\s", body) if it.strip()]
            blocks.append({"type": "list", "ordered": env == "enumerate", "items": [inline_runs(it) for it in items]})
        elif env == "equation":
            lab = re.search(r"\\label\{([^}]+)\}", body)
            num = LABELS[lab.group(1)] if lab else None
            if num is None:   # unlabelled numbered equation: count it
                num = str(sum(1 for b in blocks if b["type"] == "equation") + 1)
            xml = omml(re.sub(r"\\label\{[^}]+\}", "", body).strip())
            if "<m:eqArr>" in xml:   # wide two-case equation: 9 pt so it fits one column line
                xml = xml.replace('<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>',
                                  '<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/><w:sz w:val="18"/><w:szCs w:val="18"/>')
            blocks.append({"type": "equation", "num": num, "omml": xml})
        elif env == "align":
            for line in re.split(r"\\\\", body):
                lab = re.search(r"\\label\{([^}]+)\}", line)
                blocks.append({"type": "equation", "num": LABELS[lab.group(1)],
                               "omml": omml(re.sub(r"\\label\{[^}]+\}", "", line).replace("&", "").strip())})
        elif env in ("figure", "figure*"):
            blocks.append(parse_figure(body, env == "figure*"))
        elif env == "table":
            cap_txt, _ = read_group(body, re.search(r"\\caption\{", body).end() - 1)
            label = re.search(r"\\label\{([^}]+)\}", body).group(1)
            tab = parse_tabular(body[body.index("\\begin{tabular}"):body.index("\\end{tabular}") + len("\\end{tabular}")])
            blocks.append({"type": "table", "number": LABELS[label], "caption": inline_runs(cap_txt), **tab})
        elif env == "algorithm":
            blocks.append({"type": "algorithm", "number": "1", **parse_algorithm(body)})
    # renumber equations sequentially in reading order (matches LaTeX)
    k = 0
    for b in blocks:
        if b["type"] == "equation":
            k += 1
            b["num"] = str(k)
    return blocks


title = re.search(r"\\title\{(.*?)\}\n", src, re.S).group(1)
body = src[src.index("\\maketitle") + len("\\maketitle"): src.index("\\begin{thebibliography}")]
blocks = parse_body(body)
bib = src[src.index("\\begin{thebibliography}"): src.index("\\end{thebibliography}")]
refs = []
for m in re.finditer(r"\\bibitem\{([^}]+)\}\s*(.*?)(?=\\bibitem|\Z)", bib, re.S):
    refs.append({"n": CITE[m.group(1)], "runs": inline_runs(m.group(2).strip())})

doc = {"title": inline_runs(title), "blocks": blocks, "refs": refs, "labels": LABELS}
with open(os.path.join(HERE, "paper.json"), "w", encoding="utf-8") as f:
    json.dump(doc, f, ensure_ascii=False, indent=1)
print(f"{len(blocks)} blocks, {len(refs)} references, "
      f"{sum(1 for b in blocks if b['type'] == 'equation')} equations, "
      f"{sum(1 for b in blocks if b['type'] == 'figure')} figures, {sum(1 for b in blocks if b['type'] == 'table')} tables")
