from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import csv
import io

import models, schemas
from database import engine, get_db, logs_collection

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="LibTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "LibTrack System Online"}
# --- BOOK ROUTES ---

@app.get("/books", response_model=list[schemas.BookResponse], tags=["Books"])
def get_all_books(db: Session = Depends(get_db)):
    return db.query(models.Book).all()

@app.post("/books", response_model=schemas.BookResponse, tags=["Books"])
def create_book(book: schemas.BookBase, db: Session = Depends(get_db)):
    db_book = models.Book(**book.model_dump(), available_copies=book.total_copies)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

# --- STUDENT ROUTES ---

@app.get("/students", tags=["Students"])
def get_all_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()

@app.post("/students", tags=["Students"])
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

# --- CSV BOOK UPLOAD ---
@app.post("/books/upload", tags=["Inventory"])
async def upload_books_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    decoded = content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(decoded))

    added_count = 0
    for row in reader:
        existing_book = db.query(models.Book).filter(models.Book.isbn == row['isbn']).first()
        if not existing_book:
            new_book = models.Book(
                isbn=row['isbn'], title=row['title'], author=row['author'],
                total_copies=int(row['total_copies']), available_copies=int(row['total_copies'])
            )
            db.add(new_book)
            added_count += 1

    db.commit()

    # Push to MongoDB
    logs_collection.insert_one({
        "action": "UPLOAD",
        "details": f"Uploaded {added_count} new books via CSV.",
        "timestamp": datetime.utcnow()
    })

    return {"message": f"Successfully added {added_count} new books."}


# --- BORROW & RETURN LOGIC ---
@app.post("/borrow", response_model=schemas.BorrowResponse, tags=["Transactions"])
def borrow_book(request: schemas.BorrowRequest, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.admission_number == request.admission_number).first()
    if not student:
        # Auto-create dummy student for testing if none exists
        student = models.Student(admission_number=request.admission_number, name="Test Student",
                                 email=f"{request.admission_number}@test.com")
        db.add(student)
        db.commit()
        db.refresh(student)

    book = db.query(models.Book).filter(models.Book.id == request.book_id).first()
    if not book or book.available_copies < 1:
        raise HTTPException(status_code=400, detail="Book not available")

    book.available_copies -= 1
    new_record = models.BorrowRecord(student_id=student.id, book_id=book.id)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # Push to MongoDB
    logs_collection.insert_one({
        "action": "BORROW",
        "details": f"Student {student.admission_number} borrowed Book ID {book.id}",
        "timestamp": datetime.utcnow()
    })

    return schemas.BorrowResponse(message="Book borrowed successfully", record_id=new_record.id,
                                  due_date=new_record.due_date)


# --- UPDATE & DELETE BOOKS ---

@app.put("/books/{book_id}", tags=["Books"])
def update_book(book_id: int, book_data: schemas.BookBase, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Update fields
    for key, value in book_data.model_dump().items():
        setattr(db_book, key, value)

    db.commit()
    return {"message": "Book updated successfully"}


@app.delete("/books/{book_id}", tags=["Books"])
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully"}


# --- UPDATE & DELETE STUDENTS ---

@app.put("/students/{student_id}", tags=["Students"])
def update_student(student_id: int, student_data: schemas.StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in student_data.model_dump().items():
        setattr(db_student, key, value)

    db.commit()
    return {"message": "Student updated successfully"}


@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(db_student)
    db.commit()
    return {"message": "Student deleted successfully"}

# --- MongoDB LOGS ---
@app.get("/logs", tags=["System Logs"])
def get_audit_logs():
    # Fetch from Mongo and convert ObjectId to string so FastAPI can return it
    logs = list(logs_collection.find().sort("timestamp", -1).limit(50))
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs