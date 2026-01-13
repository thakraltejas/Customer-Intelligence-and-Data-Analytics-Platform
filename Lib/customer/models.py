from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --------------------- USER MODEL ---------------------
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# --------------------- USER MODEL ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    # One user can have many borrow records
    borrowed_books = db.relationship('BorrowRecord', back_populates='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# --------------------- BOOK MODEL ---------------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)

    # One book can have many borrow records
    borrow_records = db.relationship('BorrowRecord', back_populates='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.title}>'


# --------------------- BORROW RECORD MODEL ---------------------
class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrow_date = db.Column(db.String(20))
    return_date = db.Column(db.String(20), nullable=True)
    returned = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', back_populates='borrowed_books')
    book = db.relationship('Book', back_populates='borrow_records')

    def __repr__(self):
        return f'<BorrowRecord {self.id}>'


