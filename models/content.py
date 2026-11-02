from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PageType(str, Enum):
    """Blog post formats. (Field name kept as PageType for compatibility with the
    shared pipeline; every value here is an editorial article, not a landing page.)"""
    HOWTO = "how-to"
    GUIDE = "guide"
    LISTICLE = "listicle"
    OPINION = "opinion"
    COMPARISON = "comparison"   # editorial "X vs Y" article
    ALTERNATIVES = "alternatives"   # "[Competitor] alternatives" post, written from the alternatives playbook
    UPDATE = "update"           # refreshing an existing underperforming post


class ContentStatus(str, Enum):
    DRAFT = "Draft"
    APPROVED = "Approved"
    GENERATING = "Generating"
    STAGED = "Staged"           # created in Sanity as a draft
    PUBLISHED = "Published"
    REJECTED = "Rejected"


class KeywordMetrics(BaseModel):
    keyword: str
    monthly_volume: int = 0
    difficulty: float = 0.0     # 0-100
    current_rank: Optional[int] = None
    current_url: Optional[str] = None
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    avg_position: Optional[float] = None


class CompetitorSignal(BaseModel):
    competitor: str
    competitor_url: str
    keyword: str
    competitor_rank: int
    our_rank: Optional[int] = None
    traffic_delta: Optional[int] = None   # competitor's traffic change (30d)


class ContentOpportunity(BaseModel):
    id: str = ""
    page_type: PageType
    keyword: str
    supporting_keywords: list[str] = Field(default_factory=list)
    monthly_volume: int = 0
    difficulty: float = 0.0
    priority_score: float = 0.0
    proposed_url: str
    proposed_title: str
    rationale: str
    competitor_signal: Optional[CompetitorSignal] = None
    traffic_estimate_90d: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    calendar_row: Optional[int] = None   # 1-based row in the content-calendar sheet (for write-back), if sourced from it
    launch_batch: bool = False            # Launch Batch rows — staged all at once (bulk) into the normal review window
    includes_polymer: bool = False        # Polymer is one of the products the post covers; the feature inventory goes into the prompt
    product_based: bool = False           # the post is about named products; research runs as one call, not the three-step split


class GeneratedContent(BaseModel):
    title: str
    h1: str
    meta_description: str
    slug: str
    main_image_alt: str = ""      # alt text for the post's main image (added in Sanity)
    body_html: str
    faq_items: list[dict] = Field(default_factory=list)   # [{q, a}, ...]
    internal_links: list[dict] = Field(default_factory=list)  # [{text, url}, ...]
    word_count: int = 0
    reading_time_minutes: int = 0


class ContentPage(BaseModel):
    opportunity: ContentOpportunity
    status: ContentStatus = ContentStatus.DRAFT
    sanity_document_id: str = ""
    research_brief: str = ""
    sanity_draft_url: str = ""
    live_url: str = ""
    content: Optional[GeneratedContent] = None
    todos: list[dict] = Field(default_factory=list)   # [{item, done}] — internal-link shortfalls for the follow-up run; done = ISO date when handled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    rejection_reason: str = ""
