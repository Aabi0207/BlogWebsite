import datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import smtplib
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField
from sqlalchemy.orm import relationship, registry
import os
# Import your forms from the forms.py
from forms import CreateUserRegistrationForm, CreateLoginForm

app = Flask(__name__)
MY_EMAIL = os.environ.get("EMAIL")
MY_PASSWORD = os.environ.get("EMAIL_PASSWORD")

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)
CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
db = SQLAlchemy()
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "user_data"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)


with app.app_context():
    db.create_all()


class MyForm(FlaskForm):
    title = StringField("The title of the Blog", [DataRequired()])
    subtitle = StringField("Subtitle of the BlogPost", [DataRequired()])
    author = StringField("Author's Name", [DataRequired()])
    img_url = URLField("Url for the background image", [DataRequired(), URL()])
    body = CKEditorField("The body of your blogpost", [DataRequired()])
    submit = SubmitField('Post')


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    with app.app_context():
        posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", posts=posts)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    form = CreateUserRegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=8)
        fetch_email = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if fetch_email:
            flash("This email is already registered with the blog website try to login")
            return redirect(url_for("login"))
        fetch_username = db.session.execute(db.select(User).where(User.username == username)).scalar()
        if fetch_username:
            form.username.errors.append("This username is not available")
            form.username.errors.reverse()
            return render_template("register.html", form=form)
        new_user = User(email=email, password=password, username=username)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CreateLoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        is_password_correct = check_password_hash(user.password, form.password.data)
        if not user:
            form.email.errors.append("Invalid email address.")
            form.email.errors.reverse()
        elif not is_password_correct:
            form.password.errors.append("wrong Password")
            form.password.errors.reverse()
        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/show_post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    if current_user.is_authenticated:
        requested_post = db.get_or_404(BlogPost, post_id)
        return render_template("post.html", post=requested_post)
    else:
        flash("In order to view the post you have to login first")
        return redirect(url_for("login"))


@app.route("/contact", methods=["get", "post"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=os.environ.get("RECEIVING_EMAIL"),
                msg=f"Subject:A new user enrolled in your website\n\n\n"
                    f"Data of the user\n"
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Phone: {phone}\n"
                    f"message: {message}\n"
            )
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def new_post():
    form = MyForm()
    today_date = datetime.datetime.now()
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=f"{today_date.strftime('%B')} {date.today().day}, {date.today().year}",
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data
        )
        with app.app_context():
            db.session.add(post)
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, msg="New Post")


@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    form = MyForm(
        title=post.title,
        subtitle=post.subtitle,
        body=post.body,
        author=post.author,
        img_url=post.img_url
    )
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.author = form.author.data
        post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for('post', post_id=post_id))
    return render_template("make-post.html", form=form, msg="Edit Post")


@app.route("/delete-post/<int:post_id>")
@admin_only
def delete_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=False, port=5001)
