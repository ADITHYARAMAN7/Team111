"""
nlu.py - turns a farmer's free-text description (Tamil / English / Tanglish)
into symptom evidence, using the LayTerm layer of the knowledge graph.

Pipeline
  1. normalise + split into clauses (punctuation, "but"/"ஆனா")
  2. tokenise; map tokens to language-independent concepts (lexicon.py),
     multi-word forms first, then Tamil stem / English exact matching, then a
     typo-tolerant fuzzy fallback
  3. negation scope: Tamil post-negators (இல்லை, பறக்கலை ...) negate the
     preceding words, English pre-negators (no, not ...) the following ones
  4. every LayTerm phrase is pre-processed the same way; a phrase matches when
     the IDF-weighted share of its concepts found in the input ("coverage")
     passes a threshold. IDF makes rare, meaningful words (தூள் powder,
     வலை web) count more than common ones (இலை leaf, புள்ளி spot) - this is
     what stops shared filler words from producing false matches.
  5. per symptom keep the strongest match (present or absent).
"""
import math
import re
import unicodedata
from collections import defaultdict

from rapidfuzz import fuzz, process

from .lexicon import CLAUSE_BREAKS, CONCEPTS, NEG_SUFFIXES, NEGATORS_POST, NEGATORS_PRE, RELATED, STOPWORDS

TAMIL_RE = re.compile(r"[஀-௿]")
TOKEN_RE = re.compile(r"[஀-௿]+|[a-z0-9']+")
SPLIT_RE = re.compile(r"[.,;:!?\n\r|।]+")
MAX_TA_SUFFIX = 8      # code points a Tamil token may carry after a known stem
MAX_LAT_SUFFIX = 4
MATCH_THRESHOLD = 0.6  # coverage needed for a lay-term phrase to count


def is_tamil(tok):
    return bool(TAMIL_RE.search(tok))


def normalise(text):
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("‌", "").replace("‍", "").lower()
    return text


def unknown_key(tok):
    """Crude stem for words the lexicon does not know, so that inflected forms
    of the same unknown word still meet."""
    if is_tamil(tok):
        return "~" + tok[:4]
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(tok) > len(suf) + 3 and tok.endswith(suf):
            tok = tok[: -len(suf)]
            break
    return "~" + tok


class Lexicon:
    def __init__(self, concepts=CONCEPTS):
        self.exact = defaultdict(set)
        self.multi = []                       # (tuple of tokens, concept)
        self.prefix = []                      # (stem, concept), Tamil, longest first
        self.lat_prefix = []
        for concept, forms in concepts.items():
            for form in forms:
                toks = TOKEN_RE.findall(normalise(form))
                if not toks:
                    continue
                if len(toks) > 1:
                    self.multi.append((tuple(toks), concept))
                    continue
                t = toks[0]
                self.exact[t].add(concept)
                if is_tamil(t):
                    if len(t) >= 3:
                        self.prefix.append((t, concept))
                elif len(t) >= 4:
                    self.lat_prefix.append((t, concept))
        self.multi.sort(key=lambda x: -len(x[0]))
        self.prefix.sort(key=lambda x: -len(x[0]))
        self.lat_prefix.sort(key=lambda x: -len(x[0]))
        self.fuzzy_vocab = [w for w in self.exact if len(w) >= 5]

    def _token_matches_form(self, tok, form_tok):
        if tok == form_tok:
            return True
        if is_tamil(form_tok):
            return len(form_tok) >= 3 and tok.startswith(form_tok) and len(tok) - len(form_tok) <= MAX_TA_SUFFIX
        return len(form_tok) >= 4 and tok.startswith(form_tok) and len(tok) - len(form_tok) <= MAX_LAT_SUFFIX

    def match_multi(self, toks, i):
        """Longest multi-word form starting at toks[i] -> (length, concept) or None."""
        for form, concept in self.multi:
            n = len(form)
            if i + n <= len(toks) and all(self._token_matches_form(toks[i + k], form[k]) for k in range(n)):
                return n, concept
        return None

    def lookup(self, tok, fuzzy=True):
        if tok in self.exact:
            return set(self.exact[tok])
        table = self.prefix if is_tamil(tok) else self.lat_prefix
        limit = MAX_TA_SUFFIX if is_tamil(tok) else MAX_LAT_SUFFIX
        for stem, concept in table:
            if tok.startswith(stem) and len(tok) - len(stem) <= limit:
                # collect every concept sharing this (longest) stem
                return {c for s, c in table if s == stem}
        if fuzzy and len(tok) >= 5 and not is_tamil(tok):
            hit = process.extractOne(tok, self.fuzzy_vocab, scorer=fuzz.ratio, score_cutoff=88)
            if hit:
                return set(self.exact[hit[0]])
        return None


def _is_neg_suffix_token(tok):
    if is_tamil(tok):
        return len(tok) >= 5 and tok.endswith(NEG_SUFFIXES)
    return len(tok) >= 6 and tok.endswith(("kkala", "kkalai", "yala", "yalai", "rala", "dala"))


class Analyzer:
    """Concept extraction with negation scope."""

    def __init__(self, lexicon=None):
        self.lex = lexicon or Lexicon()

    def items(self, text, use_negation=True):
        """Returns a list of items: dict(concepts=set, text=str, negated=bool)."""
        out = []
        for clause in SPLIT_RE.split(normalise(text)):
            toks = TOKEN_RE.findall(clause)
            clause_items = []
            i = 0
            while i < len(toks):
                tok = toks[i]
                if tok in CLAUSE_BREAKS:
                    out.extend(clause_items)
                    clause_items = []
                    i += 1
                    continue
                mm = self.lex.match_multi(toks, i)
                if mm:
                    n, concept = mm
                    clause_items.append({"concepts": {concept}, "text": " ".join(toks[i:i + n]), "negated": False, "kind": "c"})
                    i += n
                    continue
                if tok in STOPWORDS:
                    i += 1
                    continue
                if not use_negation and (tok in NEGATORS_POST or tok in NEGATORS_PRE):
                    i += 1
                    continue
                if use_negation and tok in NEGATORS_POST:
                    self._negate_back(clause_items, 2)
                    i += 1
                    continue
                if use_negation and tok in NEGATORS_PRE:
                    clause_items.append({"concepts": set(), "text": tok, "negated": False, "kind": "neg_pre"})
                    i += 1
                    continue
                if tok in self.lex.exact:
                    clause_items.append({"concepts": set(self.lex.exact[tok]), "text": tok, "negated": False, "kind": "c"})
                    i += 1
                    continue
                if use_negation and _is_neg_suffix_token(tok):
                    concepts = self.lex.lookup(tok, fuzzy=False) or {unknown_key(tok)}
                    clause_items.append({"concepts": concepts, "text": tok, "negated": True, "kind": "c"})
                    self._negate_back(clause_items[:-1], 1)
                    i += 1
                    continue
                concepts = self.lex.lookup(tok)
                if concepts:
                    clause_items.append({"concepts": concepts, "text": tok, "negated": False, "kind": "c"})
                elif len(tok) > 1:
                    clause_items.append({"concepts": {unknown_key(tok)}, "text": tok, "negated": False, "kind": "u"})
                i += 1
            if use_negation:
                self._apply_pre_negation(clause_items)
            out.extend(clause_items)
        return [it for it in out if it["kind"] in ("c", "u")]

    @staticmethod
    def _negate_back(items, n):
        count = 0
        for it in reversed(items):
            if it["kind"] == "neg_pre":
                break
            if it["kind"] in ("c", "u"):
                it["negated"] = True
                count += 1
                if count >= n:
                    break

    @staticmethod
    def _apply_pre_negation(items):
        remaining = 0
        for it in items:
            if it["kind"] == "neg_pre":
                remaining = 3
                continue
            if remaining and it["kind"] in ("c", "u"):
                it["negated"] = True
                remaining -= 1

    def concept_bags(self, text):
        pos, neg = set(), set()
        for it in self.items(text):
            (neg if it["negated"] else pos).update(it["concepts"])
        return pos, neg - pos


def _related(a, b):
    if a == b:
        return 1.0
    return RELATED.get((a, b)) or RELATED.get((b, a)) or 0.0


class SymptomMatcher:
    """Matches analysed text against LayTerm phrases from the knowledge graph."""

    def __init__(self, layterms, analyzer=None, threshold=MATCH_THRESHOLD):
        """layterms: iterable of dicts with id, text, symptom_id, weight, lang."""
        self.an = analyzer or Analyzer()
        self.threshold = threshold
        self.build(layterms)

    def build(self, layterms):
        self.phrases = []
        df = defaultdict(int)
        for lt in layterms:
            concepts = set()
            for it in self.an.items(lt["text"], use_negation=False):
                concepts |= it["concepts"]
            if not concepts:
                continue
            self.phrases.append({**lt, "concepts": concepts})
            for c in concepts:
                df[c] += 1
        n = max(1, len(self.phrases))
        self.idf = {c: math.log((n + 1) / (d + 1)) + 1.0 for c, d in df.items()}
        median = sorted(self.idf.values())[len(self.idf) // 2] if self.idf else 1.0
        for c in list(self.idf):
            if c.startswith("~"):            # unknown words: don't let them dominate
                self.idf[c] = min(self.idf[c], median * 0.6)

    def _sim(self, c, bag):
        if c in bag:
            return 1.0
        best = 0.0
        if c.startswith("~"):
            for b in bag:
                if b.startswith("~") and fuzz.ratio(c, b) >= 85:
                    best = max(best, 0.8)
            return best
        for b in bag:
            best = max(best, _related(c, b))
        return best

    def _core_matched(self, p, bag):
        """The most informative half of a phrase's known concepts must be
        present - otherwise "green leaves on my plant" would match
        "green caterpillar on the plant" through the generic words alone."""
        known = sorted((c for c in p["concepts"] if not c.startswith("~")), key=lambda c: -self.idf[c])
        if not known:
            return True
        core = known[: max(1, math.ceil(len(known) / 2))]
        got = sum(self.idf[c] * self._sim(c, bag) for c in core)
        return got / sum(self.idf[c] for c in core) >= 0.6

    def match(self, text):
        pos, neg = self.an.concept_bags(text)
        text_lang = "ta" if TAMIL_RE.search(normalise(text)) else None
        results = {}
        for p in self.phrases:
            total = sum(self.idf[c] for c in p["concepts"])
            pos_part = neg_part = 0.0
            for c in p["concepts"]:
                w = self.idf[c]
                sp, sn = self._sim(c, pos), self._sim(c, neg)
                if sn > sp:
                    neg_part += w * sn
                else:
                    pos_part += w * sp
            coverage = (pos_part + neg_part) / total
            if coverage < self.threshold or not self._core_matched(p, pos | neg):
                continue
            if neg_part >= 0.25 * total:
                present, cov = False, coverage
            else:
                present, cov = True, pos_part / total
                if cov < self.threshold:
                    continue
            strength = round(cov * p["weight"], 4)
            sid = p["symptom_id"]
            prev = results.get(sid)
            # evidence strength = best match; the phrase shown (and credited when
            # learning) prefers the farmer's own script if it is nearly as strong
            same = (p.get("lang") == "ta") == (text_lang == "ta")
            rank = strength + (0.06 if same else 0.0)
            if prev is None or rank > prev["_rank"]:
                best = max(strength, prev["strength"]) if prev else strength
                results[sid] = {"symptom_id": sid, "present": present, "strength": best,
                                "coverage": round(cov, 3), "layterm_id": p["id"],
                                "phrase": p["text"], "lang": p.get("lang", "ta"), "_rank": rank}
            elif strength > prev["strength"]:
                prev["strength"] = strength
        for r in results.values():
            r.pop("_rank", None)
        return {
            "matches": sorted(results.values(), key=lambda r: -r["strength"]),
            "concepts": sorted(c for c in pos if not c.startswith("~")),
            "negated_concepts": sorted(c for c in neg if not c.startswith("~")),
            "unknown_words": sorted(c[1:] for c in pos | neg if c.startswith("~")),
        }


# ------------------------------------------------------------------ modifiers
# How bad / how widespread, from plain words - works without any AI service.
_MILD = ["கொஞ்சம்", "லேசா", "லேசாக", "சிறிது", "ஆரம்ப", "இப்போ தான்", "slight", "slightly", "mild", "a little", "just started",
         "starting", "konjam", "lesa", "laesaa"]
_SEVERE = ["ரொம்ப", "அதிகம்", "அதிகமா", "முழுக்க", "முழுசா", "மோசமா", "எல்லா செடி", "severe", "severely", "badly", "heavily",
           "very bad", "everywhere", "whole field", "all plants", "romba", "adhigam", "muzhukka"]
_EXTENT = [(r"(\d{1,3})\s*(%|percent|சதவீதம்)", None),
           (r"ஒன்னு ரெண்டு|ஒன்று இரண்டு|ஒரு சில|one or two|a few plants|few plants|oru sila|onnu rendu", 5),
           (r"பாதி|half|paadhi|paathi", 50),
           (r"எல்லா செடி|முழு வயல்|வயல் முழுக்க|all (the )?plants|whole field|entire field|every plant|ella chedi", 90)]


def extract_modifiers(text):
    t = normalise(text)
    sev = None
    if any(w in t for w in _SEVERE):
        sev = "severe"
    elif any(w in t for w in _MILD):
        sev = "mild"
    extent = None
    for pat, val in _EXTENT:
        m = re.search(pat, t)
        if m:
            extent = min(100, int(m.group(1))) if val is None else val
            break
    return {"severity": sev, "affected_percent": extent}
