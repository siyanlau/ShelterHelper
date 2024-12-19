#Import Flask Library
from flask import render_template, request, session, url_for, redirect, flash
import pymysql.cursors
from app import app
import hashlib, os
from queries import query_fetch_locations_by_itemID

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

#Define route for login authentication
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # Only process form if POST method
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query DB for user
        cursor = conn.cursor()
        query = 'SELECT * FROM person WHERE userName = %s'
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        error = None

        if user:
            stored_hash = user['password']
            stored_salt = user['salt']

            # Hash the entered password with the stored salt
            entered_hash = hashlib.sha256((stored_salt + password).encode('utf-8')).hexdigest()

            # Compare the two hashes
            if entered_hash == stored_hash:
                # Successful login
                # creates a session for the user
                session['username'] = username
                # don't just render_template to home.html, because only logged in users can access that page
                # we shall put session verification logic in home()
                return redirect(url_for('home'))
            else:
                # Incorrect password
                error = 'Invalid credentials'
                return render_template('login.html', error=error)
        else:
            # Username not found
            error = 'User not found'
            return render_template('login.html', error=error)

#Define route for register authentication
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

        cursor = conn.cursor()
        # Verify if user already exists
        query = 'SELECT * FROM person WHERE username = %s'
        cursor.execute(query, (username))
        # store the result (could be empty) in a variable
        data = cursor.fetchone()
        error = None
        if (data):
            error = "Username already exists! Please log in."
            return render_template('register.html', error = error)
        else:
            # username does not exist. we can insert into DB
            query = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s, %s)'
            cursor.execute(query, (username, hashed_pwd, fname, lname, email, salt))
            conn.commit()
            cursor.close()
            return render_template('login.html')

#Define route for home page (must be logged in)
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = session['username']
    return render_template('home.html', username=user)

#Define route for logging out user
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

#Define route for finding a single item using itemID
@app.route('/findItem', methods=['POST'])
def findItem():
    if 'username' not in session:
        return redirect(url_for('login'))

    itemID = request.form['itemID']

    # Query the database to get item details and locations
    cursor = conn.cursor()

    # Fetch item details
    item_query = 'SELECT * FROM Item WHERE ItemID = %s'
    cursor.execute(item_query, (itemID,))
    itemDetail = cursor.fetchone()

    # Fetch piece details and locations (join with Location if necessary)
    itemLocations = []
    error = None
    if itemDetail:
        cursor.execute(query_fetch_locations_by_itemID, (itemID,))
        itemLocations = cursor.fetchall()
    else:
        error = f"Item with ID {itemID} not found in the database."    
    
    cursor.close()
    
    return render_template('home.html', username=session['username'], item=itemDetail, locations=itemLocations, error=error)
    
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
