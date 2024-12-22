from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# CORS settings
origins = [
    "http://localhost",
    "http://127.0.0.1:5500"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up the database URL (adjust this to match your MySQL credentials)
DATABASE_URL = "mysql+pymysql://root@localhost:3306/librarydb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Association table for many-to-many relationship between Books and Authors
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

# Define the Book model
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(13), unique=True)
    
    # Relationship to authors through the association table
    authors = relationship("Author", secondary="book_authors", back_populates="books")

# Define the Author model
class Author(Base):
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Relationship to books through the association table
    books = relationship("Book", secondary="book_authors", back_populates="authors")

# Create the tables
Base.metadata.create_all(bind=engine)

# Dependency to handle database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints for Books
@app.post("/books/")
def create_book(book: dict = Body(...), db: Session = Depends(get_db)):
    title = book.get("title")
    isbn = book.get("isbn")
    
    if not title or not isbn:
        raise HTTPException(status_code=400, detail="Title and ISBN are required")
    
    new_book = Book(title=title, isbn=isbn)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    
    return {"id": new_book.id, "title": new_book.title, "isbn": new_book.isbn}

@app.post("/authors/")
def create_author(author: dict = Body(...), db: Session = Depends(get_db)):
    name = author.get("name")
    
    if not name:
        raise HTTPException(status_code=400, detail="Author name is required")
    
    new_author = Author(name=name)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    
    return {"id": new_author.id, "name": new_author.name}

@app.post("/books/add-author/")
def add_author_to_book(data: dict = Body(...), db: Session = Depends(get_db)):
    book_id = data.get("book_id")
    author_id = data.get("author_id")
    
    if not book_id or not author_id:
        raise HTTPException(status_code=400, detail="Book ID and Author ID are required")
    
    book = db.query(Book).filter(Book.id == book_id).first()
    author = db.query(Author).filter(Author.id == author_id).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # Check if the author is already associated with the book
    if author not in book.authors:
        book.authors.append(author)
        db.commit()
    
    return {"message": f"Author {author.name} added to book {book.title}"}

@app.get("/books/{book_id}/authors/")
def get_book_authors(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return [{"id": author.id, "name": author.name} for author in book.authors]

@app.get("/authors/{author_id}/books/")
def get_author_books(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.id == author_id).first()
    
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return [{"id": book.id, "title": book.title, "isbn": book.isbn} for book in author.books]

@app.get("/books/")
def get_all_books(db: Session = Depends(get_db)):
    books = db.query(Book).all()
    return [
        {
            "id": book.id, 
            "title": book.title, 
            "isbn": book.isbn, 
            "authors": [{"id": author.id, "name": author.name} for author in book.authors]
        } 
        for book in books
    ]

@app.get("/authors/")
def get_all_authors(db: Session = Depends(get_db)):
    authors = db.query(Author).all()
    return [
        {
            "id": author.id, 
            "name": author.name, 
            "books": [{"id": book.id, "title": book.title, "isbn": book.isbn} for book in author.books]
        } 
        for author in authors
    ]