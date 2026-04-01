from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import date, timedelta

app = Flask(__name__)

app.config['SECRET_KEY'] = 'neuroplus-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuroplus.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ── Models ──

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='child')


class SpeechScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, default=date.today)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Auth Routes ──

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

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in!', 'error')
            return redirect(url_for('signup'))

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


# ── Main Dashboard Routes ──

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/parent-dashboard')
@login_required
def parent_dashboard():
    return "Parent Dashboard coming soon."


@app.route('/teacher-dashboard')
@login_required
def teacher_dashboard():
    return "Teacher Dashboard coming soon."


# ── Speech Practice Routes ──

@app.route('/speech')
@login_required
def speech():
    today = date.today()

    today_entry = SpeechScore.query.filter_by(
        user_id=current_user.id, date=today
    ).first()
    today_score = today_entry.score if today_entry else 0

    all_scores = SpeechScore.query.filter_by(
        user_id=current_user.id
    ).order_by(SpeechScore.date.desc()).all()

    best_score = max((s.score for s in all_scores), default=0)

    # Calculate streak
    streak = 0
    check = today
    score_dates = {s.date for s in all_scores}
    while check in score_dates:
        streak += 1
        check = check - timedelta(days=1)

    history = [
        {'date': s.date.strftime('%b %d'), 'score': s.score}
        for s in all_scores if s.date != today
    ][:5]

    return render_template('speech.html',
        today_score=today_score,
        best_score=best_score,
        streak=streak,
        history=history
    )


@app.route('/speech/save-score', methods=['POST'])
@login_required
def save_score():
    data = request.get_json()
    today = date.today()

    entry = SpeechScore.query.filter_by(
        user_id=current_user.id, date=today
    ).first()

    if entry:
        entry.score = data['score']
    else:
        entry = SpeechScore(
            user_id=current_user.id,
            score=data['score'],
            date=today
        )
        db.session.add(entry)

    db.session.commit()
    return jsonify({'status': 'ok'})


# ── Init DB & Run ──

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)