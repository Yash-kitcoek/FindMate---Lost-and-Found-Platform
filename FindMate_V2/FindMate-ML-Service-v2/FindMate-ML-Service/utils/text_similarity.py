"""
Hybrid text and attribute similarity for FindMate item matching.

The matcher uses several lightweight signals instead of depending on a single
TF-IDF score. That makes it more tolerant of short descriptions such as
"black i phone near library" vs. "Apple iPhone in black cover".
"""

from collections import Counter
from difflib import SequenceMatcher
import logging
import math
import re

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None

logger = logging.getLogger(__name__)


class TextSimilarity:
    """Calculate robust text similarity using lexical, fuzzy, and TF-IDF signals."""

    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "by", "for", "from", "has", "have",
        "found", "i", "in", "is", "it", "lost", "my", "near", "of", "on", "one", "or", "the", "this", "to", "with"
    }

    TOKEN_ALIASES = {
        "cellphone": "phone",
        "mobile": "phone",
        "smartphone": "phone",
        "iphone": "phone apple iphone",
        "ipad": "tablet apple ipad",
        "earphone": "earbuds headset headphones audio",
        "earphones": "earbuds headset headphones audio",
        "headset": "headset headphones earphones audio",
        "headsets": "headset headphones earphones audio",
        "handsset": "headset headphones earphones audio",
        "handssets": "headset headphones earphones audio",
        "earpods": "earbuds apple",
        "airpods": "earbuds apple airpods",
        "laptop": "computer laptop",
        "notebook": "computer laptop",
        "rucksack": "backpack bag",
        "schoolbag": "backpack bag",
        "wallet": "purse wallet",
        "spectacles": "glasses eyewear",
        "specs": "glasses eyewear",
        "idcard": "id card",
        "identitycard": "id card",
        "charger": "adapter charger",
        "pendrive": "usb drive pendrive",
        "umbrella": "umbrella rain",
        "watch": "watch wristwatch timepiece",
        "watches": "watch wristwatch timepiece",
        "titan": "titan watch"
    }

    COLORS = {
        "black", "white", "blue", "red", "green", "yellow", "orange", "purple",
        "pink", "brown", "grey", "gray", "silver", "gold", "golden", "beige",
        "cream", "maroon", "navy", "violet"
    }

    COMMON_BRANDS = {
        "apple", "samsung", "oneplus", "oppo", "vivo", "xiaomi", "redmi", "realme",
        "lenovo", "hp", "dell", "asus", "acer", "nike", "adidas", "puma", "boat",
        "jbl", "sony", "noise", "fastrack", "wildcraft", "skybags", "american",
        "tourister", "mi", "nothing"
    }

    ITEM_FAMILIES = {
        "phone": {"phone", "iphone", "mobile", "smartphone", "cellphone"},
        "audio": {"headset", "headsets", "handsset", "handssets", "headphones", "earphones", "earbuds", "airpods", "audio"},
        "umbrella": {"umbrella", "rain"},
        "bag": {"bag", "backpack", "rucksack", "schoolbag", "purse", "wallet"},
        "laptop": {"laptop", "computer", "notebook"},
        "charger": {"charger", "adapter", "cable"},
        "keys": {"key", "keys", "keychain"},
        "documents": {"id", "card", "document", "documents", "license", "certificate"},
        "glasses": {"glasses", "spectacles", "specs", "eyewear"},
        "book": {"book", "books", "notebook", "textbook"},
        "watch": {"watch", "watches", "wristwatch", "timepiece"}
    }

    def __init__(self):
        if TfidfVectorizer:
            self.word_vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                max_features=3000,
                ngram_range=(1, 2),
                sublinear_tf=True
            )
            self.char_vectorizer = TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                max_features=3000,
                sublinear_tf=True
            )
        else:
            self.word_vectorizer = None
            self.char_vectorizer = None

    def preprocess_text(self, text):
        """Normalize text while keeping useful model numbers and short tokens."""
        if not text:
            return ""

        text = str(text).lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        expanded = []
        for token in text.split():
            normalized = self.TOKEN_ALIASES.get(token, token)
            expanded.extend(normalized.split())

        return " ".join(expanded)

    def tokenize(self, text):
        """Return normalized tokens excluding common stop words."""
        cleaned = self.preprocess_text(text)
        return {
            token for token in cleaned.split()
            if token and token not in self.STOP_WORDS and len(token) > 1
        }

    def token_overlap(self, text1, text2):
        """Calculate Jaccard-like token overlap between two texts."""
        tokens1 = self.tokenize(text1)
        tokens2 = self.tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1.intersection(tokens2))
        smaller_set = min(len(tokens1), len(tokens2))
        union = len(tokens1.union(tokens2))

        containment = intersection / smaller_set if smaller_set else 0.0
        jaccard = intersection / union if union else 0.0
        return float((containment * 0.65) + (jaccard * 0.35))

    def fuzzy_similarity(self, text1, text2):
        """Calculate spelling-tolerant similarity for names and short phrases."""
        text1 = self.preprocess_text(text1)
        text2 = self.preprocess_text(text2)

        if not text1 or not text2:
            return 0.0

        return float(SequenceMatcher(None, text1, text2).ratio())

    def extract_attributes(self, *texts):
        """Extract colors, brands, and useful model tokens from item text."""
        combined = self.combine_texts(*texts)
        tokens = self.tokenize(combined)

        return {
            "colors": sorted(tokens.intersection(self.COLORS)),
            "brands": sorted(tokens.intersection(self.COMMON_BRANDS)),
            "modelTokens": sorted(token for token in tokens if re.search(r"\d", token))
        }

    def item_family_score(self, text1, text2):
        """Return 1 for same object family, 0 for known conflicting families, 0.5 if unknown."""
        families1 = self.extract_item_families(text1)
        families2 = self.extract_item_families(text2)

        if not families1 or not families2:
            return 0.5

        if families1.intersection(families2):
            return 1.0

        return 0.0

    def extract_item_families(self, text):
        tokens = self.tokenize(text)
        families = set()

        for family, keywords in self.ITEM_FAMILIES.items():
            if tokens.intersection(keywords):
                families.add(family)

        return families

    def attribute_similarity(self, attrs1, attrs2):
        """Score structured attributes with penalties for clear contradictions."""
        color_score = self._set_similarity(attrs1.get("colors"), attrs2.get("colors"))
        brand_score = self._set_similarity(attrs1.get("brands"), attrs2.get("brands"))
        model_score = self._set_similarity(attrs1.get("modelTokens"), attrs2.get("modelTokens"))

        available_scores = [
            score for score, left, right in [
                (color_score, attrs1.get("colors"), attrs2.get("colors")),
                (brand_score, attrs1.get("brands"), attrs2.get("brands")),
                (model_score, attrs1.get("modelTokens"), attrs2.get("modelTokens"))
            ]
            if left and right
        ]

        if not available_scores:
            return 0.5, color_score, brand_score, model_score

        weighted = (color_score * 0.35) + (brand_score * 0.40) + (model_score * 0.25)
        return float(weighted), color_score, brand_score, model_score

    def _set_similarity(self, values1, values2):
        set1 = set(values1 or [])
        set2 = set(values2 or [])

        if not set1 and not set2:
            return 0.5
        if not set1 or not set2:
            return 0.5

        if set1.intersection(set2):
            return 1.0

        return 0.0

    def calculate_similarity(self, text1, text2):
        """Calculate a hybrid similarity score between two texts."""
        try:
            if not text1 or not text2:
                return 0.0

            word_score = self._tfidf_similarity(text1, text2, self.word_vectorizer)
            char_score = self._tfidf_similarity(text1, text2, self.char_vectorizer)
            overlap_score = self.token_overlap(text1, text2)
            fuzzy_score = self.fuzzy_similarity(text1, text2)

            score = (
                word_score * 0.45 +
                char_score * 0.25 +
                overlap_score * 0.20 +
                fuzzy_score * 0.10
            )

            return float(max(0.0, min(1.0, score)))

        except Exception as e:
            logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.0

    def calculate_batch_similarity(self, query_text, documents):
        """Calculate hybrid similarity between one query and many documents."""
        try:
            if not query_text or not documents:
                return [0.0] * len(documents)

            word_scores = self._batch_tfidf_similarity(query_text, documents, self.word_vectorizer)
            char_scores = self._batch_tfidf_similarity(query_text, documents, self.char_vectorizer)

            scores = []
            for index, document in enumerate(documents):
                overlap_score = self.token_overlap(query_text, document)
                fuzzy_score = self.fuzzy_similarity(query_text, document)
                score = (
                    word_scores[index] * 0.45 +
                    char_scores[index] * 0.25 +
                    overlap_score * 0.20 +
                    fuzzy_score * 0.10
                )
                scores.append(float(max(0.0, min(1.0, score))))

            return scores

        except Exception as e:
            logger.error(f"Error calculating batch similarity: {str(e)}")
            return [0.0] * len(documents)

    def _tfidf_similarity(self, text1, text2, vectorizer):
        texts = [self.preprocess_text(text1), self.preprocess_text(text2)]
        if not texts[0] or not texts[1]:
            return 0.0

        if not vectorizer:
            return self._counter_cosine(
                self._word_ngrams(texts[0], min_n=1, max_n=2),
                self._word_ngrams(texts[1], min_n=1, max_n=2)
            )

        matrix = vectorizer.fit_transform(texts)
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])

    def _batch_tfidf_similarity(self, query_text, documents, vectorizer):
        processed_query = self.preprocess_text(query_text)
        processed_docs = [self.preprocess_text(doc) for doc in documents]

        if not processed_query:
            return [0.0] * len(documents)

        if not vectorizer:
            query_terms = self._word_ngrams(processed_query, min_n=1, max_n=2)
            return [
                self._counter_cosine(query_terms, self._word_ngrams(document, min_n=1, max_n=2))
                for document in processed_docs
            ]

        matrix = vectorizer.fit_transform([processed_query] + processed_docs)
        similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]
        return similarities.tolist()

    def _word_ngrams(self, text, min_n=1, max_n=2):
        tokens = [token for token in text.split() if token not in self.STOP_WORDS]
        terms = []

        for size in range(min_n, max_n + 1):
            for index in range(0, len(tokens) - size + 1):
                terms.append(" ".join(tokens[index:index + size]))

        return Counter(terms)

    def _counter_cosine(self, left, right):
        if not left or not right:
            return 0.0

        common = set(left).intersection(right)
        numerator = sum(left[token] * right[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))

        if not left_norm or not right_norm:
            return 0.0

        return float(numerator / (left_norm * right_norm))

    def combine_texts(self, *texts):
        """Combine multiple item fields into one searchable string."""
        return " ".join([str(text) for text in texts if text])


