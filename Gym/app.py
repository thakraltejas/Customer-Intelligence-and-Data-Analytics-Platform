from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, Admin, Customer, Payment, EntryLog

app = Flask(__name__)
app.secret_key = "rishabh_secret_key"

# ------------------------------
# Database Configuration
# ------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gym.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


# ------------------------------
# HOME / INDEX
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')


# ------------------------------
# CUSTOMER REGISTRATION
# ------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')
        password = generate_password_hash(request.form['password'])
        membership_type = request.form['membership_type']

        if Customer.query.filter_by(email=email).first():
            flash("Email already exists!", "error")
            return redirect(url_for('register'))

        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            password=password,
            membership_type=membership_type,
            join_date=datetime.utcnow()
        )
        db.session.add(customer)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ------------------------------
# LOGIN (CUSTOMER / ADMIN)
# ------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role == 'customer':
            user = Customer.query.filter_by(email=email).first()
        else:
            user = Admin.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = role
            flash("Login successful!", "success")
            return redirect(url_for(f'{role}_dashboard'))
        else:
            flash("Invalid credentials!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


# ------------------------------
# LOGOUT
# ------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))


# ------------------------------
# CUSTOMER DASHBOARD
# ------------------------------
@app.route('/customer/dashboard')
def customer_dashboard():
    if session.get('role') != 'customer':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    customer = Customer.query.get(session['user_id'])
    payments = Payment.query.filter_by(customer_id=customer.id).all()
    return render_template('customer_dashboard.html', customer=customer, payments=payments)


# ------------------------------
# ADMIN DASHBOARD
# ------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    if search:
        customers = Customer.query.filter(
            (Customer.name.contains(search)) |
            (Customer.email.contains(search)) |
            (Customer.membership_type.contains(search))
        ).all()
    else:
        customers = Customer.query.all()

    total_customers = len(customers)
    active_memberships = Customer.query.filter(
        Customer.next_renewal >= datetime.utcnow().date()
    ).count()
    total_revenue = sum(p.amount for p in Payment.query.filter_by(status='Paid').all())
    payments = Payment.query.order_by(Payment.date.desc()).limit(5).all()

    return render_template(
        'admin_dashboard.html',
        customers=customers,
        total_customers=total_customers,
        active_memberships=active_memberships,
        total_revenue=total_revenue,
        payments=payments,
        search=search
    )


# ------------------------------
# CUSTOMERS LIST / SEARCH (ADMIN)
# ------------------------------
@app.route('/admin/customers')
def admin_customers_list():
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    if search:
        customers = Customer.query.filter(
            (Customer.name.contains(search)) |
            (Customer.email.contains(search)) |
            (Customer.membership_type.contains(search))
        ).all()
    else:
        customers = Customer.query.all()

    return render_template('customers_list.html', customers=customers)


# ------------------------------
# ADD CUSTOMER (ADMIN)
# ------------------------------
@app.route('/admin/customers/add', methods=['GET', 'POST'])
def add_customer():
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone')
        password = generate_password_hash(request.form['password'])
        membership_type = request.form['membership_type']
        payment_amount = float(request.form.get('payment_amount', 0))
        join_date = datetime.strptime(request.form['join_date'], '%Y-%m-%d') if request.form.get('join_date') else datetime.utcnow()
        next_renewal = datetime.strptime(request.form['next_renewal'], '%Y-%m-%d') if request.form.get('next_renewal') else None

        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            password=password,
            membership_type=membership_type,
            payment_amount=payment_amount,
            join_date=join_date,
            next_renewal=next_renewal
        )
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully!", "success")
        return redirect(url_for('admin_customers_list'))

    return render_template('edit_customer.html', customer=None)


# ------------------------------
# UPDATE CUSTOMER (ADMIN)
# ------------------------------
@app.route('/admin/customers/update/<int:id>', methods=['GET', 'POST'])
def update_customer(id):
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form.get('phone')
        if request.form.get('password'):
            customer.password = generate_password_hash(request.form['password'])
        customer.membership_type = request.form['membership_type']
        customer.payment_amount = float(request.form.get('payment_amount', 0))
        customer.join_date = datetime.strptime(request.form['join_date'], '%Y-%m-%d') if request.form.get('join_date') else customer.join_date
        customer.next_renewal = datetime.strptime(request.form['next_renewal'], '%Y-%m-%d') if request.form.get('next_renewal') else customer.next_renewal
        customer.entry_time = datetime.strptime(request.form['entry_time'], '%H:%M').time() if request.form.get('entry_time') else customer.entry_time

        db.session.commit()
        flash("Customer updated successfully!", "success")
        return redirect(url_for('admin_customers_list'))

    return render_template('edit_customer.html', customer=customer)


# ------------------------------
# DELETE CUSTOMER (ADMIN)
# ------------------------------
@app.route('/admin/customers/delete/<int:id>')
def delete_customer(id):
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for('admin_customers_list'))


# ------------------------------
# VIEW CUSTOMER PAYMENTS (ADMIN)
# ------------------------------
@app.route('/admin/customers/<int:customer_id>/payments')
def customer_payment_details(customer_id):
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    customer = Customer.query.get_or_404(customer_id)
    payments = Payment.query.filter_by(customer_id=customer_id).order_by(Payment.date.desc()).all()
    return render_template('customer_payment_details.html', customer=customer, payments=payments)


# ------------------------------
# PAYMENT HISTORY (General)
# ------------------------------
@app.route('/payments')
def payment_history():
    if 'role' not in session:
        flash("Login required!", "error")
        return redirect(url_for('login'))

    payments = Payment.query.all() if session.get('role') == 'admin' else Payment.query.filter_by(customer_id=session['user_id']).all()
    return render_template('payment_history.html', payments=payments)


# ------------------------------
# ENTRY LOGS (ADMIN)
# ------------------------------
@app.route('/entry_logs')
def entry_logs():
    if session.get('role') != 'admin':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    logs = EntryLog.query.join(Customer).filter(
        (Customer.name.contains(search)) |
        (Customer.email.contains(search))
    ).all() if search else EntryLog.query.all()

    return render_template('entry_logs.html', logs=logs)


# ------------------------------
# RUN APP
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
