from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "rishabh_secret_key"

# --------------------- DATABASE SETUP ---------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --------------------- MODELS ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    borrowed_books = db.relationship('BorrowRecord', back_populates='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)
    borrow_records = db.relationship('BorrowRecord', back_populates='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.title}>'

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrow_date = db.Column(db.String(20))
    return_date = db.Column(db.String(20), nullable=True)
    returned = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='borrowed_books')
    book = db.relationship('Book', back_populates='borrow_records')

    def __repr__(self):
        return f'<BorrowRecord {self.id}>'

# --------------------- ADMIN CREDENTIALS ---------------------
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

# --------------------- ROUTES ---------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('sign_up'))
        db.session.add(User(username=username, email=email, password=password))
        db.session.commit()
        flash("Sign Up Successful! You can now login.", "success")
        return redirect(url_for('login'))
    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Admin login
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_id'] = 'admin'
            session['username'] = 'Admin'
            session['is_admin'] = True
            flash("Welcome, Admin! 👑", "success")
            return redirect(url_for('all_users'))

        # Normal user login
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = False
            flash(f"Welcome back, {user.username}! 💛", "success")
            return redirect(url_for('books'))
        flash('Invalid credentials. Please try again.', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

# --------------------- BOOKS ---------------------
@app.route('/books')
def books():
    if 'user_id' not in session:
        flash("Please log in to view books.", "warning")
        return redirect(url_for('login'))

    # Auto-add dummy books if none exist
    if Book.query.count() == 0:
        dummy_books = [
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
            {"title": "1984", "author": "George Orwell"},
            {"title": "Pride and Prejudice", "author": "Jane Austen"},
            {"title": "The Catcher in the Rye", "author": "J.D. Salinger"},
            {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
            {"title": "Moby Dick", "author": "Herman Melville"},
            {"title": "War and Peace", "author": "Leo Tolstoy"},
            {"title": "The Odyssey", "author": "Homer"},
            {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky"}
        ]
        for book in dummy_books:
            db.session.add(Book(title=book['title'], author=book['author'], available=True))
        db.session.commit()
        flash("10 dummy books added to the library! 📚", "success")

    all_books = Book.query.all()
    return render_template('books.html', books=all_books)

@app.route('/borrow/<int:book_id>')
def borrow_book(book_id):
    if 'user_id' not in session:
        flash("Please log in to borrow books.", "warning")
        return redirect(url_for('login'))

    book = Book.query.get_or_404(book_id)
    if not book.available:
        flash("Sorry, this book is already borrowed.", "danger")
        return redirect(url_for('books'))

    record = BorrowRecord(
        user_id=session['user_id'],
        book_id=book.id,
        borrow_date=datetime.now().strftime("%Y-%m-%d"),
        returned=False
    )
    book.available = False
    db.session.add(record)
    db.session.commit()
    flash(f"You borrowed '{book.title}' successfully! 📚", "success")
    return redirect(url_for('my_borrowed_books'))

@app.route('/return/<int:record_id>')
def return_book(record_id):
    if 'user_id' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    record = BorrowRecord.query.get_or_404(record_id)
    book = Book.query.get(record.book_id)

    if record.returned:
        flash("This book has already been returned.", "info")
        return redirect(url_for('my_borrowed_books'))

    record.returned = True
    record.return_date = datetime.now().strftime("%Y-%m-%d")
    book.available = True
    db.session.commit()
    flash(f"'{book.title}' returned successfully! ✅", "success")
    return redirect(url_for('my_borrowed_books'))

@app.route('/my_borrowed_books')
def my_borrowed_books():
    if 'user_id' not in session:
        flash("Please log in to view borrowed books.", "warning")
        return redirect(url_for('login'))

    borrowed = BorrowRecord.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_borrowed_books.html', records=borrowed)

# --------------------- ADMIN ROUTES ---------------------
@app.route('/all_users')
def all_users():
    if not session.get('is_admin'):
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('books'))

    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            (User.username.contains(search_query)) | (User.email.contains(search_query))
        ).all()
    else:
        users = User.query.all()
    return render_template('all_users.html', users=users, search_query=search_query)

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if not session.get('is_admin'):
        flash("Only admin can delete users.", "danger")
        return redirect(url_for('books'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted successfully! 🗑️", "info")
    return redirect(url_for('all_users'))

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    if not session.get('is_admin'):
        flash("Only admin can update users.", "danger")
        return redirect(url_for('books'))

    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['name']
        user.email = request.form['email']
        user.password = request.form['password']
        db.session.commit()
        flash(f"User '{user.username}' updated successfully! ✏️", "success")
        return redirect(url_for('all_users'))

    return render_template('update_user.html', user=user)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not session.get('is_admin'):
        flash("Only admin can add books.", "danger")
        return redirect(url_for('books'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        db.session.add(Book(title=title, author=author, available=True))
        db.session.commit()
        flash(f"Book '{title}' added successfully! ✅", "success")
        return redirect(url_for('books'))

    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if not session.get('is_admin'):
        flash("Only admin can edit books.", "danger")
        return redirect(url_for('books'))

    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        db.session.commit()
        flash(f"Book '{book.title}' updated successfully! ✏️", "success")
        return redirect(url_for('books'))

    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not session.get('is_admin'):
        flash("Only admin can delete books.", "danger")
        return redirect(url_for('books'))

    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash(f"Book '{book.title}' deleted successfully! 🗑️", "info")
    return redirect(url_for('books'))

# --------------------- RUN APP ---------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
