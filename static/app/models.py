from typing import Optional, List
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    story_prompt: str = Field(..., min_length=3)
    character_name: str = Field(default="Alex")
    setting: str = Field(default="Fantasy Forest")
    tone: str = Field(default="Funny")
    art_style: str = Field(default="Comic Book")
    panel_count: int = Field(default=5, ge=1, le=8)


class Panel(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str
    caption: str = ""
    narration: str = ""
    dialogue: str = ""
    image_path: Optional[str] = None


class ComicResponse(BaseModel):
    title: str
    panels: List[Panel]
    pdf_path: Optional[str] = None