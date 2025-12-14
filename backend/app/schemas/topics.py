"""Pydantic schemas for topic modeling endpoints."""

from pydantic import BaseModel
from typing import Dict, List, Optional


class TopicItem(BaseModel):
    """Topic distribution item."""
    topic_id: int
    count: int
    avg_probability: float


class TopicDistributionResponse(BaseModel):
    """Topic distribution response."""
    filters: Dict[str, Optional[str]]
    data: List[TopicItem]


class TopicTimeItem(BaseModel):
    """Topic over time item."""
    date: str
    topic_id: int
    count: int


class TopicsOverTimeResponse(BaseModel):
    """Topics over time response."""
    granularity: str
    filters: Dict[str, Optional[str]]
    data: List[TopicTimeItem]


class TopicStatisticsResponse(BaseModel):
    """Topic statistics response."""
    filters: Dict[str, Optional[str]]
    total_articles: int
    articles_with_topics: int
    unique_topics: int
    avg_probability: float
    coverage: float

