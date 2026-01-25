"""Service for article search and retrieval."""

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def normalize_outlets(outlets: List[str]) -> List[str]:
    return [outlet.strip().lower() for outlet in outlets if outlet and outlet.strip()]


class ArticlesService:
    """Service for querying articles."""

    def __init__(self, db: Session):
        self.db = db

    def search_articles(
        self,
        query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        country: Optional[str] = None,
        partisan: Optional[str] = None,
        sentiment: Optional[str] = None,
        categories: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
        outlets: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        conditions = ["date IS NOT NULL"]
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if query:
            conditions.append(
                "(title ILIKE :query OR description ILIKE :query OR content ILIKE :query)"
            )
            params["query"] = f"%{query}%"

        if date_from:
            conditions.append("date >= :date_from")
            params["date_from"] = date_from

        if date_to:
            conditions.append("date <= :date_to")
            params["date_to"] = date_to

        if country:
            conditions.append("country = :country")
            params["country"] = country

        if partisan:
            conditions.append("partisan = :partisan")
            params["partisan"] = partisan

        if sentiment:
            conditions.append("sentiment = :sentiment")
            params["sentiment"] = sentiment

        if outlets:
            normalized_outlets = normalize_outlets(outlets)
            if normalized_outlets:
                conditions.append("LOWER(domain) = ANY(:outlets)")
                params["outlets"] = normalized_outlets

        if entities:
            conditions.append("entities_json::text ILIKE :entities")
            params["entities"] = f"%{entities[0]}%"

        # Categories handling: support either category column or JSONB categories
        categories_clause = ""
        if categories:
            check_query = text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='articles' AND column_name='category'"
            )
            has_category_column = self.db.execute(check_query).fetchone() is not None
            if has_category_column:
                categories_clause = "category = ANY(:categories)"
                params["categories"] = categories
            else:
                categories_clause = (
                    "EXISTS (SELECT 1 FROM jsonb_array_elements_text(categories) AS cat "
                    "WHERE cat = ANY(:categories))"
                )
                params["categories"] = categories

        if categories_clause:
            conditions.append(categories_clause)

        where_clause = " AND ".join(conditions)

        total_query = text(f"""
            SELECT COUNT(*)
            FROM clean_articles
            WHERE {where_clause}
        """)
        total = self.db.execute(total_query, params).scalar() or 0

        data_query = text(f"""
            SELECT
                id,
                title,
                url,
                date,
                domain,
                country,
                partisan,
                sentiment,
                sentiment_score,
                description,
                content,
                categories,
                entities_json
            FROM clean_articles
            WHERE {where_clause}
            ORDER BY date DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """)
        rows = self.db.execute(data_query, params).fetchall()

        articles = []
        for row in rows:
            articles.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "date": str(row[3]) if row[3] else None,
                    "domain": row[4],
                    "country": row[5],
                    "partisan": row[6],
                    "sentiment": row[7],
                    "sentiment_score": float(row[8]) if row[8] is not None else None,
                    "description": row[9],
                    "content": row[10],
                    "categories": row[11] or [],
                    "entities": row[12] or {},
                }
            )

        return {"total": total, "articles": articles}
