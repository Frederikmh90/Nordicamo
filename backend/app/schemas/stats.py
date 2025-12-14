"""Pydantic schemas for statistics endpoints."""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import date


class DateRange(BaseModel):
    """Date range model."""
    earliest: Optional[str] = None
    latest: Optional[str] = None


class OverviewResponse(BaseModel):
    """Overview statistics response."""
    total_articles: int
    total_outlets: int
    date_range: DateRange
    by_country: Dict[str, int]
    by_partisan: Dict[str, int]


class CountryStatsItem(BaseModel):
    """Country statistics item."""
    country: str
    count: int


class ArticlesByCountryResponse(BaseModel):
    """Articles by country response."""
    filters: Dict[str, Optional[str]]
    data: List[CountryStatsItem]


class TimeSeriesItem(BaseModel):
    """Time series data item."""
    date: str
    count: int


class ArticlesOverTimeResponse(BaseModel):
    """Articles over time response."""
    granularity: str
    filters: Dict[str, Optional[str]]
    data: List[TimeSeriesItem]


class TopOutletItem(BaseModel):
    """Top outlet item."""
    domain: str
    outlet_name: Optional[str] = None
    country: Optional[str] = None
    partisan: Optional[str] = None
    count: int


class TopOutletsResponse(BaseModel):
    """Top outlets response."""
    filters: Dict[str, Optional[str]]
    data: List[TopOutletItem]


class CategoryItem(BaseModel):
    """Category statistics item."""
    category: str
    count: int


class CategoriesResponse(BaseModel):
    """Categories distribution response."""
    filters: Dict[str, Optional[str]]
    data: List[CategoryItem]


class SentimentItem(BaseModel):
    """Sentiment statistics item."""
    sentiment: str
    count: int
    avg_score: float


class SentimentResponse(BaseModel):
    """Sentiment distribution response."""
    filters: Dict[str, Optional[str]]
    data: List[SentimentItem]


class EntityItem(BaseModel):
    """Entity item."""
    entity_name: str
    count: int
    positive_count: int
    negative_count: int
    neutral_count: int


class TopEntitiesResponse(BaseModel):
    """Top entities response."""
    entity_type: str
    filters: Dict[str, Optional[str]]
    data: List[EntityItem]


class EntityStatisticsResponse(BaseModel):
    """Entity statistics response."""
    filters: Dict[str, Optional[str]]
    total_articles: int
    articles_with_persons: int
    articles_with_locations: int
    articles_with_organizations: int
    coverage: Dict[str, float]

