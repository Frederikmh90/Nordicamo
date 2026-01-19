"""Statistics service for computing analytics."""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StatsService:
    """Service for computing statistics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_overview(self) -> Dict:
        """Get overview statistics."""
        query = text("""
            SELECT 
                COUNT(*) as total_articles,
                COUNT(DISTINCT domain) as total_outlets,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM clean_articles
            WHERE date IS NOT NULL
        """)
        result = self.db.execute(query).fetchone()
        
        # Get country distribution
        country_query = text("""
            SELECT country, COUNT(*) as count
            FROM clean_articles
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
        """)
        country_results = self.db.execute(country_query).fetchall()
        by_country = {row[0]: row[1] for row in country_results}
        
        # Get partisan distribution
        partisan_query = text("""
            SELECT partisan, COUNT(*) as count
            FROM clean_articles
            WHERE partisan IS NOT NULL
            GROUP BY partisan
            ORDER BY count DESC
        """)
        partisan_results = self.db.execute(partisan_query).fetchall()
        by_partisan = {row[0]: row[1] for row in partisan_results}
        
        return {
            "total_articles": result[0] or 0,
            "total_outlets": result[1] or 0,
            "date_range": {
                "earliest": str(result[2]) if result[2] else None,
                "latest": str(result[3]) if result[3] else None
            },
            "by_country": by_country,
            "by_partisan": by_partisan
        }
    
    def get_articles_by_country(
        self,
        partisan: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get article counts by country with optional filters."""
        conditions = ["country IS NOT NULL"]
        params = {}
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        if date_from:
            conditions.append("date >= :date_from")
            params["date_from"] = date_from
        
        if date_to:
            conditions.append("date <= :date_to")
            params["date_to"] = date_to
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT country, COUNT(*) as count
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY country
            ORDER BY count DESC
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [{"country": row[0], "count": row[1]} for row in results]
    
    def get_articles_over_time(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None,
        granularity: str = "month",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get time series data for articles."""
        conditions = ["date IS NOT NULL"]
        params = {}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        if date_from:
            conditions.append("date >= :date_from")
            params["date_from"] = date_from
        
        if date_to:
            conditions.append("date <= :date_to")
            params["date_to"] = date_to
        
        where_clause = " AND ".join(conditions)
        
        # Determine date format based on granularity
        if granularity == "year":
            date_format = "TO_CHAR(date, 'YYYY')"
            group_by = "TO_CHAR(date, 'YYYY')"
        elif granularity == "month":
            date_format = "TO_CHAR(date, 'YYYY-MM')"
            group_by = "TO_CHAR(date, 'YYYY-MM')"
        elif granularity == "week":
            date_format = "TO_CHAR(date, 'IYYY-IW')"
            group_by = "TO_CHAR(date, 'IYYY-IW')"
        else:  # day
            date_format = "TO_CHAR(date, 'YYYY-MM-DD')"
            group_by = "TO_CHAR(date, 'YYYY-MM-DD')"
        
        query = text(f"""
            SELECT 
                {date_format} as date,
                COUNT(*) as count
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY {group_by}
            ORDER BY date
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [{"date": str(row[0]), "count": row[1]} for row in results]
    
    def get_top_outlets(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get top outlets by article count."""
        conditions = ["domain IS NOT NULL"]
        params = {"limit": limit}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                domain,
                actor as outlet_name,
                country,
                partisan,
                COUNT(*) as count
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY domain, actor, country, partisan
            ORDER BY count DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [
            {
                "domain": row[0],
                "outlet_name": row[1],
                "country": row[2],
                "partisan": row[3],
                "count": row[4]
            }
            for row in results
        ]

    def get_outlet_profile(self, domain: str) -> Optional[Dict]:
        """Get outlet profile summary by domain."""
        query = text("""
            SELECT
                domain,
                actor as outlet_name,
                country,
                COUNT(*) as total_articles,
                MIN(date) as first_article_date,
                MAX(date) as last_article_date
            FROM clean_articles
            WHERE domain = :domain
            GROUP BY domain, actor, country
        """)
        result = self.db.execute(query, {"domain": domain}).fetchone()
        if not result:
            return None
        return {
            "domain": result[0],
            "outlet_name": result[1],
            "country": result[2],
            "total_articles": result[3],
            "first_article_date": str(result[4]) if result[4] else None,
            "last_article_date": str(result[5]) if result[5] else None,
        }
    
    def get_categories_distribution(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None
    ) -> List[Dict]:
        """Get distribution of categories."""
        # Check if category column exists (newer format)
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='articles' AND column_name='category'
        """)
        has_category_column = self.db.execute(check_query).fetchone() is not None
        
        if has_category_column:
            # Use category column (simpler and faster)
            conditions = ["category IS NOT NULL"]
            params = {}
            
            if country:
                conditions.append("country = :country")
                params["country"] = country
            
            if partisan:
                conditions.append("partisan = :partisan")
                params["partisan"] = partisan
            
            where_clause = " AND ".join(conditions)
            
            query = text(f"""
                SELECT 
                    category,
                    COUNT(*) as count
                FROM clean_articles
                WHERE {where_clause}
                GROUP BY category
                ORDER BY count DESC
            """)
        else:
            # Fallback to categories JSONB column
            conditions = ["categories IS NOT NULL"]
            params = {}
            
            if country:
                conditions.append("country = :country")
                params["country"] = country
            
            if partisan:
                conditions.append("partisan = :partisan")
                params["partisan"] = partisan
            
            where_clause = " AND ".join(conditions)
            
            query = text(f"""
                SELECT 
                    jsonb_array_elements_text(categories) as category,
                    COUNT(*) as count
                FROM clean_articles
                WHERE {where_clause}
                GROUP BY category
                ORDER BY count DESC
            """)
        
        results = self.db.execute(query, params).fetchall()
        return [{"category": row[0], "count": row[1]} for row in results]
    
    def get_sentiment_distribution(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None
    ) -> List[Dict]:
        """Get sentiment distribution."""
        conditions = ["sentiment IS NOT NULL"]
        params = {}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                sentiment,
                COUNT(*) as count,
                AVG(sentiment_score) as avg_score
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY sentiment
            ORDER BY count DESC
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [
            {
                "sentiment": row[0],
                "count": row[1],
                "avg_score": float(row[2]) if row[2] else 0.0
            }
            for row in results
        ]
    
    def get_top_entities(
        self,
        entity_type: str = "persons",  # persons, locations, organizations
        country: Optional[str] = None,
        partisan: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get top entities by type."""
        conditions = [
            "entities_json IS NOT NULL",
            f"entities_json ? '{entity_type}'",
            f"jsonb_array_length(entities_json->'{entity_type}') > 0"
        ]
        params = {"limit": limit, "entity_type": entity_type}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        where_clause = " AND ".join(conditions)
        
        # Extract entities and count occurrences
        # Note: entity_type is validated before this function is called
        query = text(f"""
            WITH entity_extract AS (
                SELECT 
                    jsonb_array_elements(entities_json->'{entity_type}') as entity_data
                FROM clean_articles
                WHERE {where_clause}
            )
            SELECT 
                entity_data->>'name' as entity_name,
                COUNT(*) as count,
                COUNT(CASE WHEN entity_data->>'sentiment' = 'positive' THEN 1 END) as positive_count,
                COUNT(CASE WHEN entity_data->>'sentiment' = 'negative' THEN 1 END) as negative_count,
                COUNT(CASE WHEN entity_data->>'sentiment' = 'neutral' OR entity_data->>'sentiment' = 'none' THEN 1 END) as neutral_count
            FROM entity_extract
            WHERE entity_data->>'name' IS NOT NULL
            GROUP BY entity_data->>'name'
            ORDER BY count DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [
            {
                "entity_name": row[0],
                "count": row[1],
                "positive_count": row[2],
                "negative_count": row[3],
                "neutral_count": row[4]
            }
            for row in results
        ]
    
    def get_entity_statistics(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None
    ) -> Dict:
        """Get overall entity statistics."""
        conditions = ["entities_json IS NOT NULL"]
        params = {}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT 
                COUNT(*) FILTER (WHERE entities_json ? 'persons' AND jsonb_array_length(entities_json->'persons') > 0) as articles_with_persons,
                COUNT(*) FILTER (WHERE entities_json ? 'locations' AND jsonb_array_length(entities_json->'locations') > 0) as articles_with_locations,
                COUNT(*) FILTER (WHERE entities_json ? 'organizations' AND jsonb_array_length(entities_json->'organizations') > 0) as articles_with_organizations,
                COUNT(*) as total_articles
            FROM clean_articles
            WHERE {where_clause}
        """)
        
        result = self.db.execute(query, params).fetchone()
        
        return {
            "total_articles": result[3] or 0,
            "articles_with_persons": result[0] or 0,
            "articles_with_locations": result[1] or 0,
            "articles_with_organizations": result[2] or 0,
            "coverage": {
                "persons": (result[0] / result[3] * 100) if result[3] and result[3] > 0 else 0,
                "locations": (result[1] / result[3] * 100) if result[3] and result[3] > 0 else 0,
                "organizations": (result[2] / result[3] * 100) if result[3] and result[3] > 0 else 0
            }
        }
    
    def get_data_freshness(self) -> Dict:
        """Get data freshness information (last updated timestamp)."""
        query = text("""
            SELECT 
                MAX(date) as last_article_date,
                MAX(updated_at) as last_updated
            FROM clean_articles
        """)
        result = self.db.execute(query).fetchone()
        
        last_article_date = result[0] if result[0] else None
        last_updated = result[1] if result[1] else None
        
        # Calculate hours ago if we have a timestamp
        hours_ago = None
        if last_updated:
            try:
                if isinstance(last_updated, str):
                    last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                else:
                    last_updated_dt = last_updated
                now = datetime.now(last_updated_dt.tzinfo) if last_updated_dt.tzinfo else datetime.now()
                delta = now - last_updated_dt
                hours_ago = int(delta.total_seconds() / 3600)
            except Exception:
                pass
        
        return {
            "last_article_date": str(last_article_date) if last_article_date else None,
            "last_updated": str(last_updated) if last_updated else None,
            "hours_ago": hours_ago
        }
    
    def get_enhanced_overview(self) -> Dict:
        """Get enhanced overview with additional metrics."""
        base_overview = self.get_overview()
        
        # Get articles per outlet average
        query = text("""
            SELECT 
                COUNT(*)::float / NULLIF(COUNT(DISTINCT domain), 0) as avg_articles_per_outlet
            FROM clean_articles
            WHERE domain IS NOT NULL
        """)
        result = self.db.execute(query).fetchone()
        avg_articles_per_outlet = float(result[0]) if result[0] else 0.0
        
        # Get growth rate (articles per year trend)
        growth_query = text("""
            SELECT 
                TO_CHAR(date, 'YYYY') as year,
                COUNT(*) as count
            FROM clean_articles
            WHERE date IS NOT NULL
            GROUP BY TO_CHAR(date, 'YYYY')
            ORDER BY year
        """)
        growth_results = self.db.execute(growth_query).fetchall()
        
        # Calculate average growth rate
        growth_rate = None
        if len(growth_results) >= 2:
            years = [int(row[0]) for row in growth_results]
            counts = [row[1] for row in growth_results]
            if len(years) > 1:
                # Simple linear regression slope
                n = len(years)
                sum_x = sum(years)
                sum_y = sum(counts)
                sum_xy = sum(years[i] * counts[i] for i in range(n))
                sum_x2 = sum(x * x for x in years)
                
                denominator = n * sum_x2 - sum_x * sum_x
                if denominator != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / denominator
                    growth_rate = round(slope, 1)
        
        # Get date range for coverage display
        dr = base_overview.get("date_range", {})
        earliest = dr.get("earliest")
        latest = dr.get("latest")
        coverage_years = None
        if earliest and latest:
            try:
                earliest_year = int(str(earliest)[:4])
                latest_year = int(str(latest)[:4])
                coverage_years = f"{earliest_year}-{latest_year}"
            except Exception:
                pass
        
        return {
            **base_overview,
            "avg_articles_per_outlet": round(avg_articles_per_outlet, 1),
            "growth_rate_per_year": growth_rate,
            "coverage_years": coverage_years
        }
    
    def get_outlet_concentration(self, country: Optional[str] = None) -> Dict:
        """Get outlet concentration ratio (top 3 outlets' % of total articles)."""
        conditions = ["domain IS NOT NULL"]
        params = {}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        where_clause = " AND ".join(conditions)
        
        # Get total articles for the country/filter
        total_query = text(f"""
            SELECT COUNT(*) as total
            FROM clean_articles
            WHERE {where_clause}
        """)
        total_result = self.db.execute(total_query, params).fetchone()
        total_articles = total_result[0] if total_result[0] else 0
        
        # Get top 3 outlets
        top_outlets_query = text(f"""
            SELECT 
                domain,
                country,
                COUNT(*) as count
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY domain, country
            ORDER BY count DESC
            LIMIT 3
        """)
        top_outlets = self.db.execute(top_outlets_query, params).fetchall()
        
        # Calculate concentration
        top3_total = sum(row[2] for row in top_outlets)
        concentration_pct = (top3_total / total_articles * 100) if total_articles > 0 else 0
        
        outlets_detail = [
            {
                "domain": row[0],
                "country": row[1],
                "count": row[2],
                "percentage": round((row[2] / total_articles * 100), 1) if total_articles > 0 else 0
            }
            for row in top_outlets
        ]
        
        return {
            "total_articles": total_articles,
            "top3_articles": top3_total,
            "concentration_percentage": round(concentration_pct, 1),
            "outlets": outlets_detail
        }
    
    def get_comparative_metrics(self) -> Dict:
        """Get comparative metrics across countries."""
        countries = ["denmark", "sweden", "norway", "finland"]
        comparative = {}
        
        for country in countries:
            # Get outlet concentration for each country
            concentration = self.get_outlet_concentration(country=country)
            
            # Get partisan balance
            partisan_query = text("""
                SELECT 
                    partisan,
                    COUNT(*) as count
                FROM clean_articles
                WHERE country = :country AND partisan IS NOT NULL
                GROUP BY partisan
            """)
            partisan_results = self.db.execute(partisan_query, {"country": country}).fetchall()
            
            partisan_counts = {row[0]: row[1] for row in partisan_results}
            right_count = partisan_counts.get("Right", 0)
            left_count = partisan_counts.get("Left", 0)
            total_partisan = right_count + left_count
            
            # Calculate partisan balance ratio
            partisan_ratio = None
            if total_partisan > 0:
                partisan_ratio = round((right_count / total_partisan) * 100, 1)
            
            comparative[country] = {
                "outlet_concentration": concentration["concentration_percentage"],
                "partisan_balance": {
                    "right_percentage": partisan_ratio,
                    "right_count": right_count,
                    "left_count": left_count
                },
                "top_outlets": concentration["outlets"]
            }
        
        return comparative
