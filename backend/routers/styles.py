from fastapi import APIRouter

from models.schemas import StylesResponse

router = APIRouter(tags=["styles"])

AVAILABLE_STYLES = [
    "baroque",
    "renaissance",
    "impressionism",
    "art deco",
    "watercolor",
    "anime",
    "pop art",
    "cubism",
    "minimalist",
    "photorealistic",
    "sketch",
    "oil painting",
    "digital art",
]


@router.get("/styles", response_model=StylesResponse)
async def get_styles():
    """Returns the list of supported art styles."""
    return StylesResponse(styles=AVAILABLE_STYLES)
