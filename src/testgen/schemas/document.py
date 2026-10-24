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


class Chunk(BaseModel):
    """A piece of a TextBlock, sized for embedding and for LLM context."""

    id: str
    document: str
    index: int = Field(ge=0, description="Position of the chunk within its document")
    text: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    section: str | None = None

    @property
    def text_for_embedding(self) -> str:
        # The heading gives short chunks context: "Loans are limited to 5" alone
        # says nothing about borrowing, but "2.3 Borrowing and Returns" does.
        return f"{self.section}\n{self.text}" if self.section else self.text
