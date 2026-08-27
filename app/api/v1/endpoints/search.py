from fastapi import APIRouter, Query
from app.schemas.search import SearchResponse
from app.services.mock_data import search_all

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get("", response_model=SearchResponse, summary="Search Across Targets, Threats & Assets")
async def global_search(
    q: str = Query(..., min_length=1, description="Search term / keyword across targets, threats, and assets")
):
    """Unified search endpoint returning matched targets, threats, and assets."""
    return search_all(q)
