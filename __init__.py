#Import Flask Library
from flask import render_template, request, session, url_for, redirect, flash
import pymysql.cursors
from app import app
import hashlib, os

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='1929ulrica',
                       db='donation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # Only process form if POST method
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query DB for user
        cursor = conn.cursor()
        query = 'SELECT * FROM Person WHERE userName = %s'
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            stored_hash = user['password']
            stored_salt = user['salt']

            # Hash the entered password with the stored salt
            entered_hash = hashlib.sha256((stored_salt + password).encode('utf-8')).hexdigest()

            # Compare the two hashes
            if entered_hash == stored_hash:
                # Successful login
                session['username'] = username
                flash("Login successful!")
                return redirect(url_for('hello'))
            else:
                # Incorrect password
                flash("Incorrect password.")
                return redirect(url_for('login'))
        else:
            # Username not found
            flash("Username does not exist.")
            return redirect(url_for('login'))
    else:
        # If it's not a POST request, just redirect to login page
        return redirect(url_for('login'))


@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']

        # Generate salt and hash password
        salt = os.urandom(16).hex()
        hashed_pwd = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

        # Insert new user into the database
        cursor = conn.cursor()
        query = 'INSERT INTO Person (userName, password, fname, lname, email, salt) VALUES (%s, %s, %s, %s, %s, %s)'
        try:
            cursor.execute(query, (username, hashed_pwd, fname, lname, email, salt))
            conn.commit()
            cursor.close()
            flash("You are registered! Please log in.")
            return redirect(url_for('login'))
        except pymysql.err.IntegrityError:
            # Username already taken (assuming userName is a PRIMARY KEY)
            cursor.close()
            error = "This user already exists"
            return render_template('register.html', error = error)
    else:
        # If it's not a POST request, just redirect to register page
        return redirect('/index')


if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
