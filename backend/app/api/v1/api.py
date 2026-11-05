from fastapi import APIRouter
from backend.app.api.v1.endpoints import projects

api_router = APIRouter()

# Projects: /projects
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
