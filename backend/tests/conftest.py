import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.database import Base, get_db
from backend.app.models.base import EditorialStyleProfile
from backend.app.main import app

# In-memory SQLite with StaticPool so all connections share the same memory DB
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Ensure baseline default style profile is provisioned in test database
    if not db.query(EditorialStyleProfile).filter(EditorialStyleProfile.is_default == True).first():
        default_p = EditorialStyleProfile(
            id="default-style-profile-000000000000",
            organization_id=None,
            name="This Week in AI Standard",
            publication_name="This Week in AI",
            tone="Authoritative, analytical, objective",
            target_audience="Founders, builders, and operators",
            max_sentence_length=25,
            preferred_sentence_length=18,
            max_paragraph_length=75,
            target_flesch_score=65.0,
            preferred_terminology={
                "AI chip": "AI accelerator",
                "running the model": "inference",
                "hallucination": "model fabrication",
                "smart agent": "autonomous agent",
                "super intelligence": "AGI",
                "large model": "frontier model"
            },
            words_to_avoid=[
                "delve", "game-changer", "revolutionary", "paradigm shift",
                "unprecedented", "groundbreaking", "unrivaled", "pivotal"
            ],
            headline_style="Direct, analytical, hook-driven",
            formatting_preferences={
                "bold_key_takeaways": True,
                "bullet_summaries": True,
                "citation_style": "numbered_bracket"
            },
            is_default=True
        )
        db.add(default_p)
        db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
