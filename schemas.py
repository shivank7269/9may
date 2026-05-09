from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class BookBase(BaseModel):
    isbn: str
    title: str
    author: str
    total_copies: int

class BookResponse(BookBase):
    id: int
    available_copies: int
    model_config = {"from_attributes": True}

class StudentCreate(BaseModel):
    admission_number: str
    name: str
    email: EmailStr
    phone_number: str

class BorrowRequest(BaseModel):
    admission_number: str
    book_id: int

class BorrowResponse(BaseModel):
    message: str
    record_id: int
    due_date: datetime