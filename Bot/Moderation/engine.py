import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT


class ModerationEngine:
    """
    NLP-powered moderation engine for Sentra.
    Uses a pre-trained XLM-RoBERTa toxicity classifier + KeyBERT for keyword extraction.
    """

    def __init__(self):
        model_name = "malexandersalazar/xlm-roberta-large-binary-cls-toxicity"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()  # inference mode

        self.kw_model = KeyBERT()

        print("✅ Moderation engine loaded.")

    def analyze(self, text: str) -> dict:
        """
        Analyze a message for toxicity.
        Returns {"toxic": bool, "score": float, "keywords": list[str]}
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)

        # Binary classification: index 1 = toxic
        toxic_score = probs[0][1].item()

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
