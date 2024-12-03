""" Pagination Schema """

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, HttpUrl, validator, conint


# Pagination Model
class Pagination(BaseModel):
    """Pagination schema."""

    page: int = Field(..., description="Current page number.")
    per_page: int = Field(..., description="Number of items per page.")
    total_items: int = Field(..., description="Total number of items.")
    total_pages: int = Field(..., description="Total number of pages.")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {"page": 1, "per_page": 10, "total_items": 50, "total_pages": 5}
        }


class PaginationLink(BaseModel):
    """Pagination link schema."""

    rel: str
    href: HttpUrl
    method: str = "GET"


class EnhancedPagination(Pagination):
    """Enhanced pagination schema with links."""

    links: List[PaginationLink] = []

    def add_link(self, rel: str, href: str):
        """Add a link to the pagination response."""
        self.links.append(PaginationLink(rel=rel, href=href))
