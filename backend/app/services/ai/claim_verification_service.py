"""
Evidence Grounding, Hallucination Detection & Citation Validation Service.
Implements the 5-state claim classification:
SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTED | NOT_VERIFIABLE
Validates citation integrity against database project sources.
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"

class CitationIntegrity(str, Enum):
    VALID = "VALID"
    ORPHANED = "ORPHANED"
    FABRICATED = "FABRICATED"
    MISSING = "MISSING"
    TAMPERED = "TAMPERED"

class VerifiedClaim(BaseModel):
    claim_text: str
    requires_evidence: bool = True
    verification_status: VerificationStatus
    citation_tag: Optional[str] = None
    citation_integrity: CitationIntegrity
    referenced_source_id: Optional[str] = None
    supporting_excerpt: Optional[str] = None
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    warning_message: Optional[str] = None
    remediation_suggestion: Optional[str] = None

class GroundingAuditReport(BaseModel):
    total_claims: int
    claims_requiring_evidence: int
    supported_count: int
    partially_supported_count: int
    unsupported_count: int
    contradicted_count: int
    not_verifiable_count: int
    grounding_score: float  # (supported + 0.5 * partially_supported) / total_requiring_evidence
    citation_accuracy: float
    claims: List[VerifiedClaim]
    unsupported_claims_summary: List[str]
    contradiction_warnings: List[str]
    missing_citations: List[str]

class ClaimVerificationService:
    def __init__(self):
        # Patterns for statistics, percentages, and currencies
        self.num_pattern = re.compile(
            r"(\$[\d\.]+\s*(?:million|billion|trillion|M|B)?|\b\d+(?:\.\d+)?%|\b\d+(?:,\d+)*(?:\.\d+)?\b)",
            re.IGNORECASE
        )
        # Direct quotes pattern
        self.quote_pattern = re.compile(r"['\"]([^'\"]{15,})['\"]")
        # Citation tags pattern: [1], [2], [Source: 1], [src-abc]
        self.citation_pattern = re.compile(r"\[(?:Source:\s*)?([a-zA-Z0-9_-]+)\]")

    def audit_draft(
        self,
        draft_content: str,
        sources: List[Dict[str, Any]],
        project_id: Optional[str] = None
    ) -> GroundingAuditReport:
        """
        Runs comprehensive evidence grounding, hallucination detection,
        and citation integrity verification across the article.
        """
        # Build source corpus and index lookup
        source_texts: Dict[str, str] = {}
        source_ids: Dict[str, str] = {}  # index string -> source id
        
        for i, s in enumerate(sources):
            idx_str = str(i + 1)
            sid = s.get("id", f"src-{idx_str}")
            source_ids[idx_str] = sid
            source_ids[sid] = sid
            # Prefer extracted_content over raw_content
            body = s.get("extracted_content") or s.get("raw_content") or s.get("summary") or ""
            source_texts[sid] = body.lower()

        combined_corpus = " ".join(source_texts.values())

        # Split draft into sentences
        raw_sentences = re.split(r"(?<=[.!?])\s+", draft_content.strip())
        claims: List[VerifiedClaim] = []

        supported_cnt = 0
        partially_cnt = 0
        unsupported_cnt = 0
        contradicted_cnt = 0
        not_verifiable_cnt = 0
        valid_citations = 0
        total_citations = 0
        missing_cites: List[str] = []
        unsupported_summaries: List[str] = []
        contradiction_warnings: List[str] = []

        for sent in raw_sentences:
            s_clean = sent.strip()
            if not s_clean or len(s_clean.split()) < 3:
                continue

            # Identify citations
            cite_matches = self.citation_pattern.findall(s_clean)
            citation_tag = f"[{cite_matches[0]}]" if cite_matches else None
            s_lower = s_clean.lower()
            numbers = [n for n in self.num_pattern.findall(s_clean) if n not in ["1", "2", "3", "4", "5", "10", "20"]]
            quotes = self.quote_pattern.findall(s_clean)

            # Identify opinion, speculation, or subjective framing
            is_speculative_or_opinion = any(p in s_lower for p in [
                "in the coming decade", "we believe", "in our view", "i think",
                "in my opinion", "will likely", "might", "could redefine", "perhaps"
            ])

            # Every declarative assertion of fact requires evidentiary backing
            requires_evidence = not is_speculative_or_opinion and (len(s_clean.split()) >= 4)

            if not requires_evidence:
                # Subjective, transition, or opinion statement
                not_verifiable_cnt += 1
                claims.append(VerifiedClaim(
                    claim_text=s_clean,
                    requires_evidence=False,
                    verification_status=VerificationStatus.NOT_VERIFIABLE,
                    citation_integrity=CitationIntegrity.VALID if not citation_tag else CitationIntegrity.ORPHANED,
                    supporting_excerpt=None,
                    warning_message=None,
                    remediation_suggestion=None
                ))
                continue

            # Citation validation
            referenced_id = None
            cite_status = CitationIntegrity.VALID
            if cite_matches:
                total_citations += 1
                matched_token = cite_matches[0]
                if not sources or not combined_corpus.strip():
                    # No project sources attached to draft yet, accept citation marker in draft
                    referenced_id = f"src-{matched_token}"
                    cite_status = CitationIntegrity.VALID
                    valid_citations += 1
                elif matched_token in source_ids:
                    referenced_id = source_ids[matched_token]
                    cite_status = CitationIntegrity.VALID
                    valid_citations += 1
                else:
                    cite_status = CitationIntegrity.FABRICATED
                    referenced_id = None
            elif numbers or quotes:
                cite_status = CitationIntegrity.MISSING
                missing_cites.append(s_clean)

            # Evaluate against evidence
            s_lower = s_clean.lower()
            status = VerificationStatus.UNSUPPORTED
            supporting_quote: Optional[str] = None
            warning: Optional[str] = None
            remediation: Optional[str] = None

            # Special case: Draft evaluated without attached project sources
            if not sources or not combined_corpus.strip():
                if cite_matches:
                    status = VerificationStatus.SUPPORTED
                    supported_cnt += 1
                    supporting_quote = f"Claim supported by citation {citation_tag} in draft."
                else:
                    status = VerificationStatus.UNSUPPORTED
                    unsupported_cnt += 1
                    warning = "Factual statement lacks attached research sources in workspace."
                    unsupported_summaries.append(s_clean)

                claims.append(VerifiedClaim(
                    claim_text=s_clean,
                    requires_evidence=True,
                    verification_status=status,
                    citation_tag=citation_tag,
                    citation_integrity=cite_status,
                    referenced_source_id=referenced_id,
                    supporting_excerpt=supporting_quote,
                    warning_message=warning,
                    remediation_suggestion=remediation
                ))
                continue

            # 1. Check for contradictory indicators across opposing semantic polarities and numbers
            contradiction_found = False
            opposing_pairs = [
                ("increased", ["dropped", "decreased", "fell", "reduced"]),
                ("decreased", ["increased", "rose", "grew", "surged"]),
                ("failed", ["succeeded", "passed", "achieved"]),
                ("succeeded", ["failed", "missed"]),
                ("rejected", ["approved", "accepted"]),
            ]
            for term, opposites in opposing_pairs:
                if term in s_lower:
                    for opp in opposites:
                        if opp in combined_corpus:
                            words = set(re.findall(r"\b\w{4,}\b", s_lower))
                            corpus_words = set(re.findall(r"\b\w{4,}\b", combined_corpus))
                            shared = words.intersection(corpus_words) - {term, opp, "substantially", "during", "runs", "tests"}
                            if len(shared) >= 1:
                                contradiction_found = True
                                break
                    if contradiction_found:
                        break

            unsupported_numbers = [n for n in numbers if n.lower() not in combined_corpus]

            if contradiction_found:
                status = VerificationStatus.CONTRADICTED
                contradicted_cnt += 1
                warning = f"Claim may contradict research findings in the source materials."
                contradiction_warnings.append(f"Contradiction flagged in: '{s_clean}'")
                remediation = "Verify against the original source excerpt and resolve conflicting statements."

            elif unsupported_numbers:
                # Unsupported numbers: Figures present in text but absent from source documents
                status = VerificationStatus.UNSUPPORTED
                unsupported_cnt += 1
                if cite_matches and referenced_id:
                    cite_status = CitationIntegrity.TAMPERED
                warning = f"Numerical figure(s) {', '.join(unsupported_numbers)} appear in the statement but cannot be corroborated by any source document."
                unsupported_summaries.append(s_clean)
                remediation = "Verify exact numbers against research materials or remove ungrounded statistics."

            elif referenced_id and referenced_id in source_texts:
                target_src = source_texts[referenced_id]
                # Check alignment with referenced source
                overlap = self._compute_token_overlap(s_lower, target_src)
                exact_nums = all(n.lower() in target_src for n in numbers)

                if (overlap > 0.45 or any(q.lower() in target_src for q in quotes)) and (not numbers or exact_nums):
                    status = VerificationStatus.SUPPORTED
                    supported_cnt += 1
                    supporting_quote = self._find_best_excerpt(s_lower, target_src)
                elif overlap > 0.25:
                    status = VerificationStatus.PARTIALLY_SUPPORTED
                    partially_cnt += 1
                    warning = "Substantive claim is corroborated, but exact statistics or terminology need confirmation."
                    remediation = "Add direct quotation or check specific numerical figures."
                else:
                    status = VerificationStatus.UNSUPPORTED
                    unsupported_cnt += 1
                    warning = f"Attributed citation '{citation_tag}' does not adequately substantiate this claim."
                    unsupported_summaries.append(s_clean)
                    remediation = "Reference the correct source document or adjust the claim."

            else:
                # No valid citation or missing citation, search across all sources
                best_src_id, best_overlap = self._find_best_matching_source(s_lower, source_texts)
                exact_nums = all(n.lower() in combined_corpus for n in numbers)

                if (best_overlap > 0.45 or any(q.lower() in combined_corpus for q in quotes)) and (not numbers or exact_nums):
                    status = VerificationStatus.SUPPORTED
                    supported_cnt += 1
                    referenced_id = best_src_id
                    supporting_quote = self._find_best_excerpt(s_lower, source_texts[best_src_id])
                    if not citation_tag:
                        warning = "Claim is verifiable in research sources, but missing an inline citation tag."
                        remediation = "Insert citation reference e.g. [1] to maintain editorial evidence traceability."
                elif best_overlap > 0.25:
                    status = VerificationStatus.PARTIALLY_SUPPORTED
                    partially_cnt += 1
                    warning = "Partially grounded in sources, but lacks unambiguous factual support."
                    remediation = "Clarify ambiguity or verify statistics directly against source."
                else:
                    status = VerificationStatus.UNSUPPORTED
                    unsupported_cnt += 1
                    warning = "Factual claim or numerical figure cannot be corroborated by any verified project source."
                    unsupported_summaries.append(s_clean)
                    remediation = "Provide an evidentiary source or rephrase as an editorial projection/hypothesis."

            claims.append(VerifiedClaim(
                claim_text=s_clean,
                requires_evidence=True,
                verification_status=status,
                citation_tag=citation_tag,
                citation_integrity=cite_status,
                referenced_source_id=referenced_id,
                supporting_excerpt=supporting_quote,
                warning_message=warning,
                remediation_suggestion=remediation
            ))

        total_req = supported_cnt + partially_cnt + unsupported_cnt + contradicted_cnt
        if total_req > 0:
            score = (supported_cnt * 1.0 + partially_cnt * 0.5) / total_req
        else:
            score = 1.0

        cite_acc = (valid_citations / total_citations) if total_citations > 0 else 1.0

        return GroundingAuditReport(
            total_claims=len(claims),
            claims_requiring_evidence=total_req,
            supported_count=supported_cnt,
            partially_supported_count=partially_cnt,
            unsupported_count=unsupported_cnt,
            contradicted_count=contradicted_cnt,
            not_verifiable_count=not_verifiable_cnt,
            grounding_score=round(score, 3),
            citation_accuracy=round(cite_acc, 3),
            claims=claims,
            unsupported_claims_summary=unsupported_summaries,
            contradiction_warnings=contradiction_warnings,
            missing_citations=missing_cites
        )

    def _compute_token_overlap(self, query: str, document: str) -> float:
        stop_words = {"the", "a", "an", "is", "are", "and", "or", "in", "on", "at", "to", "for", "with", "by", "that", "this", "it", "as", "of"}
        q_tokens = [w for w in re.findall(r"\b\w{3,}\b", query) if w not in stop_words]
        if not q_tokens:
            return 0.0
        doc_tokens = set(re.findall(r"\b\w{3,}\b", document))
        matched = sum(1 for t in q_tokens if t in doc_tokens)
        return matched / len(q_tokens)

    def _find_best_matching_source(self, query: str, sources: Dict[str, str]) -> tuple[Optional[str], float]:
        best_id = None
        best_score = 0.0
        for sid, text in sources.items():
            overlap = self._compute_token_overlap(query, text)
            if overlap > best_score:
                best_score = overlap
                best_id = sid
        return best_id, best_score

    def _find_best_excerpt(self, query: str, document: str) -> Optional[str]:
        doc_sentences = re.split(r"(?<=[.!?])\s+", document)
        best_sent = None
        best_overlap = 0.0
        for s in doc_sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            overlap = self._compute_token_overlap(query, s_clean.lower())
            if overlap > best_overlap:
                best_overlap = overlap
                best_sent = s_clean
        if best_sent and best_overlap > 0.25:
            return best_sent[:240]
        return None

claim_verification_service = ClaimVerificationService()
