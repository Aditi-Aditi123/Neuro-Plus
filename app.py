from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)

# Config — all free, uses SQLite (no external DB needed)
app.config['SECRET_KEY'] = 'neuroplus-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuroplus.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ── User Model (like a schema/table) ──
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='child')  # child / parent / teacher


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Routes ──
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # Redirect based on role
            if user.role == 'parent':
                return redirect(url_for('parent_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Incorrect email or password. Try again!', 'error')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in!', 'error')
            return redirect(url_for('signup'))

        # Hash password before saving
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ── Placeholder routes for other teammates' components ──
@app.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome {current_user.name}! Dashboard coming soon."

@app.route('/parent-dashboard')
@login_required
def parent_dashboard():
    return f"Parent Dashboard coming soon."

@app.route('/teacher-dashboard')
@login_required
def teacher_dashboard():
    return f"Teacher Dashboard coming soon."


# ── Create DB tables on first run ──
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)