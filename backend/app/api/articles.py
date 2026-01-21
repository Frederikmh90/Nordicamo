"""API routes for article search."""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.articles_service import ArticlesService

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("/search")
async def search_articles(
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    country: Optional[str] = None,
    partisan: Optional[str] = None,
    sentiment: Optional[str] = None,
    categories: Optional[str] = None,
    entities: Optional[str] = None,
    outlets: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    service = ArticlesService(db)

    category_list: Optional[List[str]] = categories.split(",") if categories else None
    entity_list: Optional[List[str]] = entities.split(",") if entities else None
    outlet_list: Optional[List[str]] = outlets.split(",") if outlets else None

    return service.search_articles(
        query=q,
        date_from=date_from,
        date_to=date_to,
        country=country,
        partisan=partisan,
        sentiment=sentiment,
        categories=category_list,
        entities=entity_list,
        outlets=outlet_list,
        limit=limit,
        offset=offset,
    )
