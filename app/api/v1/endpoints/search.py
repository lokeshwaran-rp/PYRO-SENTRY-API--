from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.search import SearchResponse
from app.db.session import get_db
from app.services.db_service import search_all
from app.auth.security import get_current_user

router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get("", response_model=SearchResponse, summary="Search Across Targets, Threats & Assets")
async def global_search(
    q: str = Query(..., min_length=1, description="Search term / keyword across targets, threats, and assets"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Unified search endpoint returning matched targets, threats, and assets."""
    return await search_all(db, q)
