import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey, JSON, Index, Boolean
from sqlalchemy.orm import relationship, synonym
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan", lazy="selectin")
    projects = relationship("ResearchProject", back_populates="organization", cascade="all, delete-orphan", lazy="selectin")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan", lazy="selectin")
    style_profiles = relationship("EditorialStyleProfile", back_populates="organization", cascade="all, delete-orphan", lazy="selectin")


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        Index("uq_org_user", "organization_id", "user_id", unique=True),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="EDITOR")  # OWNER, ADMIN, EDITOR, REVIEWER, VIEWER
    joined_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="EDITOR")  # ADMIN, EDITOR, REVIEWER, VIEWER
    token = Column(String(255), unique=True, nullable=False, index=True)
    invited_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="invitations")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    briefs = relationship("ResearchBrief", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    drafts = relationship("WritingDraft", back_populates="project", lazy="selectin")
    editorial_outputs = relationship("EditorialOutput", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    entities = relationship("ResearchEntity", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    claims = relationship("ResearchClaim", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    relationships = relationship("ResearchRelationship", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    contradictions = relationship("ResearchContradiction", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    trends = relationship("ResearchTrend", back_populates="project", cascade="all, delete-orphan", lazy="selectin")

    def __init__(self, **kwargs):
        # Support both name and title interchangeably
        if "name" in kwargs and "title" not in kwargs:
            kwargs["title"] = kwargs["name"]
        elif "title" in kwargs and "name" not in kwargs:
            kwargs["name"] = kwargs["title"]
        super().__init__(**kwargs)

class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        Index("ix_sources_project_created", "project_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=True, index=True)
    original_url = Column(String(1024), nullable=True)
    source_type = Column(String(50), default="URL", nullable=False) # URL, TEXT, ARTICLE, TWEET
    raw_content = Column(Text, nullable=True)
    extracted_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(String(100), nullable=True)
    extraction_status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, EXTRACTING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="sources")
    analyses = relationship("SourceAnalysis", back_populates="source", cascade="all, delete-orphan", lazy="selectin", uselist=False)

    def __init__(self, **kwargs):
        if "original_url" in kwargs and "url" not in kwargs:
            kwargs["url"] = kwargs["original_url"]
        elif "url" in kwargs and "original_url" not in kwargs:
            kwargs["original_url"] = kwargs["url"]
        super().__init__(**kwargs)

class SourceAnalysis(Base):
    __tablename__ = "source_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=True)
    key_points = Column(JSON, default=list, nullable=False)
    reported_facts = Column(JSON, default=list, nullable=False)
    analysis = Column(JSON, default=list, nullable=False)
    founder_implications = Column(JSON, default=dict, nullable=False)
    uncertainties = Column(JSON, default=list, nullable=False)
    newsletter_angles = Column(JSON, default=list, nullable=False)

    # Legacy & detailed fields for research assistant
    key_developments = Column(JSON, default=list, nullable=False)
    important_claims = Column(JSON, default=list, nullable=False)
    facts = Column(JSON, default=list, nullable=False)
    speculation = Column(JSON, default=list, nullable=False)
    implications = Column(JSON, default=dict, nullable=False)
    limitations = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    source = relationship("Source", back_populates="analyses")

class ResearchBrief(Base):
    __tablename__ = "research_briefs"
    __table_args__ = (
        Index("ix_briefs_project_created", "project_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="Research Brief", nullable=False)
    executive_summary = Column(Text, nullable=False)
    key_developments = Column(JSON, default=list, nullable=False)
    strategic_implications = Column(JSON, default=dict, nullable=False)
    newsletter_angles = Column(JSON, default=list, nullable=False)
    source_references = Column(JSON, default=list, nullable=False)

    # Rich synthesis fields
    brief_content = Column(JSON, default=dict, nullable=False)
    evidence = Column(JSON, default=list, nullable=False)
    recommended_angle = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="briefs")

class WritingDraft(Base):
    __tablename__ = "writing_drafts"
    __table_args__ = (
        Index("ix_drafts_project_created", "project_id", "created_at"),
        Index("ix_drafts_org_created", "organization_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="SET NULL"), nullable=True, index=True)
    brief_id = Column(String(36), ForeignKey("research_briefs.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), default="editorial_analysis", nullable=False, index=True)
    target_audience = Column(String(100), default="Founders, builders, and operators", nullable=True)
    tone = Column(String(100), default="Authoritative, analytical, objective", nullable=True)
    desired_length = Column(Integer, default=800, nullable=True)
    original_content = Column(Text, nullable=False)
    revised_content = Column(Text, nullable=False)
    final_content = Column(Text, nullable=True)
    word_count = Column(Integer, default=0, nullable=False)
    readability_score = Column(Float, nullable=True)
    research_grounding_score = Column(Float, nullable=True)
    unsupported_claims_count = Column(Integer, default=0, nullable=False)
    style_profile_id = Column(String(36), ForeignKey("editorial_style_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    style_score = Column(Float, nullable=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="drafts")
    brief = relationship("ResearchBrief", foreign_keys=[brief_id])
    style_profile = relationship("EditorialStyleProfile", back_populates="drafts")
    suggestions = relationship("WritingSuggestion", back_populates="draft", cascade="all, delete-orphan", lazy="selectin")
    editorial_output = relationship("EditorialOutput", back_populates="draft", uselist=False)

class WritingSuggestion(Base):
    __tablename__ = "writing_suggestions"
    __table_args__ = (
        Index("ix_suggestions_draft_status", "draft_id", "status"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    draft_id = Column(String(36), ForeignKey("writing_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=True)
    suggested_rewrite = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    severity = Column(String(20), default="medium", nullable=False)
    reason = Column(Text, nullable=True, default="")
    confidence = Column(Float, default=0.9, nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True) # PENDING, ACCEPTED, REJECTED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    draft = relationship("WritingDraft", back_populates="suggestions")

    def __init__(self, **kwargs):
        if "suggested_text" in kwargs and "suggested_rewrite" not in kwargs:
            kwargs["suggested_rewrite"] = kwargs["suggested_text"]
        elif "suggested_rewrite" in kwargs and "suggested_text" not in kwargs:
            kwargs["suggested_text"] = kwargs["suggested_rewrite"]
        super().__init__(**kwargs)

class EditorialOutput(Base):
    __tablename__ = "editorial_outputs"
    __table_args__ = (
        Index("ix_editorial_project_created", "project_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_id = Column(String(36), ForeignKey("writing_drafts.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    headline = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    original_content = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    source_references = Column(JSON, default=list, nullable=False)
    ai_review_results = Column(JSON, default=dict, nullable=True)
    status = Column(String(50), default="DRAFT_CREATED", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="editorial_outputs")
    draft = relationship("WritingDraft", back_populates="editorial_output")
    reviews = relationship("EditorialReview", back_populates="editorial", cascade="all, delete-orphan", lazy="selectin")

    def __init__(self, **kwargs):
        if "content" in kwargs and "original_content" not in kwargs:
            kwargs["original_content"] = kwargs["content"]
        super().__init__(**kwargs)


class EditorialReview(Base):
    __tablename__ = "editorial_reviews"
    __table_args__ = (
        Index("ix_editorial_review_created", "editorial_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    editorial_id = Column(String(36), ForeignKey("editorial_outputs.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_name = Column(String(255), default="Human Editor", nullable=False)
    review_status = Column(String(50), nullable=False, index=True)  # APPROVED, CHANGES_REQUESTED, HUMAN_REVIEW_PENDING
    overall_feedback = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

    editorial = relationship("EditorialOutput", back_populates="reviews")
    comments = relationship("EditorialComment", back_populates="review", cascade="all, delete-orphan", lazy="selectin")


class EditorialComment(Base):
    __tablename__ = "editorial_comments"
    __table_args__ = (
        Index("ix_editorial_comments_review", "review_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    review_id = Column(String(36), ForeignKey("editorial_reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    section_reference = Column(String(100), nullable=True)
    original_text = Column(Text, nullable=True)
    comment = Column(Text, nullable=False)
    suggested_revision = Column(Text, nullable=True)
    resolution_status = Column(String(50), default="open", nullable=False, index=True)  # open, resolved, rejected
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    review = relationship("EditorialReview", back_populates="comments")


class ResearchEntity(Base):
    __tablename__ = "research_entities"
    __table_args__ = (
        Index("ix_entities_project_type", "project_id", "entity_type"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # COMPANY, PERSON, AI_MODEL, PRODUCT, TECHNOLOGY, INVESTOR, FUNDING_ORG, INDUSTRY, MARKET
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True)
    supporting_excerpt = Column(Text, nullable=True)
    confidence = Column(Float, default=0.9, nullable=False)
    extraction_method = Column(String(50), default="heuristic_nlp", nullable=False)  # llm_verified, heuristic_nlp
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="entities")
    source = relationship("Source")


class ResearchClaim(Base):
    __tablename__ = "research_claims"
    __table_args__ = (
        Index("ix_claims_project_classification", "project_id", "evidence_classification"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    supporting_excerpt = Column(Text, nullable=False)
    evidence_classification = Column(String(50), default="DIRECTLY_STATED", nullable=False, index=True)  # DIRECTLY_STATED, REPORTED_BY_SOURCE, INFERENCE, UNVERIFIED
    entity_references = Column(JSON, default=list, nullable=False)
    confidence = Column(Float, default=0.9, nullable=False)
    publication_date = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="claims")
    source = relationship("Source")


class ResearchRelationship(Base):
    __tablename__ = "research_relationships"
    __table_args__ = (
        Index("ix_relationships_project_type", "project_id", "relationship_type"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_entity_name = Column(String(255), nullable=False, index=True)
    target_entity_name = Column(String(255), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)  # ANNOUNCED, DEVELOPED, INVESTED_IN, COMPETES_WITH, USES, REPORTED_BY, SUPPORTS, CONTRADICTS
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True)
    supporting_evidence = Column(Text, nullable=False)
    confidence = Column(Float, default=0.85, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="relationships")
    source = relationship("Source")


class ResearchContradiction(Base):
    __tablename__ = "research_contradictions"
    __table_args__ = (
        Index("ix_contradictions_project", "project_id"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_a_id = Column(String(36), nullable=True)
    claim_b_id = Column(String(36), nullable=True)
    source_a_id = Column(String(36), nullable=True)
    source_b_id = Column(String(36), nullable=True)
    claim_a_text = Column(Text, nullable=False)
    claim_b_text = Column(Text, nullable=False)
    disagreement_nature = Column(Text, nullable=False)
    possible_explanations = Column(Text, nullable=False)
    unresolved_questions = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="contradictions")


class ResearchTrend(Base):
    __tablename__ = "research_trends"
    __table_args__ = (
        Index("ix_trends_project_cat", "project_id", "category"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    theme = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # EMERGING_TECHNOLOGY, REPEATED_ANNOUNCEMENT, MARKET_DEVELOPMENT, DEVELOPER_ADOPTION, FUNDING_PATTERN, PRODUCT_LAUNCH
    supporting_source_ids = Column(JSON, default=list, nullable=False)
    evidence_summary = Column(Text, nullable=False)
    is_prediction = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float, default=0.85, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject", back_populates="trends")


class EditorialStyleProfile(Base):
    __tablename__ = "editorial_style_profiles"
    __table_args__ = (
        Index("ix_style_org_default", "organization_id", "is_default"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    publication_name = Column(String(255), default="This Week in AI", nullable=False)
    tone = Column(String(100), default="Authoritative, analytical, objective", nullable=False)
    target_audience = Column(String(255), default="Founders, builders, and operators", nullable=False)
    max_sentence_length = Column(Integer, default=25, nullable=False)
    preferred_sentence_length = Column(Integer, default=18, nullable=False)
    max_paragraph_length = Column(Integer, default=75, nullable=False)
    target_flesch_score = Column(Float, default=65.0, nullable=False)
    preferred_terminology = Column(JSON, default=dict, nullable=False)
    words_to_avoid = Column(JSON, default=list, nullable=False)
    headline_style = Column(String(100), default="Direct, analytical, hook-driven", nullable=False)
    formatting_preferences = Column(JSON, default=dict, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization", back_populates="style_profiles")
    drafts = relationship("WritingDraft", back_populates="style_profile")



class EditorialVersion(Base):
    """
    Immutable version snapshot capturing change history for research briefs,
    writing drafts, and editorial newsletter outputs.
    """
    __tablename__ = "editorial_versions"
    __table_args__ = (
        Index("ix_editorial_versions_doc", "document_type", "document_id", "version_number"),
        Index("ix_editorial_versions_created", "document_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    document_type = Column(String(50), nullable=False, index=True)  # WRITING_DRAFT, RESEARCH_BRIEF, EDITORIAL_OUTPUT
    document_id = Column(String(36), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    content_snapshot = Column(Text, nullable=False)
    change_summary = Column(Text, default="", nullable=False)
    change_type = Column(String(50), default="MANUAL_EDIT", nullable=False)  # INITIAL, MANUAL_EDIT, AI_REVISION, SUGGESTION_ACCEPTED, SUGGESTION_REJECTED, RESTORE
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    organization = relationship("Organization")
    creator = relationship("User")


# ==============================================================================
# PHASE 4 DATA MODEL EXTENSIONS: AUTH, AI, JOBS, ANALYTICS & AUDIT LOGS
# ==============================================================================

class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_exp", "user_id", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User")


class ResearchEvidence(Base):
    __tablename__ = "research_evidence"
    __table_args__ = (
        Index("ix_evidence_project_source", "project_id", "source_id"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    project_id = Column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_id = Column(String(36), ForeignKey("research_claims.id", ondelete="SET NULL"), nullable=True, index=True)
    excerpt = Column(Text, nullable=False)
    fact_type = Column(String(50), default="DIRECT_FACT", nullable=False)
    confidence = Column(Float, default=0.95, nullable=False)
    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    project = relationship("ResearchProject")
    source = relationship("Source")
    claim = relationship("ResearchClaim")


class AiProviderConfig(Base):
    __tablename__ = "ai_provider_configs"
    __table_args__ = (
        Index("ix_ai_provider_org", "organization_id", "provider"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True) # openai, google_gemini, anthropic, groq
    model_name = Column(String(100), nullable=False)
    encrypted_api_key = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    config_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"
    __table_args__ = (
        Index("ix_integration_org_provider", "organization_id", "provider"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="connected", nullable=False)
    masked_key = Column(String(100), nullable=True)
    encrypted_secret = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    organization = relationship("Organization")


class ProviderUsageRecord(Base):
    __tablename__ = "provider_usage_records"
    __table_args__ = (
        Index("ix_usage_org_created", "organization_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False, index=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class IntegrationHealthRecord(Base):
    __tablename__ = "integration_health_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    provider = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    response_time_ms = Column(Float, default=0.0, nullable=False)
    error_details = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        Index("ix_jobs_org_status", "organization_id", "status"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, RUNNING, COMPLETED, FAILED
    payload = Column(JSON, default=dict, nullable=False)
    result = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    __table_args__ = (
        Index("ix_activity_org_created", "organization_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_org_created", "organization_id", "created_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor_email = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    changes_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notif_user_read", "user_id", "is_read"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class UsageEvent(Base):
    __tablename__ = "usage_events"
    __table_args__ = (
        Index("ix_events_org_metric_time", "organization_id", "metric_name", "timestamp"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, default=1.0, nullable=False)
    tags_json = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
