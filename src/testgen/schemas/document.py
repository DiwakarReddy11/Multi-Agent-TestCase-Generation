"""A parsed SRS: text blocks that remember which page and section they came from."""

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    text: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1, description="PDF page; None for DOCX/Markdown")
    section: str | None = Field(default=None, description="Nearest heading above this text")


class ParsedDocument(BaseModel):
    name: str
    blocks: list[TextBlock] = Field(min_length=1)

    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks)
