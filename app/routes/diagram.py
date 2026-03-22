# app/routes/diagram.py
import os
from typing import Optional, Tuple

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from app.utils.zip_handler import extract_zip
from app.services.parser_service import parse_dotnet_project
from app.services.mermaid_builder import build_mermaid
from app.services.claude_service import generate_mermaid_with_claude

router = APIRouter()


class GenerateDiagramBody(BaseModel):
    architecture: dict
    selected_controller: Optional[str] = None
    detail_level: str = "medium"


async def _mermaid_for_architecture(
    architecture: dict,
    selected_controller: Optional[str],
    detail_level: str,
) -> Tuple[str, str]:
    """
    Returns (mermaid_source, source_label) where source_label is 'claude' or 'rules'.
    """
    use_ai = os.environ.get("USE_AI_DIAGRAM", "true").lower() in ("1", "true", "yes")
    if use_ai:
        try:
            mermaid = await generate_mermaid_with_claude(
                architecture,
                detail_level=detail_level,
                selected_controller=selected_controller,
            )
            return mermaid, "claude"
        except Exception:
            pass
    return (
        build_mermaid(architecture, selected_controller),
        "rules",
    )


@router.post("/generate-from-zip")
async def generate_from_zip(
    file: UploadFile = File(...),
    selected_controller: Optional[str] = Form(None),
    detail_level: str = Form("medium"),
):
    zip_path = f"temp_{file.filename}"
    with open(zip_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_path = extract_zip(zip_path)

    architecture, controllers_sorted = parse_dotnet_project(extracted_path)

    mermaid, diagram_source = await _mermaid_for_architecture(
        architecture,
        selected_controller if selected_controller else None,
        detail_level,
    )

    return {
        "architecture": architecture,
        "controllers_sorted": controllers_sorted,
        "mermaid": mermaid,
        "diagram_source": diagram_source,
    }


@router.post("/generate-diagram")
async def generate_diagram(body: GenerateDiagramBody):
    """Regenerate diagram from cached architecture (no ZIP re-upload)."""
    mermaid, diagram_source = await _mermaid_for_architecture(
        body.architecture,
        body.selected_controller,
        body.detail_level,
    )
    return {"mermaid": mermaid, "diagram_source": diagram_source}
