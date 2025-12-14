"""Topic modeling API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.topic_service import TopicService
from app.schemas.topics import (
    TopicDistributionResponse,
    TopicsOverTimeResponse,
    TopicStatisticsResponse,
    TopicItem,
    TopicTimeItem
)

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("/distribution", response_model=TopicDistributionResponse)
async def get_topic_distribution(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get topic distribution."""
    service = TopicService(db)
    data = service.get_topic_distribution(
        country=country,
        partisan=partisan,
        date_from=date_from,
        date_to=date_to
    )
    
    return TopicDistributionResponse(
        filters={
            "country": country,
            "partisan": partisan,
            "date_from": date_from,
            "date_to": date_to
        },
        data=[TopicItem(**item) for item in data]
    )


@router.get("/over-time", response_model=TopicsOverTimeResponse)
async def get_topics_over_time(
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    country: Optional[str] = Query(None, description="Filter by country"),
    granularity: str = Query("month", description="Time granularity: day, week, month, year"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get topics over time."""
    service = TopicService(db)
    data = service.get_topics_over_time(
        topic_id=topic_id,
        country=country,
        granularity=granularity,
        date_from=date_from,
        date_to=date_to
    )
    
    return TopicsOverTimeResponse(
        granularity=granularity,
        filters={
            "topic_id": topic_id,
            "country": country,
            "date_from": date_from,
            "date_to": date_to
        },
        data=[TopicTimeItem(**item) for item in data]
    )


@router.get("/statistics", response_model=TopicStatisticsResponse)
async def get_topic_statistics(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    db: Session = Depends(get_db)
):
    """Get topic statistics."""
    service = TopicService(db)
    data = service.get_topic_statistics(
        country=country,
        partisan=partisan
    )
    
    return TopicStatisticsResponse(
        filters={
            "country": country,
            "partisan": partisan
        },
        **data
    )

