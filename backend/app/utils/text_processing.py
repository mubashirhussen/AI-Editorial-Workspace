import re
from typing import List, Tuple, Optional

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into sentences while respecting common abbreviations and quotes.
    """
    if not text:
        return []
    
    cleaned = text.strip()
    if not cleaned:
        return []

    # Protect common abbreviations before splitting
    protected = cleaned
    abbreviations = [
        ("e.g.", "e_g_placeholder"),
        ("i.e.", "i_e_placeholder"),
        ("Dr.", "Dr_placeholder"),
        ("Mr.", "Mr_placeholder"),
        ("Ms.", "Ms_placeholder"),
        ("Mrs.", "Mrs_placeholder"),
        ("Prof.", "Prof_placeholder"),
        ("Inc.", "Inc_placeholder"),
        ("Ltd.", "Ltd_placeholder"),
        ("vs.", "vs_placeholder"),
        ("etc.", "etc_placeholder"),
        ("U.S.", "U_S_placeholder"),
        ("AI.", "AI_placeholder"),
    ]
    for abbr, placeholder in abbreviations:
        protected = protected.replace(abbr, placeholder)

    # Split on period/exclamation/question mark followed by space
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected)
    
    results = []
    for s in raw_sentences:
        # Restore placeholders
        for abbr, placeholder in abbreviations:
            s = s.replace(placeholder, abbr)
        s_clean = s.strip()
        if s_clean:
            # Also handle any multiline splits
            sub_parts = [p.strip() for p in s_clean.split("\n\n") if p.strip()]
            results.extend(sub_parts)
            
    return results if results else [cleaned]

def count_words(text: str) -> int:
    if not text:
        return 0
    words = re.findall(r'\b[a-zA-Z0-9\'-]+\b', text)
    return len(words)

def count_syllables_in_word(word: str) -> int:
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    # Remove common non-syllable endings
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    word = re.sub(r'^y', '', word)
    matches = re.findall(r'[aeiouy]{1,2}', word)
    return max(1, len(matches))

def calculate_reading_ease(text: str) -> Tuple[float, str]:
    """
    Computes the Flesch Reading Ease score:
    206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
    Score range typically: 0 - 100
    90-100: Very Easy
    80-89: Easy
    70-79: Fairly Easy
    60-69: Standard
    50-59: Fairly Difficult
    30-49: Difficult
    0-29: Very Confusing / Complex
    """
    words = re.findall(r'\b[a-zA-Z0-9\'-]+\b', text)
    total_words = len(words)
    if total_words < 5:
        return 70.0, "Standard"
    
    sentences = split_into_sentences(text)
    total_sentences = max(1, len(sentences))
    
    total_syllables = sum(count_syllables_in_word(w) for w in words)
    
    asl = total_words / total_sentences
    asw = total_syllables / total_words
    
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    score = round(max(0.0, min(100.0, score)), 1)
    
    if score >= 90:
        grade = "Very Easy"
    elif score >= 80:
        grade = "Easy"
    elif score >= 70:
        grade = "Fairly Easy"
    elif score >= 60:
        grade = "Standard"
    elif score >= 50:
        grade = "Fairly Difficult"
    elif score >= 30:
        grade = "Difficult"
    else:
        grade = "Very Confusing"
        
    return score, grade

def replace_text_safely(document: str, original_target: str, replacement: str) -> Tuple[str, bool, Optional[str]]:
    """
    Safely replaces an occurrence of original_target in document.
    Ensures that if there are multiple occurrences or ambiguous boundaries,
    it behaves predictably without corrupting other content.
    Returns: (new_document, success, error_message_if_any)
    """
    if not original_target:
        return document, False, "Original text target is empty."
    
    target_clean = original_target.strip()
    if not target_clean:
        return document, False, "Original text target contains only whitespace."

    # First try exact match
    occurrences = document.count(target_clean)
    if occurrences == 1:
        new_doc = document.replace(target_clean, replacement.strip(), 1)
        return new_doc, True, None
    elif occurrences > 1:
        # Multiple exact matches: replace the first one cleanly
        new_doc = document.replace(target_clean, replacement.strip(), 1)
        return new_doc, True, None
    
    # Try normalized whitespace match
    pattern = re.escape(target_clean)
    pattern = re.sub(r'\\\s+', r'\\s+', pattern)
    matches = list(re.finditer(pattern, document, re.IGNORECASE))
    
    if len(matches) == 1:
        match = matches[0]
        new_doc = document[:match.start()] + replacement.strip() + document[match.end():]
        return new_doc, True, None
    elif len(matches) > 1:
        match = matches[0]
        new_doc = document[:match.start()] + replacement.strip() + document[match.end():]
        return new_doc, True, None
    
    return document, False, "Original target passage could not be uniquely matched in the draft. Manual adjustment recommended."
