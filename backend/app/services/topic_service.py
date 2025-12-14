"""Topic modeling service for analyzing article topics."""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TopicService:
    """Service for topic modeling analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_topic_distribution(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get topic distribution."""
        conditions = ["topic_id IS NOT NULL"]
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
        
        query = text(f"""
            SELECT 
                topic_id,
                COUNT(*) as count,
                AVG(topic_probability) as avg_probability
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY topic_id
            ORDER BY count DESC
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [
            {
                "topic_id": int(row[0]),
                "count": row[1],
                "avg_probability": float(row[2]) if row[2] else 0.0
            }
            for row in results
        ]
    
    def get_topics_over_time(
        self,
        topic_id: Optional[int] = None,
        country: Optional[str] = None,
        granularity: str = "month",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict]:
        """Get topic distribution over time."""
        conditions = ["topic_id IS NOT NULL", "date IS NOT NULL"]
        params = {}
        
        if topic_id is not None:
            conditions.append("topic_id = :topic_id")
            params["topic_id"] = topic_id
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
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
                topic_id,
                COUNT(*) as count
            FROM clean_articles
            WHERE {where_clause}
            GROUP BY {group_by}, topic_id
            ORDER BY date, count DESC
        """)
        
        results = self.db.execute(query, params).fetchall()
        return [
            {
                "date": str(row[0]),
                "topic_id": int(row[1]),
                "count": row[2]
            }
            for row in results
        ]
    
    def get_topic_statistics(
        self,
        country: Optional[str] = None,
        partisan: Optional[str] = None
    ) -> Dict:
        """Get overall topic statistics."""
        conditions = []
        params = {}
        
        if country:
            conditions.append("country = :country")
            params["country"] = country
        
        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = text(f"""
            SELECT 
                COUNT(*) FILTER (WHERE topic_id IS NOT NULL) as articles_with_topics,
                COUNT(DISTINCT topic_id) FILTER (WHERE topic_id IS NOT NULL) as unique_topics,
                COUNT(*) as total_articles,
                AVG(topic_probability) FILTER (WHERE topic_probability IS NOT NULL) as avg_probability
            FROM clean_articles
            WHERE {where_clause}
        """)
        
        result = self.db.execute(query, params).fetchone()
        
        return {
            "total_articles": result[2] or 0,
            "articles_with_topics": result[0] or 0,
            "unique_topics": result[1] or 0,
            "avg_probability": float(result[3]) if result[3] else 0.0,
            "coverage": (result[0] / result[2] * 100) if result[2] and result[2] > 0 else 0.0
        }

