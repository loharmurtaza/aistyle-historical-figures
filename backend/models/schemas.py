from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Request models ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    figure: str = Field(
        ..., min_length=2, description="Historical figure name or description"
    )
    style: Optional[str] = Field(
        None, description="Desired art style; omit to let the AI choose"
    )
    user_prompt: Optional[str] = Field(
        None, description="Optional extra context from the user"
    )
    session_id: Optional[str] = Field(
        None, description="Session ID for history-aware generation"
    )
    enhance: bool = Field(
        True,
        description=(
            "True = AI freely enhances the prompt with creative details. "
            "False = AI only formats/structures the prompt without adding "
            "new ideas."
        ),
    )


class EnhancePromptRequest(BaseModel):
    figure: str = Field(..., min_length=2)
    style: str = Field(..., min_length=2)
    user_prompt: Optional[str] = None


# ── Response models ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    openai_connected: bool


class EnhancePromptResponse(BaseModel):
    enhanced_prompt: str
    figure: str
    style: str


class GenerateResponse(BaseModel):
    image_url: str
    revised_prompt: str
    enhanced_prompt: str
    figure: str
    figure_title: str
    style: str


# ── Gallery models ──────────────────────────────────────────────

class GalleryItem(BaseModel):
    id: int
    figure: str
    style: str
    prompt: str
    enhanced_prompt: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GalleryResponse(BaseModel):
    items: list[GalleryItem]
    total: int
    page: int
    page_size: int


class StylesResponse(BaseModel):
    styles: list[str]


class StatsResponse(BaseModel):
    portraits_created: int
    unique_figures: int
    styles_available: int


# ── Figures models ───────────────────────────────────────────────

class FigureItem(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    born_year: Optional[int]
    died_year: Optional[int]
    era: Optional[str]
    origin: Optional[str]
    tags: Optional[str]
    featured: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FiguresResponse(BaseModel):
    items: list[FigureItem]
    total: int
    page: int
    page_size: int


class FiguresMetaResponse(BaseModel):
    eras: list[str]
    origins: list[str]
    tags: list[str]


class FigureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    born_year: Optional[int] = None
    died_year: Optional[int] = None
    era: Optional[str] = Field(None, max_length=100)
    origin: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    featured: bool = False
