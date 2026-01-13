from models import db, Admin
from app import app
from werkzeug.security import generate_password_hash

# Default admin credentials
ADMIN_NAME = "Admin"
ADMIN_EMAIL = "admin@gym.com"
ADMIN_PASSWORD = "admin123"  # You can change this

with app.app_context():
    existing_admin = Admin.query.filter_by(email=ADMIN_EMAIL).first()
    if existing_admin:
        print(f"Admin with email {ADMIN_EMAIL} already exists.")
    else:
        admin = Admin(
            name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD)
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created! Email: {ADMIN_EMAIL}, Password: {ADMIN_PASSWORD}")
if __name__ == '__main__':
    app.run(debug=True)