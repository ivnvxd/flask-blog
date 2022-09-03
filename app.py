from flask import Flask, render_template, request, flash, redirect, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required


# Configure application
app = Flask(__name__)

# Configure SQLAlchemy to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set development mode
app.config["FLASK_ENV"] = 'development'

app.config['SECRET_KEY'] = 'KLXH243GssUWwKdTWS8FDhdwYF56wPj6'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    hash = db.Column(db.String)

    def __init__(self, username, hash):
        self.username = username
        self.hash = hash


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    title = db.Column(db.String(50))
    subtitle = db.Column(db.String(50))
    content = db.Column(db.Text)

    def __init__(self, user_id, created, title, subtitle, content):
        self.user_id = user_id
        self.created = created
        self.title = title
        self.subtitle = subtitle
        self.content = content


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
def index():
    """Show homepage"""

    # Query all posts from db and render homepage
    posts = db.session.query(Post, User.username).join(User, Post.user_id == User.id).order_by(Post.created.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/create', methods=["GET", "POST"])
@login_required
def create():
    """Create new post"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get user input
        user_id = session["user_id"]
        created = datetime.now()
        title = request.form['title']
        subtitle = request.form['subtitle']
        content = request.form['content']

        # Ensure all fields were submitted
        if not title:
            flash('Title is required!')
            return render_template('create.html')
        elif not subtitle:
            flash('Subtitle is required!')
            return render_template('create.html')
        elif not content:
            flash('Post content is required!')
            return render_template('create.html')

        else:
            # Add record to database
            post = Post(user_id, created, title, subtitle, content)
            db.session.add(post)
            db.session.commit()

            # Redirect user to home page
            flash(f'"{post.title}" was successfully added!')
            return redirect('/')

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template('create.html')


@app.route('/about')
def about():
    """Show about page"""
    return render_template('about.html')


@app.route('/post/<int:post_id>')
def post(post_id):
    """Show post"""

    # Query post from db and render post page
    post = db.session.query(Post, User.username).join(User, Post.user_id == User.id).filter(Post.id == post_id).one()
    return render_template('post.html', post=post, session=session)


@app.route('/post/<int:post_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(post_id):
    """Edit post"""

    post = db.session.query(Post, User.username).join(User, Post.user_id == User.id).filter(Post.id == post_id).one()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        post[0].title = request.form['title']
        post[0].subtitle = request.form['subtitle']
        post[0].content = request.form['content']
        post[0].user_id = session["user_id"]

        # Ensure all fields were submitted
        if not post[0].title:
            flash('Title is required!')
            return render_template('edit.html', post=post)
        elif not post[0].subtitle:
            flash('Subtitle is required!')
            return render_template('edit.html', post=post)
        elif not post[0].content:
            flash('Post content is required!')
            return render_template('edit.html', post=post)

        else:
            # Update record in db
            db.session.commit()

            # Redirect user to home page
            flash(f'{post[0].title} was successfully edited!')
            return redirect('/')

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Render edit page if correct user logged in
        if session["user_id"] == post[0].user_id:
            return render_template('edit.html', post=post)

        # Redirect to homepage if not author is logged in
        else:
            flash(f'You are not allowed to edit "{post[0].title}"')
            return redirect("/")


@app.route('/post/<int:post_id>/delete', methods=('POST', ))
@login_required
def delete(post_id):
    """Delete post"""

    post = Post.query.filter_by(id=post_id).one()

    # User reached route via POST
    if request.method == "POST":

        # Delete record from db
        db.session.delete(post)
        db.session.commit()

        # Redirect user to home page
        flash(f'"{post.title}" was successfully deleted!')
        return redirect('/')


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirmation']

        # Ensure all fields were submitted
        if not username:
            flash('Must provide username')
            return render_template('register.html')
        elif not password:
            flash('Must provide password')
            return render_template('register.html')
        elif not confirmation:
            flash('Must provide confirmation')
            return render_template('register.html')

        # Ensure new password and confirmation match
        if password != confirmation:
            flash("Password and confirmation don't match")
            return render_template('register.html')

        # Ensure username not taken
        user = User.query.filter_by(username=username).first()
        if user:
            flash(f'Username already taken')
            return render_template('register.html')

        # Get password hash value
        hash = generate_password_hash(password)

        # Add user to database
        user = User(username, hash)
        db.session.add(user)
        db.session.commit()

        # Log user in
        user = User.query.filter_by(username=username).first()
        session["user_id"] = user.id

        # Redirect user to home page
        flash(f'You have been registered as "{user.username}"')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        # Ensure all fields were submitted
        if not username:
            flash('Must provide username')
            return render_template('login.html')
        elif not password:
            flash('Must provide password')
            return render_template('login.html')

        # Query database for username/password
        user = User.query.filter_by(username=username).first()

        # Ensure username exists and password is correct
        if not user or not check_password_hash(user.hash, password):
            flash('Invalid username and/or password')
            return render_template('login.html')

        # Remember which user has logged in
        session["user_id"] = user.id

        # Redirect user to home page
        flash(f'You have logged in as "{user.username}"')
        return redirect('/')

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirmation = request.form['confirmation']

        # Ensure all fields were submitted
        if not current_password:
            flash('Must provide current password')
            return render_template('settings.html')
        elif not new_password:
            flash('Must provide new password')
            return render_template('settings.html')
        elif not confirmation:
            flash('Must provide confirmation')
            return render_template('settings.html')

        # Ensure new password and confirmation match
        if new_password != confirmation:
            flash("New password and confirmation don't match")
            return render_template('settings.html')

        # Query database for password hash
        user_id = session["user_id"]
        user = User.query.filter_by(id=user_id).first()

        # Ensure password is correct
        if not check_password_hash(user.hash, current_password):
            flash('Invalid password')
            return render_template('settings.html')

        # Update user's password
        user.hash = generate_password_hash(new_password)
        db.session.commit()

        # Redirect user to home page
        flash('Password changed successfully')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("settings.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    flash('You have logged out')
    return redirect("/")
