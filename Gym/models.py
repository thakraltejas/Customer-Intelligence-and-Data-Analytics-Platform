from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ------------------------------
# Admin Model
# ------------------------------
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed password

    def __repr__(self):
        return f"<Admin {self.name}>"


# ------------------------------
# Customer Model
# ------------------------------
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    membership_type = db.Column(db.String(20), nullable=False, default='Monthly')
    payment_amount = db.Column(db.Float, nullable=True, default=0.0)
    join_date = db.Column(db.Date, nullable=True, default=datetime.utcnow)
    next_renewal = db.Column(db.Date, nullable=True)
    entry_time = db.Column(db.Time, nullable=True)

    payments = db.relationship('Payment', backref='customer', lazy=True)
    entry_logs = db.relationship('EntryLog', backref='customer', lazy=True)

    def __repr__(self):
        return f"<Customer {self.name}>"


# ------------------------------
# Payment Model
# ------------------------------
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    month = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Paid / Pending
    date = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.customer.name} - {self.month}>"


# ------------------------------
# Entry Log Model
# ------------------------------
class EntryLog(db.Model):
    __tablename__ = 'entry_logs'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=True)   # Changed from Time → DateTime
    check_out = db.Column(db.DateTime, nullable=True)  # Changed from Time → DateTime
    date = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return f"<EntryLog {self.customer.name} - {self.date}>"
