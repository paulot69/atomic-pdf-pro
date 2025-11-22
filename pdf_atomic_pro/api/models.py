from pydantic import BaseModel
from typing import Optional, List

class ProcessRequest(BaseModel):
    row_index: int
    structure_content: Optional[str] = None
    no_ai: bool = False
    translate_to: Optional[str] = None

class BatchProcessRequest(BaseModel):
    no_ai: bool = False
    translate_to: Optional[str] = None

class LogMessage(BaseModel):
    message: str
    level: str = "INFO"

class Book(BaseModel):
    row_index: int
    title: str
    filename: str
    status: str

class BookListResponse(BaseModel):
    books: List[Book]
