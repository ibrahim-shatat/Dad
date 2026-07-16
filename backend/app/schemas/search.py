from pydantic import BaseModel, Field


class SearchResultRead(BaseModel):
    type: str
    id: str
    title: str
    snippet: str | None
    link: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatSourceRead(BaseModel):
    label: str
    link: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSourceRead]
