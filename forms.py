from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, length, Email

# WTForm for creating a blog post
# class CreatePostForm(FlaskForm):
#     title = StringField("Blog Post Title", validators=[DataRequired()])
#     subtitle = StringField("Subtitle", validators=[DataRequired()])
#     img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
#     body = CKEditorField("Blog Content", validators=[DataRequired()])
#     submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class CreateUserRegistrationForm(FlaskForm):
    email = EmailField("Enter your email", validators=[DataRequired(), Email()])
    username = StringField("Enter a username which you want to display", validators=[DataRequired(), length(max=20)])
    password = PasswordField("Create a password to login on the website", validators=[DataRequired(), length(min=8, max=20)])
    sign_in = SubmitField("sign me up")


# TODO: Create a LoginForm to login existing users
class CreateLoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), length(min=8, max=20)])
    login = SubmitField("Login")

# TODO: Create a CommentForm so users can leave comments below posts
