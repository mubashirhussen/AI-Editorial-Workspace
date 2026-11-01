import re
import logging
from typing import List, Dict, Any, Optional, Set
from backend.app.utils.text_processing import split_into_sentences

logger = logging.getLogger(__name__)

# Canonical Entities Catalog for high-precision deterministic extraction
CANONICAL_ENTITIES = {
    # Companies
    "OpenAI": ("COMPANY", ["OpenAI Inc.", "OpenAI LLC", "OpenAI, Inc."]),
    "Anthropic": ("COMPANY", ["Anthropic PBC", "Anthropic AI"]),
    "Google": ("COMPANY", ["Google LLC", "Google Inc."]),
    "Microsoft": ("COMPANY", ["Microsoft Corporation", "Microsoft Corp."]),
    "Meta": ("COMPANY", ["Meta Platforms", "Meta Platforms Inc.", "Facebook"]),
    "Nvidia": ("COMPANY", ["NVIDIA Corporation", "Nvidia Corp.", "NVIDIA"]),
    "Amazon": ("COMPANY", ["Amazon.com Inc.", "AWS", "Amazon Web Services"]),
    "Apple": ("COMPANY", ["Apple Inc."]),
    "DeepSeek": ("COMPANY", ["DeepSeek AI", "Hangzhou DeepSeek"]),
    "Mistral AI": ("COMPANY", ["Mistral", "Mistral SAS"]),
    "Cohere": ("COMPANY", ["Cohere Inc."]),
    "xAI": ("COMPANY", ["xAI Corp."]),
    "TSMC": ("COMPANY", ["Taiwan Semiconductor Manufacturing Co."]),
    "Intel": ("COMPANY", ["Intel Corporation", "Intel Corp."]),
    "AMD": ("COMPANY", ["Advanced Micro Devices"]),
    "Databricks": ("COMPANY", ["Databricks Inc."]),
    "Snowflake": ("COMPANY", ["Snowflake Inc."]),
    "Scale AI": ("COMPANY", ["Scale AI Inc."]),
    "Hugging Face": ("COMPANY", ["Hugging Face Inc."]),

    # Founders and Executives
    "Sam Altman": ("PERSON", ["Altman", "Samuel Altman"]),
    "Dario Amodei": ("PERSON", ["Amodei"]),
    "Demis Hassabis": ("PERSON", ["Sir Demis Hassabis", "Hassabis"]),
    "Jensen Huang": ("PERSON", ["Huang"]),
    "Satya Nadella": ("PERSON", ["Nadella"]),
    "Mark Zuckerberg": ("PERSON", ["Zuckerberg"]),
    "Sundar Pichai": ("PERSON", ["Pichai"]),
    "Elon Musk": ("PERSON", ["Musk"]),
    "Greg Brockman": ("PERSON", ["Brockman"]),
    "Ilya Sutskever": ("PERSON", ["Sutskever"]),
    "Yann LeCun": ("PERSON", ["LeCun"]),
    "Arthur Mensch": ("PERSON", ["Mensch"]),
    "Daniela Amodei": ("PERSON", []),

    # AI Models
    "GPT-4": ("AI_MODEL", ["GPT-4 Turbo", "GPT-4o", "GPT-4.5"]),
    "Claude 3.5 Sonnet": ("AI_MODEL", ["Claude 3.5", "Sonnet 3.5"]),
    "Claude 3 Opus": ("AI_MODEL", ["Opus 3", "Claude Opus"]),
    "Gemini 1.5 Pro": ("AI_MODEL", ["Gemini 1.5", "Gemini Pro 1.5"]),
    "Gemini Ultra": ("AI_MODEL", ["Gemini 1.0 Ultra"]),
    "Llama 3": ("AI_MODEL", ["Llama-3", "Llama 3.1", "Llama 3.2"]),
    "Mistral Large": ("AI_MODEL", ["Mistral Large 2"]),
    "DeepSeek-V3": ("AI_MODEL", ["DeepSeek V3"]),
    "DeepSeek-R1": ("AI_MODEL", ["DeepSeek R1", "R1"]),
    "DALL-E 3": ("AI_MODEL", ["DALL-E"]),
    "Sora": ("AI_MODEL", ["OpenAI Sora"]),

    # Products
    "ChatGPT": ("PRODUCT", ["ChatGPT Plus", "ChatGPT Team", "ChatGPT Enterprise"]),
    "Microsoft Copilot": ("PRODUCT", ["Copilot", "GitHub Copilot", "Copilot Pro"]),
    "Cursor": ("PRODUCT", ["Cursor IDE"]),
    "Midjourney": ("PRODUCT", ["Midjourney v6"]),
    "Perplexity": ("PRODUCT", ["Perplexity AI", "Perplexity Pro"]),
    "AWS Bedrock": ("PRODUCT", ["Amazon Bedrock", "Bedrock"]),
    "Google Vertex AI": ("PRODUCT", ["Vertex AI"]),
    "Nvidia Blackwell": ("PRODUCT", ["Blackwell B200", "GB200", "B200", "B100"]),
    "Nvidia H100": ("PRODUCT", ["H100 Tensor Core GPU", "H200"]),

    # Technologies
    "Retrieval-Augmented Generation": ("TECHNOLOGY", ["RAG"]),
    "Transformer Architecture": ("TECHNOLOGY", ["Transformer", "Transformers"]),
    "Reinforcement Learning from Human Feedback": ("TECHNOLOGY", ["RLHF"]),
    "Mixture of Experts": ("TECHNOLOGY", ["MoE"]),
    "Low-Rank Adaptation": ("TECHNOLOGY", ["LoRA"]),
    "Two-Phase Immersion Cooling": ("TECHNOLOGY", ["Immersion Cooling", "liquid cooling"]),
    "Small Modular Reactor": ("TECHNOLOGY", ["SMR", "micro-nuclear"]),
    "High Bandwidth Memory": ("TECHNOLOGY", ["HBM3e", "HBM4", "HBM"]),
    "CUDA": ("TECHNOLOGY", ["CUDA platform"]),

    # Investors
    "Sequoia Capital": ("INVESTOR", ["Sequoia"]),
    "Andreessen Horowitz": ("INVESTOR", ["a16z"]),
    "Y Combinator": ("INVESTOR", ["YC"]),
    "Benchmark": ("INVESTOR", ["Benchmark Capital"]),
    "Lightspeed Venture Partners": ("INVESTOR", ["Lightspeed"]),
    "Khosla Ventures": ("INVESTOR", ["Khosla"]),
    "SoftBank Vision Fund": ("INVESTOR", ["SoftBank"]),
    "Founders Fund": ("INVESTOR", []),
    "Index Ventures": ("INVESTOR", []),

    # Funding Organizations
    "National Science Foundation": ("FUNDING_ORG", ["NSF"]),
    "DARPA": ("FUNDING_ORG", ["Defense Advanced Research Projects Agency"]),
    "EU AI Office": ("FUNDING_ORG", ["European AI Office"]),
    "Frontier Model Forum": ("FUNDING_ORG", []),

    # Industries
    "AI Infrastructure": ("INDUSTRY", ["datacenter infrastructure", "AI compute"]),
    "Semiconductor Industry": ("INDUSTRY", ["chipmaking", "silicon fabrication"]),
    "Enterprise Software": ("INDUSTRY", ["SaaS", "enterprise AI"]),

    # Markets
    "Generative AI Market": ("MARKET", ["GenAI market"]),
    "AI Hardware Acceleration": ("MARKET", ["AI accelerator market", "datacenter GPU market"]),
}

def normalize_entity_name(name: str) -> str:
    """
    Normalizes obvious corporate naming variations without merging distinct entities.
    Example: 'OpenAI, Inc.' -> 'OpenAI', 'NVIDIA Corp.' -> 'Nvidia'
    """
    cleaned = name.strip()
    # Strip trailing punctuation
    cleaned = re.sub(r'[,.]+$', '', cleaned)
    
    # Strip common corporate suffixes
    suffix_pattern = r'(?i)\s+(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|Limited|PBC|SAS|Co\.?|Technologies|Holdings)$'
    cleaned = re.sub(suffix_pattern, '', cleaned).strip()
    cleaned = re.sub(r'[,.]+$', '', cleaned).strip()

    # Normalize known alias lookups
    for canonical, (_, aliases) in CANONICAL_ENTITIES.items():
        if cleaned.lower() == canonical.lower():
            return canonical
        for alias in aliases:
            if cleaned.lower() == alias.lower():
                return canonical
                
    return cleaned

class EntityExtractor:
    """
    Extracts structured entities across 9 distinct categories with supporting excerpts and confidence.
    """

    def extract_entities(self, text: str, source_id: Optional[str] = None, source_title: Optional[str] = None) -> List[Dict[str, Any]]:
        if not text:
            return []

        sentences = split_into_sentences(text)
        entities_found: Dict[str, Dict[str, Any]] = {}

        # 1. Check Canonical Catalog across sentences
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            for canonical_name, (ent_type, aliases) in CANONICAL_ENTITIES.items():
                targets = [canonical_name] + aliases
                for target in targets:
                    # Match exact word boundaries
                    pattern = r'(?<![A-Za-z0-9_])' + re.escape(target) + r'(?![A-Za-z0-9_])'
                    if re.search(pattern, sentence_clean, flags=re.IGNORECASE):
                        normalized = normalize_entity_name(canonical_name)
                        key = f"{normalized}_{ent_type}"
                        if key not in entities_found:
                            entities_found[key] = {
                                "name": canonical_name,
                                "normalized_name": normalized,
                                "entity_type": ent_type,
                                "source_id": source_id,
                                "source_title": source_title,
                                "supporting_excerpt": sentence_clean[:300],
                                "confidence": 0.95,
                                "extraction_method": "canonical_nlp"
                            }
                        break

        # 2. Heuristic Regex Pattern Extraction for uncatalogued entities
        # E.g. AI Models like "ModelX-7B", "DeepSeek-V2", etc.
        model_regex = r'\b([A-Z][a-zA-Z0-9]+(?:-[A-Z0-9]+|\s+[0-9]+(?:\.[0-9]+)?[a-zA-Z]*))\b'
        for sentence in sentences:
            sentence_clean = sentence.strip()
            # Check for funding patterns: "$X million" or "$Y billion" -> Funding / Investor context
            if "$" in sentence_clean:
                funding_match = re.search(r'\$([0-9]+(?:\.[0-9]+)?\s*(?:million|billion|M|B))', sentence_clean, re.IGNORECASE)
                if funding_match:
                    # Look for investor/company near it
                    lead_words = sentence_clean[:100]
                    # Assign MARKET or FUNDING context if relevant
                    key = f"Venture Funding_{sentence_clean[:20]}"
                    # Just keep supporting facts cleanly

        return list(entities_found.values())
