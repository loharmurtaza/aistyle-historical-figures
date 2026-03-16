import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from openai import BadRequestError
from sqlalchemy.orm import Session

from database import get_db
from logger import get_logger
from models.schemas import GenerateRequest, GenerateResponse
from rate_limit import limiter
from services.image_generator import ContentPolicyError, generate_portrait
from services.gallery import save_portrait

router = APIRouter(tags=["generate"])
logger = get_logger(__name__)


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit("10/minute")
async def generate_endpoint(
    request: Request,
    body: GenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Full pipeline: GPT-4o-mini enhances the prompt, DALL·E 3 generates the
    portrait, then the result is auto-saved to the gallery.
    Pass session_id to enable history-aware generation.
    """
    logger.info(
        "Generate request — figure=%r  style=%r  user_prompt=%r",
        body.figure,
        body.style or "(none — AI will decide)",
        (body.user_prompt or "")[:120],
    )

    try:
        result = await generate_portrait(
            figure=body.figure,
            style=body.style or "",
            user_prompt=body.user_prompt or "",
            session_id=body.session_id,
            enhance=body.enhance,
        )
    except (BadRequestError, ContentPolicyError) as e:
        detail = e.message if hasattr(e, "message") else str(e)
        raise HTTPException(
            status_code=400,
            detail=f"Content policy violation: {detail}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    figure_title = result["figure_title"]
    resolved_style = result["resolved_style"]

    # Download image bytes so we can serve them from DB (CDN URLs expire)
    image_data: bytes | None = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(result["image_url"])
            resp.raise_for_status()
            image_data = resp.content
    except Exception as exc:
        logger.warning("Could not download image for storage: %s", exc)

    # Auto-save every successful generation to the gallery
    save_portrait(
        db=db,
        figure=figure_title,
        style=resolved_style,
        prompt=body.figure,
        enhanced_prompt=result["enhanced_prompt"],
        image_url=result["image_url"],
        image_data=image_data,
    )

    return GenerateResponse(
        image_url=result["image_url"],
        enhanced_prompt=result["enhanced_prompt"],
        revised_prompt=result["enhanced_prompt"],
        figure=body.figure,
        figure_title=figure_title,
        style=resolved_style,
    )
