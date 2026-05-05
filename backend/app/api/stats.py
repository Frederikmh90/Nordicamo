"""Statistics API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.stats_service import StatsService
from app.schemas.stats import (
    OverviewResponse,
    ArticlesByCountryResponse,
    ArticlesOverTimeResponse,
    ArticlesOverTimeByOutletResponse,
    TopOutletsResponse,
    CountryStatsItem,
    TimeSeriesItem,
    OutletTimeSeriesItem,
    TopOutletItem,
    CategoriesResponse,
    CategoriesOverTimeResponse,
    SentimentResponse,
    CategoryItem,
    CategoryOverTimeItem,
    SentimentItem,
    TopEntitiesResponse,
    EntityStatisticsResponse,
    EntityItem,
    OutletProfileResponse,
    ConcentrationMetricsResponse,
    PartisanMixResponse,
    PartisanMixItem,
    TopicSimilarityResponse,
    SimilarityValue,
)

router = APIRouter(prefix="/api/stats", tags=["statistics"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(db: Session = Depends(get_db)):
    """Get overview statistics."""
    service = StatsService(db)
    return service.get_overview()


@router.get("/articles-by-country", response_model=ArticlesByCountryResponse)
async def get_articles_by_country(
    partisan: Optional[str] = Query(None, description="Filter by partisan (Right, Left, Other)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get article counts by country with optional filters."""
    service = StatsService(db)
    data = service.get_articles_by_country(
        partisan=partisan,
        date_from=date_from,
        date_to=date_to
    )
    
    return ArticlesByCountryResponse(
        filters={
            "partisan": partisan,
            "date_from": date_from,
            "date_to": date_to
        },
        data=[CountryStatsItem(**item) for item in data]
    )


@router.get("/articles-over-time", response_model=ArticlesOverTimeResponse)
async def get_articles_over_time(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    granularity: str = Query("month", description="Time granularity: day, week, month, year"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get time series data for articles over time."""
    service = StatsService(db)
    data = service.get_articles_over_time(
        country=country,
        partisan=partisan,
        granularity=granularity,
        date_from=date_from,
        date_to=date_to
    )
    
    return ArticlesOverTimeResponse(
        granularity=granularity,
        filters={
            "country": country,
            "partisan": partisan,
            "date_from": date_from,
            "date_to": date_to
        },
        data=[TimeSeriesItem(**item) for item in data]
    )


@router.get("/articles-over-time-by-outlet", response_model=ArticlesOverTimeByOutletResponse)
async def get_articles_over_time_by_outlet(
    outlets: str = Query(..., description="Comma-separated outlet domains"),
    country: Optional[str] = Query(None, description="Filter by country"),
    granularity: str = Query("month", description="Time granularity: day, week, month, year"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Get time series data for selected outlets."""
    outlet_list = [o.strip() for o in outlets.split(",") if o.strip()]
    if not outlet_list:
        raise HTTPException(status_code=400, detail="outlets must contain at least one domain")
    service = StatsService(db)
    data = service.get_articles_over_time_by_outlet(
        outlets=outlet_list,
        country=country,
        granularity=granularity,
        date_from=date_from,
        date_to=date_to,
    )

    return ArticlesOverTimeByOutletResponse(
        granularity=granularity,
        filters={
            "country": country,
            "date_from": date_from,
            "date_to": date_to,
            "outlets": ",".join(outlet_list),
        },
        data=[OutletTimeSeriesItem(**item) for item in data],
    )


@router.get("/top-outlets", response_model=TopOutletsResponse)
async def get_top_outlets(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, description="Number of outlets to return", ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get top outlets by article count."""
    service = StatsService(db)
    data = service.get_top_outlets(
        country=country,
        partisan=partisan,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )
    
    return TopOutletsResponse(
        filters={
            "country": country,
            "partisan": partisan,
            "date_from": date_from,
            "date_to": date_to
        },
        data=[TopOutletItem(**item) for item in data]
    )


@router.get("/outlet-profile", response_model=OutletProfileResponse)
async def get_outlet_profile(
    domain: str = Query(..., description="Outlet domain"),
    db: Session = Depends(get_db)
):
    """Get outlet profile summary by domain."""
    service = StatsService(db)
    data = service.get_outlet_profile(domain=domain)
    if not data:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return OutletProfileResponse(**data)


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    db: Session = Depends(get_db)
):
    """Get category distribution."""
    service = StatsService(db)
    data = service.get_categories_distribution(
        country=country,
        partisan=partisan
    )
    
    return CategoriesResponse(
        filters={
            "country": country,
            "partisan": partisan
        },
        data=[CategoryItem(**item) for item in data]
    )


@router.get("/categories/over-time", response_model=CategoriesOverTimeResponse)
async def get_categories_over_time(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    outlets: Optional[str] = Query(None, description="Comma-separated outlet domains"),
    granularity: str = Query("month", description="Time granularity: year, month, week"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(6, description="Number of categories to return", ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get category trends over time."""
    service = StatsService(db)
    outlet_list = [o.strip() for o in outlets.split(",") if o.strip()] if outlets else None
    data = service.get_categories_over_time(
        country=country,
        partisan=partisan,
        outlets=outlet_list,
        date_from=date_from,
        date_to=date_to,
        granularity=granularity,
        limit=limit,
    )

    return CategoriesOverTimeResponse(
        filters={
            "country": country,
            "partisan": partisan,
            "outlets": outlets,
            "granularity": granularity,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
        },
        data=[CategoryOverTimeItem(**item) for item in data]
    )


@router.get("/sentiment", response_model=SentimentResponse)
async def get_sentiment(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    db: Session = Depends(get_db)
):
    """Get sentiment distribution."""
    service = StatsService(db)
    data = service.get_sentiment_distribution(
        country=country,
        partisan=partisan
    )
    
    return SentimentResponse(
        filters={
            "country": country,
            "partisan": partisan
        },
        data=[SentimentItem(**item) for item in data]
    )


@router.get("/entities/top", response_model=TopEntitiesResponse)
async def get_top_entities(
    entity_type: str = Query("persons", description="Entity type: persons, locations, organizations"),
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    limit: int = Query(20, description="Number of entities to return", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get top entities by type."""
    if entity_type not in ["persons", "locations", "organizations"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="entity_type must be one of: persons, locations, organizations")
    
    service = StatsService(db)
    data = service.get_top_entities(
        entity_type=entity_type,
        country=country,
        partisan=partisan,
        limit=limit
    )
    
    return TopEntitiesResponse(
        entity_type=entity_type,
        filters={
            "country": country,
            "partisan": partisan
        },
        data=[EntityItem(**item) for item in data]
    )


@router.get("/entities/statistics", response_model=EntityStatisticsResponse)
async def get_entity_statistics(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    db: Session = Depends(get_db)
):
    """Get entity statistics."""
    service = StatsService(db)
    data = service.get_entity_statistics(
        country=country,
        partisan=partisan
    )
    
    return EntityStatisticsResponse(
        filters={
            "country": country,
            "partisan": partisan
        },
        **data
    )


@router.get("/concentration", response_model=ConcentrationMetricsResponse)
async def get_concentration_metrics(
    country: Optional[str] = Query(None, description="Filter by country"),
    partisan: Optional[str] = Query(None, description="Filter by partisan"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    top_n: int = Query(5, description="Top N outlets for concentration share", ge=1, le=25),
    db: Session = Depends(get_db),
):
    """Get outlet concentration metrics (Top-N share, HHI, ENP, coverage)."""
    service = StatsService(db)
    data = service.get_concentration_metrics(
        country=country,
        partisan=partisan,
        date_from=date_from,
        date_to=date_to,
        top_n=top_n,
    )
    return ConcentrationMetricsResponse(
        filters={
            "country": country,
            "partisan": partisan,
            "date_from": date_from,
            "date_to": date_to,
        },
        **data,
    )


@router.get("/partisan-mix", response_model=PartisanMixResponse)
async def get_partisan_mix(
    country: Optional[str] = Query(None, description="Filter by country"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Get partisan composition with unknown/missing diagnostics."""
    service = StatsService(db)
    data = service.get_partisan_mix(
        country=country,
        date_from=date_from,
        date_to=date_to,
    )
    return PartisanMixResponse(
        filters={
            "country": country,
            "date_from": date_from,
            "date_to": date_to,
        },
        total_count=int(data.get("total_count", 0)),
        unknown_or_missing_count=int(data.get("unknown_or_missing_count", 0)),
        data=[PartisanMixItem(**row) for row in data.get("data", [])],
    )


@router.get("/topic-similarity", response_model=TopicSimilarityResponse)
async def get_topic_similarity(
    level: str = Query("country", description="Comparison level: country, country_partisan, or outlet"),
    country: Optional[str] = Query(None, description="Country filter (required for outlet level)"),
    partisan: Optional[str] = Query(None, description="Partisan filter"),
    outlets: Optional[str] = Query(None, description="Comma-separated outlet domains"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit_topics: int = Query(12, description="Number of topics in vector space", ge=2, le=40),
    db: Session = Depends(get_db),
):
    """Get pairwise topic-similarity matrices (cosine + JSD)."""
    normalized_level = (level or "country").lower()
    allowed_levels = {"country", "country_partisan", "country_orientation", "outlet"}
    if normalized_level not in allowed_levels:
        raise HTTPException(
            status_code=400,
            detail="level must be 'country', 'country_partisan', 'country_orientation', or 'outlet'",
        )
    if normalized_level == "outlet" and not country:
        raise HTTPException(status_code=400, detail="country is required when level='outlet'")

    outlet_list = [o.strip() for o in outlets.split(",") if o.strip()] if outlets else None
    service = StatsService(db)
    data = service.get_topic_similarity(
        level=normalized_level,
        country=country,
        partisan=partisan,
        outlets=outlet_list,
        date_from=date_from,
        date_to=date_to,
        limit_topics=limit_topics,
    )
    return TopicSimilarityResponse(
        filters={
            "level": normalized_level,
            "country": country,
            "partisan": partisan,
            "outlets": outlets,
            "date_from": date_from,
            "date_to": date_to,
            "limit_topics": limit_topics,
        },
        topics=data.get("topics", []),
        entities=data.get("entities", []),
        cosine=[SimilarityValue(**row) for row in data.get("cosine", [])],
        jsd=[SimilarityValue(**row) for row in data.get("jsd", [])],
    )


@router.get("/overview/enhanced")
async def get_enhanced_overview(db: Session = Depends(get_db)):
    """Get enhanced overview with additional metrics (articles per outlet, growth rate, etc.)."""
    service = StatsService(db)
    return service.get_enhanced_overview()


@router.get("/overview/full")
async def get_full_enhanced_overview(db: Session = Depends(get_db)):
    """Get enhanced overview from the full articles dataset."""
    service = StatsService(db)
    return service.get_enhanced_overview_full()


@router.get("/data-freshness")
async def get_data_freshness(db: Session = Depends(get_db)):
    """Get data freshness information (last updated timestamp)."""
    service = StatsService(db)
    return service.get_data_freshness()


@router.get("/outlet-concentration")
async def get_outlet_concentration(
    country: Optional[str] = Query(None, description="Filter by country"),
    db: Session = Depends(get_db)
):
    """Get outlet concentration ratio (top 3 outlets' % of total articles)."""
    service = StatsService(db)
    return service.get_outlet_concentration(country=country)


@router.get("/comparative")
async def get_comparative_metrics(db: Session = Depends(get_db)):
    """Get comparative metrics across countries (concentration, partisan balance, etc.)."""
    service = StatsService(db)
    return service.get_comparative_metrics()
