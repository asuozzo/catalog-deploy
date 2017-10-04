import random
import string
import json
import httplib2
from functools import wraps
from models import Base, User, Book
from flask import Flask, jsonify, request, render_template, url_for, redirect, flash
from flask import session as login_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from flask import make_response
import os

engine = create_engine('postgresql://catalog:udacity@localhost/catalog')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)
app.config['SECRET_KEY'] = "super_secret_key"

def check_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" in  login_session:
            return f(*args, **kwargs)
        flash("whoops, you need to be logged in to do that!")
        return redirect(url_for("login"))
    return wrapper

def check_object_owner(username):
    if username == login_session["username"]:
        return True
    return False


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get("state") != login_session['state']:
        response = make_response(json.dumps("Invalid state parameter"), 401)
        response.headers['Content-Type'] = "application/json"
        return response
    access_token = request.data

    # Exchange client token for server-side token
    app_id = json.loads(open('/var/www/html/fb_client_secrets.json', "r").read())["web"]["app_id"]
    app_secret = json.loads(open('/var/www/html/fb_client_secrets.json', "r").read())["web"]["app_secret"]
    url = ("https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s") % (app_id,app_secret,access_token)
    h = httplib2.Http()
    result = h.request(url, "GET")[1]
    data = json.loads(result)

    token = "access_token="+data["access_token"]

    url = ("https://graph.facebook.com/v2.8/me?%s&fields=name,id,email") % (token)
    h = httplib2.Http()
    result = h.request(url, "GET")[1]

    data = json.loads(result)

    login_session['provider'] = "facebook"
    login_session["username"] = data["name"]
    login_session["email"] = data["email"]
    login_session["facebook_id"] = data["id"]

    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session["user_id"] = user_id

    output = ""
    output += "<h1>Welcome, "
    output += login_session["username"]
    output += "!</h1>"
    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route("/fbdisconnect/")
def fbdisconnect():
    facebook_id = login_session["facebook_id"]
    access_token = login_session["access_token"]
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/logout')
def logout():
    if 'provider' in login_session:
        fbdisconnect()
        del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        del login_session['provider']

        flash("You have been logged out.")
        return redirect(url_for("showAllBooks"))
    else:
        flash("Whoops, we can't log you out because you weren't logged in!")
        return redirect(url_for('showAllBooks'))

@app.route('/')
@app.route('/library/')
def showAllBooks():
    books = session.query(Book).all()
    genres = [b.genre for b in session.query(Book.genre).distinct()]
    return render_template('home.html', books=books, genres=genres)


@app.route("/library/<book_genre>")
def showGenreBooks(book_genre):
    books = session.query(Book).filter_by(genre=book_genre)
    return render_template('genre.html', genre=book_genre, books=books)


@app.route('/library/<int:book_id>/')
def showBook(book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    user = session.query(User).filter_by(id=book.user_id).one()
    username = user.username
    return render_template('item.html', book=book, username=username)


@app.route('/library/<int:book_id>/edit', methods=['GET', 'POST'])
@check_login
def editBook(book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    user = session.query(User).filter_by(username=login_session['username']).one()
    if user.id == book.user_id:
        if request.method == 'POST':
            book.title = request.form['title']
            book.author = request.form['author']
            book.description = request.form['description']
            book.genre = request.form['genre']
            session.commit()
            flash("Item successfully edited")
            return redirect(url_for("showBook", book_id=book.id))
        return render_template('edit.html', book=book)
    else:
        flash("Sorry, you can't edit a book you didn't create.")
        return redirect(url_for("showBook", book_id=book.id))


@app.route('/library/<int:book_id>/delete', methods=['GET', 'POST'])
@check_login
def deleteBook(book_id):
    book = session.query(Book).filter_by(id=book_id).one()
    user = session.query(User).filter_by(username=login_session['username']).one()
    if user.id == book.user_id:
        if request.method == 'POST':
            user = session.query(User).filter_by(username=login_session['username']).one()
            session.delete(book)
            session.commit()
            flash("Item successfully deleted")
            return redirect(url_for("showAllBooks"))
        return render_template('delete.html', book=book)
    else:
        flash("Sorry, you can't delete a book you didn't create.")
        return redirect(url_for("showBook", book_id=book.id))



@app.route('/library/add', methods=['GET', 'POST'])
@check_login
def addBook():
    if request.method == 'POST':
        newBook = Book(title=request.form['title'],
                       author=request.form['author'],
                       description=request.form['description'],
                       genre=request.form['genre'])
        user = session.query(User).filter_by(username=login_session["username"]).one()
        newBook.user_id = user.id
        session.add(newBook)
        session.commit()
        flash("Success!")
        return redirect(url_for("showAllBooks"))
    return render_template('additem.html')


@app.route('/library/json')
def jsonifyBooks():
    books = session.query(Book).all()
    return jsonify(books=[book.serialize for book in books])

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def createUser(loginsession):
    newUser = User(username=loginsession['username'], email=loginsession['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=loginsession['email']).one()
    return user.id


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
