import secrets
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///main.db'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    reg_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.id}"





@app.route("/")
def go_home():
    return redirect("/home")


@app.route("/home")
def main():
    if 'authorized' in session:
        user = User.query.get(session['id'])
        name = user.username
        return render_template("main.html", name=name)
    else:
        return redirect('/auth')


@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/registration", methods=["POST", "GET"])
def registartion():
    if request.method == "GET":
        return render_template("registration.html")
    else:
        nickname = request.form['name']
        username = request.form['username']
        password = request.form['password']

        user = User(nickname=nickname, username=username, password=password)


        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template("registration.html", text="Пользователь существует")
        else:
            try:
                db.session.add(user)
                db.session.commit()
                session['authorized'] = True
                session['id'] = user.id
                return redirect('/home')
            except Exception as Ex:
                print(Ex)
                return render_template("registration.html", text="Произошла ошибка БД")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            if existing_user.password == password:
                session['authorized'] = True
                session['id'] = existing_user.id
                return redirect("/home")
            else:
                return render_template("login.html", text="Данные не верны")
        else:
            return render_template("login.html", text="Данные не верны")


if __name__ == '__main__':
    app.run(debug=True)