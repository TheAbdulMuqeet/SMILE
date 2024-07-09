import random
import os
import hashlib
import time
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from main import Chatbot
from flask_session import Session


def secret():
    random_text = 'Random Key # ' + str(random.randint(100, 999))
    hashObj = hashlib.md5(random_text.encode('utf-8'))
    return hashObj.hexdigest()


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SECRET_KEY"] = secret()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQLAlchemy(app)
bot = Chatbot()

login_manager = LoginManager()
login_manager.init_app(app)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username").capitalize()
        user = Users(
            username=name,
            password=request.form.get("password")
        )
        db.session.add(user)
        db.session.commit()
        session["uname"] = name
        session["authenticated"] = True
        bot.uname = name
        bot.set_sid(request.form.get("sid"))
        bot.chat_counter = request.form.get("counter")
        login_user(user)
        return redirect("/")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username").capitalize()
        user = Users.query.filter_by(username=name).first()
        if user and user.password == request.form.get("password"):
            session["uname"] = name
            session["authenticated"] = True
            bot.uname = name
            bot.set_sid(request.form.get("sid"))
            bot.chat_counter = int(request.form.get("counter"))
            login_user(user)
            return redirect("/")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session["uname"] = None
    session["authenticated"] = False
    logout_user()
    return redirect("/")


@app.route("/")
def root():
    if session.get("authenticated"):
        return render_template("index.html", BotName=bot.name)
    return redirect("/login")


@app.route("/user_message/", methods=["POST"])
@login_required
def conversation():
    if request.method == "POST":
        message = request.form.get('message')
        return jsonify(bot.response(message))


@app.route("/upload/kb", methods=["POST"])
@login_required
def upload_kb():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            timestamp = str(int(time.time()))
            _, file_extension = os.path.splitext(uploaded_file.filename)
            unique_filename = f"kb_uploaded_{timestamp}{file_extension}"
            path = os.path.join(bot.base_path, os.environ.get(
                "KB_DIR", ""), unique_filename)

            with open(path, 'wb+') as destination:
                destination.write(uploaded_file.read())

            return jsonify({'message': 'File uploaded successfully'}), 200
        else:
            return jsonify({'error': 'No file uploaded'}), 400
    else:
        return jsonify({'error': 'Method not allowed'}), 405


if __name__ == "__main__":
    app.run(debug=True)
