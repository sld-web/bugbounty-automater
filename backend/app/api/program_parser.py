from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.services.program_parser import parse_program_policy, parse_program_policy_ai, ParsedProgram

router = APIRouter(prefix="/programs", tags=["programs"])


class ParseProgramRequest(BaseModel):
    policy_text: str
    name: str | None = None
    platform: str = "hackerone"
    use_ai: bool = True


class ParseProgramResponse(BaseModel):
    success: bool
    program: ParsedProgram | None = None
    error: str | None = None
    ai_used: bool = False


@router.post("/parse", response_model=ParseProgramResponse)
async def parse_program(request: ParseProgramRequest) -> ParseProgramResponse:
    """Parse raw program policy text into structured program data using AI."""
    try:
        if request.use_ai:
            parsed = await parse_program_policy_ai(request.policy_text)
            ai_used = parsed.ai_enhanced
        else:
            parsed = parse_program_policy(request.policy_text)
            ai_used = False
        
        if request.name:
            parsed.name = request.name
        if request.platform:
            parsed.platform = request.platform
        
        return ParseProgramResponse(
            success=True,
            program=parsed,
            ai_used=ai_used,
        )
    except Exception as e:
        return ParseProgramResponse(
            success=False,
            error=str(e),
        )


@router.post("/import", response_model=dict)
async def import_program(request: ParseProgramRequest) -> dict:
    """Parse and immediately import a program."""
    try:
        parsed = parse_program_policy(request.policy_text)
        
        if request.name:
            parsed.name = request.name
        
        return {
            "success": True,
            "program": parsed.model_dump(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
