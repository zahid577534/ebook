from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask import Flask, render_template, request, send_file
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    classification_no = db.Column(db.String(50))
    cutter_no = db.Column(db.String(50))
    publisher_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float)
    donation_received = db.Column(db.String(100), nullable=True)
    date_of_purchase = db.Column(db.Date, default=datetime.date.today, nullable=True)

class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    status = db.Column(db.String(20), default="Pending")  # Pending, Approved, Rejected
    user = db.relationship('User', backref='requests')
    book = db.relationship('Book', backref='requests')

# ------------------ LOGIN MANAGER ------------------
login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # ✅ Take role from form

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
        else:
            new_user = User(username=username, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
#Export file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
@app.route('/export/<file_type>')
def export_books(file_type):
    search = request.args.get('search', '')

    if search:
        books = Book.query.filter(
            (Book.title.ilike(f"%{search}%")) | (Book.author.ilike(f"%{search}%"))
        ).all()
    else:
        books = Book.query.all()

    if file_type == 'pdf':
        return generate_pdf(books)
    elif file_type == 'excel':
        return generate_excel(books)
    else:
        return "Invalid file type", 400
git init
def generate_pdf(books):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("<b>Book List</b>", styles['Title'])
    elements.append(title)

    # Table Data (Header + Rows)
    data = [["#", "Title", "Author", "Classification No", "Cutter No", "Publisher", "Price", "Quantity", "Date of Purchase"]]

    for idx, book in enumerate(books, start=1):
        data.append([
            str(idx),
            book.title,
            book.author,
            book.classification_no,
            book.cutter_no,
            book.publisher_name,
            f"{book.price:.2f}",
            str(book.quantity),
            book.date_of_purchase.strftime('%Y-%m-%d') if book.date_of_purchase else ""
        ])

    # Create Table
    table = Table(data, colWidths=[25, 90, 80, 80, 60, 80, 50, 50, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),  # Header bg (Bootstrap Primary)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="books.pdf", mimetype='application/pdf')


def generate_excel(books):
    data = []
    for book in books:
        data.append({
            "Title": book.title,
            "Author": book.author,
            "Classification No": book.classification_no,
            "Cutter No": book.cutter_no,
            "Publisher": book.publisher_name,
            "Price": book.price,
            "Quantity": book.quantity,
            "Date of Purchase": book.date_of_purchase.strftime('%Y-%m-%d') if book.date_of_purchase else ""
        })

    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Books")

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="books.xlsx",
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for('manage_books'))
    else:
        return redirect(url_for('view_books'))

# ADMIN: MANAGE BOOKS
@app.route('/manage_books')
@login_required
def manage_books():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')

    # Start query
    query = Book.query

    # Apply search filter if keyword provided
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Book.title.ilike(search_pattern)) |
            (Book.author.ilike(search_pattern))
        )

    # Paginate after filtering
    pagination = query.paginate(page=page, per_page=10)
    books = pagination.items

    # Calculate total stats (filtered)
    total_books = query.count()
    total_quantity = sum(book.quantity for book in books)

    return render_template('manage_books.html',
                           books=books,
                           pagination=pagination,
                           total_books=total_books,
                           total_quantity=total_quantity)



# ADMIN: ADD BOOK
from datetime import datetime

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        classification_no = request.form['classification_no']
        cutter_no = request.form['cutter_no']
        publisher_name = request.form['publisher_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        donation_received = request.form['donation_received']
        date_of_purchase_str = request.form['date_of_purchase']

        # ✅ Convert string to Python date
        date_of_purchase = datetime.strptime(date_of_purchase_str, '%Y-%m-%d').date()

        new_book = Book(
            title=title,
            author=author,
            classification_no=classification_no,
            cutter_no=cutter_no,
            publisher_name=publisher_name,
            quantity=quantity,
            price=price,
            donation_received=donation_received,
            date_of_purchase=date_of_purchase  # ✅ Pass the date object
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('view_books'))
    return render_template('add_book.html')
#edit books
@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.classification_no = request.form['classification_no']
        book.cutter_no = request.form['cutter_no']
        book.publisher_name = request.form['publisher_name']
        book.price = float(request.form['price'])
        book.quantity = int(request.form['quantity'])
        # Optional: handle date if editable
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('manage_books'))

    return render_template('edit_book.html', book=book)

# ADMIN: DELETE BOOK
@app.route('/delete_book/<int:book_id>', methods=['GET'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('manage_books'))


# STUDENT: VIEW BOOKS
@app.route('/student/books')
@login_required
def view_books():
    books = Book.query.all()
    return render_template('view_books.html', books=books)

# STUDENT: REQUEST BOOK
@app.route('/student/request_book/<int:id>')
@login_required
def request_book(id):
    if current_user.role != "student":
        flash("Only students can request books!", "danger")
        return redirect(url_for('dashboard'))

    new_request = BookRequest(user_id=current_user.id, book_id=id)
    db.session.add(new_request)
    db.session.commit()
    flash('Book request sent successfully!', 'success')
    return redirect(url_for('view_books'))

# LOGOUT
@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ------------------ INITIALIZE DB ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ✅ Flask 3 compatible
        # Create an admin user if not exists
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", password=generate_password_hash("admin123"), role="admin")
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)
