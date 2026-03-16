from fastapi import APIRouter, HTTPException

from models.schemas import EnhancePromptRequest, EnhancePromptResponse
from services.prompt_builder import enhance_prompt

router = APIRouter(tags=["prompts"])


@router.post("/enhance-prompt", response_model=EnhancePromptResponse)
async def enhance_prompt_endpoint(request: EnhancePromptRequest):
    """
    Accepts a figure + style (+ optional user_prompt) and returns a
    GPT-4o-mini enhanced DALL·E 3 prompt via the LangChain LCEL chain.
    """
    try:
        enhanced = await enhance_prompt(
            figure=request.figure,
            style=request.style,
            user_prompt=request.user_prompt or "",
        )
        return EnhancePromptResponse(
            enhanced_prompt=enhanced,
            figure=request.figure,
            style=request.style,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
