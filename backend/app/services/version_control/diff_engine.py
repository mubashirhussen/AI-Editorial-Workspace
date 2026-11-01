import difflib
import re
from typing import Dict, Any, List

class DiffEngine:
    """
    Deterministic comparison engine computing word count metrics,
    line-level diffs, and word-level inline additions/deletions.
    """

    @staticmethod
    def count_words(text: str) -> int:
        if not text:
            return 0
        return len(re.findall(r"\b[\w'-]+\b", text))

    @classmethod
    def compare_texts(cls, text_a: str, text_b: str) -> Dict[str, Any]:
        text_a = text_a or ""
        text_b = text_b or ""

        word_count_a = cls.count_words(text_a)
        word_count_b = cls.count_words(text_b)
        word_count_diff = word_count_b - word_count_a

        char_count_a = len(text_a)
        char_count_b = len(text_b)
        char_count_diff = char_count_b - char_count_a

        # 1. Line-level diff
        lines_a = text_a.splitlines(keepends=True) or [""]
        lines_b = text_b.splitlines(keepends=True) or [""]

        ndiff = difflib.ndiff(lines_a, lines_b)
        diff_chunks: List[Dict[str, str]] = []
        additions_count = 0
        deletions_count = 0
        unchanged_count = 0

        for line in ndiff:
            code = line[:2]
            content = line[2:]
            if code == "+ ":
                additions_count += 1
                diff_chunks.append({"type": "addition", "text": content})
            elif code == "- ":
                deletions_count += 1
                diff_chunks.append({"type": "deletion", "text": content})
            elif code == "  ":
                unchanged_count += 1
                diff_chunks.append({"type": "unchanged", "text": content})
            # Skip "? " which is intra-line guide in ndiff

        # 2. Word-level tokens for fine-grained inline visual highlighting
        # Tokenize preserving spaces so we can reconstruct exact inline diffs
        tokens_a = re.findall(r'\S+|\s+', text_a)
        tokens_b = re.findall(r'\S+|\s+', text_b)

        matcher = difflib.SequenceMatcher(None, tokens_a, tokens_b)
        word_diff_chunks: List[Dict[str, str]] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                word_diff_chunks.append({
                    "type": "equal",
                    "text": "".join(tokens_a[i1:i2])
                })
            elif tag == 'delete':
                word_diff_chunks.append({
                    "type": "delete",
                    "text": "".join(tokens_a[i1:i2])
                })
            elif tag == 'insert':
                word_diff_chunks.append({
                    "type": "insert",
                    "text": "".join(tokens_b[j1:j2])
                })
            elif tag == 'replace':
                word_diff_chunks.append({
                    "type": "delete",
                    "text": "".join(tokens_a[i1:i2])
                })
                word_diff_chunks.append({
                    "type": "insert",
                    "text": "".join(tokens_b[j1:j2])
                })

        return {
            "word_count_a": word_count_a,
            "word_count_b": word_count_b,
            "word_count_diff": word_count_diff,
            "char_count_a": char_count_a,
            "char_count_b": char_count_b,
            "char_count_diff": char_count_diff,
            "additions_count": additions_count,
            "deletions_count": deletions_count,
            "unchanged_count": unchanged_count,
            "diff_chunks": diff_chunks,
            "word_diff_chunks": word_diff_chunks
        }

diff_engine = DiffEngine()

