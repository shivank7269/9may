from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from database import Base

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String, unique=True, index=True)
    title = Column(String)
    author = Column(String)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)

    records = relationship("BorrowRecord", back_populates="book")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String, unique=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)

    records = relationship("BorrowRecord", back_populates="student")

class BorrowRecord(Base):
    __tablename__ = "borrow_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    borrow_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    return_date = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="records")
    book = relationship("Book", back_populates="records")