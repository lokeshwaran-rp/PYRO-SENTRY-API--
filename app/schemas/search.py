from typing import List, Dict
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Individual search match item."""
    id: str
    type: str
    title: str
    details: str


class SearchResultGroups(BaseModel):
    """Categorized search matches."""
    targets: List[SearchResultItem]
    threats: List[SearchResultItem]
    assets: List[SearchResultItem]


class SearchResponse(BaseModel):
    """Search query response."""
    query: str
    total_results: int
    results: SearchResultGroups
