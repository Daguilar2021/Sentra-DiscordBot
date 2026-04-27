import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
import re


class ModerationEngine:
    """
    NLP-powered moderation engine for Sentra.
    Uses a pre-trained XLM-RoBERTa toxicity classifier + KeyBERT for keyword extraction.
    """

    def __init__(self):
        model_name = "unitary/toxic-bert"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()  # inference mode

        self.kw_model = KeyBERT()

        bad_word_patterns = [
            #list of curse/nsfw/hate speech words
            r"\b[a@][s\$][s\$]\b",
            r"\b[a@][s\$][s\$]h[o0][l1][e3][s\$]?\b",
            r"\b[b][a@][s\$][t\+][a@]rd\b",
            r"\b[b][e3][a@][s\$][t\+][i1][a@]?[l1]([i1][t\+]y)?\b",
            r"\b[b][e3][a@][s\$][t\+][i1][l1][i1][t\+]y\b",
            r"\b[b][e3][s\$][t\+][i1][a@][l1]([i1][t\+]y)?\b",
            r"\bb[i1][t\+]ch[s\$]?\b",
            r"\bb[i1][t\+]ch[e3]r[s\$]?\b",
            r"\bb[i1][t\+]ch[e3][s\$]\b",
            r"\bb[i1][t\+]ch[i1]ng?\b",
            r"\bb[l1][o0]wj[o0]b[s\$]?\b",
            r"\bb[o0]ob(?:s)?\b",
            r"\bc[l1][i1][t\+]\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]?\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]u\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]u(c|k|ck|q)[e3]d\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]u(c|k|ck|q)[e3]r\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]u(c|k|ck|q)[i1]ng\b",
            r"\b(c|k|ck|q)[o0](c|k|ck|q)[s\$]u(c|k|ck|q)[s\$]\b",
            r"^cum[s\$]?$",
            r"cumm??[e3]r",
            r"cumm?[i1]ngcock",
            r"(c|k|ck|q)um[s\$]h[o0][t\+]",
            r"(c|k|ck|q)un[i1][l1][i1]ngu[s\$]",
            r"(c|k|ck|q)un[i1][l1][l1][i1]ngu[s\$]",
            r"(c|k|ck|q)unn[i1][l1][i1]ngu[s\$]",
            r"(c|k|ck|q)un[t\+][s\$]?",
            r"(c|k|ck|q)un[t\+][l1][i1](c|k|ck|q)",
            r"(c|k|ck|q)un[t\+][l1][i1](c|k|ck|q)[e3]r",
            r"(c|k|ck|q)un[t\+][l1][i1](c|k|ck|q)[i1]ng",
            r"\bcyb[e3]r(ph|f)u(c|k|ck|q)\b",
            r"\bc[l1!|]it(?:s)?\b",
            r"\bc[l1!|]it[o0]r[i1](?:s)?\b",
            r"\bd[a@]mn\b",
            r"\bd[i1]ck\b",
            r"\bd[i1][l1]d[o0]\b",
            r"\bd[i1][l1]d[o0][s\$]\b",
            r"\bd[i1]n(c|k|ck|q)\b",
            r"d[i1]n(c|k|ck|q)[s\$]",
            r"\b[e3]j[a@]cu[l1]\b",
            r"(ph|f)[a@]g[s\$]?",
            r"(ph|f)[a@]gg[i1]ng",
            r"(ph|f)[a@]gg?[o0][t\+][s\$]?",
            r"(ph|f)[a@]gg[s\$]",
            r"(ph|f)[e3][l1][l1]?[a@][t\+][i1][o0]",
            r"(ph|f)u(c|k|ck|q)",
            r"(ph|f)u(c|k|ck|q)[s\$]?",
            r"g[a@]ngb[a@]ng[s\$]?",
            r"g[a@]ngb[a@]ng[e3]d",
            r"h[o0]m?m[o0]",
            r"h[o0]rny",
            r"j[a@](c|k|ck|q)\-?[o0](ph|f)(ph|f)?",
            r"j[e3]rk\-?[o0](ph|f)(ph|f)?",
            r"j[i1][s\$z][s\$z]?m?",
            r"\bkys\b",
            r"[ck][o0][nN][dD][u0o][mM][s\$]?",
            r"mast(e|ur)b(8|ait|ate)",
            r"\bm[o0]t[o0]rb[o0][a@]t(?:ing|ed|s)?\b",
            r"n+[i1]+[gq]+[e3]*r+[s\$]*",
            r"\bn+[i1]+[gq]+[a@]+s?\b",
            r"n+[i1]+[gq]+[l1]+et(?:s)?\b",
            r"\b[cĆćĈĉČčĊċÇçḈḉȻȼꞒꞓꟄꞔƇƈɕ]+[hĤĥȞȟḦḧḢḣḨḩḤḥḪḫH̱ẖĦħⱧⱨꞪɦꞕΗНн]+[[iÍíi̇́Ììi̇̀ĬĭÎîǏǐÏïḮḯĨĩi̇̃ĮįĮ́į̇́Į̃į̇̃ĪīĪ̀ī̀ỈỉȈȉI̋i̋ȊȋỊịꞼꞽḬḭƗɨᶖİiIıＩｉ1lĺľļḷḹl̃ḽḻłŀƚꝉⱡɫɬꞎꬷꬸꬹᶅɭȴＬｌ]+[nŃńǸǹŇňÑñṄṅŅņṆṇṊṋṈṉN̈n̈ƝɲŊŋꞐꞑꞤꞥᵰᶇɳȵꬻꬼИиПпＮｎ]+[kḰḱǨǩĶķḲḳḴḵƘƙⱩⱪᶄꝀꝁꝂꝃꝄꝅꞢꞣ]+[sŚśṤṥŜŝŠšṦṧṠṡŞşṢṣṨṩȘșS̩s̩ꞨꞩⱾȿꟅʂᶊᵴ]*\b",
            r"\b[o0]rg[a@][s\$][i1]m[s\$]?\b",
            r"\b[o0]rg[a@][s\$]m[s\$]?\b",
            r"\bp[e3]nn?[i1][s\$]\b",
            r"\bp[i1][s\$][s\$]\b",
            r"\bp[i1][s\$][s\$][o0](ph|f)(ph|f)\b",
            r"\bp[o0]rn\b",
            r"\bp[o0]rn[o0][s\$]?\b",
            r"\bp[o0]rn[o0]gr[a@]phy\b",
            r"\bp[u*]ss(?:y|ies)\b",
            r"p+[rR]+[iI!1]+[cCkKqQ]+[sS\$]?",
            r"p+[uU]+[sS\$][sS\$][iI1!]+[e3][sS\$]?",
            r"p+[uU]+[sS\$][sS\$]y[s\$]?",
            r"r+[a@]+[pq]+[e3]?",
            r"r[a@]+[ppq]+[e3][s\$]?",
            r"r[a@]+[p]+[e3]d",
            r"r[a@]+[p]+[e3]r",
            r"r[a@]+[p]+[e3]r[s\$]?",
            r"r[a@]+[p]+[i1!l]ng",
            r"r[a@]+[p]+[i1!l]ng[s\$]?",
            r"r[a@]+[p]+[i1!l]st",
            r"r[a@]+[p]+[i1!l]st[s\$]?",
            r"[s\$][e3]x",
            r"[s\$]h[i1][t\+][s\$]?",
            r"\bshit(?:s|ty|ted|ting)?\b",
            r"[s\$][l1]u[t\+][s\$]?",
            r"[s\$]mu[t\+][s\$]?",
            r"[s\$]tfu",
            r"[t\+]w[a@][t\+][s\$]?",
            r"[t\+][i1]t1",
            r"\bt[i1!l]tt(?:y|ie|ies|ys)\b",
            r"\bv[a@]g[i1!]na\b",
            r"\bwh[o0]re(?:s)?\b",

            #list of impropper embeddings
            r"\b[b]+[r]+[a@]+[z]+[e3]*[r]*[s]*\b",
            r"\bp[o0]rnh[u*]b\b",
            r"\bxnxx\b",
            r"\bxv[i1!]d[e3]os\b",
            r"\bredt[u*]be\b",
            r"\by[o0]up[o0]rn\b",
            r"\bonlyf[a@]ns\b",
            r"\bch[a@]turb[a@]te\b",
            r"\bmyfr[e3][e3]c[a@]ms\b",
            r"\bc[a@]m(?:girl|boy|s)?\b",
        ]
        
        # Combine into a single regex for fast searching
        # This automatically strips ^ and $ and enforces word boundaries \b on every pattern
        combined_pattern = "|".join(f"\\b(?:{p.lstrip('^').rstrip('$')})\\b" for p in bad_word_patterns)
        self.bad_words_regex = re.compile(combined_pattern, re.IGNORECASE)

        print("✅ Moderation engine loaded.")

    def analyze(self, text: str) -> dict:
        """
        Analyze a message for toxicity.
        Returns {"toxic": bool, "score": float, "keywords": list[str]}
        """
        # Fast-path regex check
        match = self.bad_words_regex.search(text)
        if match:
            return {
                "toxic": True,
                "score": 1.0,
                "keywords": [match.group()],
            }

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            # unitary/toxic-bert uses independent sigmoids for each class (toxic, severe_toxic, etc.)
            probs = torch.sigmoid(logits)

        # Class 0 is 'toxic'
        toxic_score = probs[0][0].item()

        keywords = []
        if toxic_score > 0.5:
            keywords = self._extract_keywords(text)

        return {
            "toxic": toxic_score > 0.5,
            "score": round(toxic_score, 4),
            "keywords": keywords,
        }

    def _extract_keywords(self, text: str, top_n: int = 5) -> list[str]:
        """Extract key phrases from a flagged message for logging."""
        try:
            kw_results = self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                top_n=top_n,
            )
            return [kw[0] for kw in kw_results]
        except Exception:
            # KeyBERT can fail on very short texts
            return []
