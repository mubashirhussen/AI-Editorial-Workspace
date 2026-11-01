from fastapi import APIRouter
from backend.app.api.v1.endpoints import projects, sources, writing
from backend.app.api.routes.editorial import router as editorial_router

api_router = APIRouter()

# Projects: /projects, and /projects/{id}/sources
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(sources.project_sources_router, prefix="/projects", tags=["Sources"])

# Sources: /sources/{id}
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])

# Writing: /writing/drafts
api_router.include_router(writing.router, prefix="/writing", tags=["Writing"])
