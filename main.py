import random
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
        return f"<User {self.id}>"



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, nullable=False)
    author_name = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    likes = db.relationship('Like', backref='post', lazy=True)

    def __repr__(self):
        return f"<Post {self.id}>"


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)






@app.route('/delete-post')
def delete_post():
    user_id = request.args.get('user_id')
    post_id = request.args.get('id')
    if 'authorized' in session and 'id' in session:
        if int(user_id) == int(session["id"]):
            try:
                Post.query.filter_by(id=post_id).delete()
                Like.query.filter_by(post_id=post_id).delete()
                db.session.commit()
                return redirect(f'/user/{user_id}')
            except Exception as ex:
                print(ex)
                return "Ошибка БД"
        else:
            return 'Нет доступа'
    else:
        return redirect('/')
@app.route("/")
def go_home():
    return redirect("/home")



@app.route("/like-post", methods=["POST"])
def like_post():
    if request.method == "POST":
        post_id = request.form.get('post_id')
        print(post_id)
        post = Post.query.get(post_id)
        liked_users = [like.user_id for like in post.likes]
        if session['id'] not in liked_users:
            like = Like(post_id=post_id, user_id=session['id'])
            try:
                db.session.add(like)
                db.session.commit()
            except Exception as ex:
                print(ex)
                return "Произошла ошибка БД"
        else:
            Like.query.filter_by(user_id=session['id']).filter_by(post_id=post_id).delete()
            try:
                db.session.commit()
            except Exception as ex:
                print(ex)
                return "Произошла ошибка БД"

        return str(get_like_count(post_id))

def get_like_count(post_id):
    post = Post.query.get(post_id)
    liked_users = [like.user_id for like in post.likes]
    return len(liked_users)



@app.route("/home")
def main():
    if 'authorized' in session and session['authorized']:
        user = User.query.get(session['id'])
        name = user.username

        posts = Post.query.order_by(Post.date.desc()).all()

        likes_list = Like.query.filter_by(user_id=session['id']).all()
        likes = [like.post_id for like in likes_list]
        return render_template("main.html", name=name, id=session['id'], posts=posts, likes=likes)
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

@app.route("/user/<int:id>", methods=["GET", "POST"])
def user_profile(id):
    if 'authorized' in session and session['authorized']:
        if request.method == "GET":
            if User.query.get(id):
                name = User.query.get(id).nickname
                try:
                    posts = Post.query.filter_by(author_id=id).order_by(Post.date.desc()).all()
                except:
                    posts = []
                self_name = User.query.get(session['id']).nickname
                return render_template('user_profile.html', self_id=session['id'], id=id, name=name, posts=posts, self_name=self_name)
            else:
                return "Пользователь не найден"
        else:
            post_id = request.form['post_id']
            return redirect(f'/user/{id}')
    else:
        return redirect("/auth")


@app.route('/create-post', methods=["POST", "GET"])
def create_post():
    if 'authorized' in session and session['authorized']:
        if request.method == "GET":
            id = request.args.get('id')
            if int(session['id']) == int(id):
                User.query.get(id)
                return render_template('create-post.html')
            else:
                return 'Ошибка'
        else:
            title = request.form['title']
            text = request.form['text']
            image = request.files['image']
            file_name = f'{session["id"]}-{datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")}'
            image_path = f'static/img/users-post-pictures/{file_name}'
            image.save(image_path)

            print(image_path, file_name)

            author_id = session['id']
            author_name = User.query.get(author_id).nickname

            post = Post(author_id=author_id, author_name=author_name, title=title, text=text, image_path=file_name)

            try:
                db.session.add(post)
                db.session.commit()
                return redirect(f'/user/{session["id"]}')
            except Exception as ex:
                print(ex)
                return "Произошла ошибка базы данных"
    else:
        return redirect("/auth")

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/auth')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)