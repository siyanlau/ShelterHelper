#Import Flask Library
from flask import render_template, request, session, url_for, redirect, flash
import pymysql.cursors
from app import app
import hashlib, os
from queries import query_fetch_locations_by_itemID, query_fetch_orderID, query_fetch_items_by_orderID


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
        role = request.form.get('role', 'customer')  # Default to 'customer'

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
            query = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s, %s, %s)'
            cursor.execute(query, (username, hashed_pwd, fname, lname, email, salt, role))
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

    # Fetch piece details and locations
    itemLocations = []
    error = None
    if itemDetail:
        cursor.execute(query_fetch_locations_by_itemID, (itemID,))
        itemLocations = cursor.fetchall()
    else:
        error = f"Item with ID {itemID} not found in the database."    
    
    cursor.close()
    
    return render_template('findItem.html', username=session['username'], item=itemDetail, locations=itemLocations, error=error)
 
#Find all items in an order and the location of each piece    
@app.route('/findOrderItems', methods=['POST'])
def findOrderItems():
    if 'username' not in session:
        return redirect(url_for('login'))

    orderID = request.form['orderID']

    # Initialize variables for template rendering
    orderDetails = None
    items = []
    error = None

    # Connect to the database
    cursor = conn.cursor()

    # Check if the orderID is valid
    cursor.execute(query_fetch_orderID, (orderID,))
    orderDetails = cursor.fetchone()

    if not orderDetails:
        error = f"Order with ID {orderID} not found."
        cursor.close()
        return render_template('findOrderItems.html', username=session['username'], error=error)

    # Fetch items in the order
    cursor.execute(query_fetch_items_by_orderID, (orderID,))
    itemsInOrder = cursor.fetchall()

    if not itemsInOrder:
        error = f"No items found for Order ID {orderID}."
        cursor.close()
        return render_template('findOrderItems.html', username=session['username'], error=error)

    # Fetch locations for each item
    for item in itemsInOrder:
        itemID = item['ItemID']
        cursor.execute(query_fetch_locations_by_itemID, (itemID,))
        item['locations'] = cursor.fetchall()
        items.append(item)

    cursor.close()

    # Render the template with order and item details
    return render_template('findOrderItems.html', username=session['username'], order=orderDetails, items=items)

@app.route('/findItemPage')
def findItemPage():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('findItem.html')

@app.route('/findOrderItemsPage')
def findOrderItemsPage():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('findOrderItems.html')

@app.route('/acceptDonation', methods=['GET', 'POST'])
def acceptDonation():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Check if the user is a staff member or supervisor
    username = session['username']
    cursor = conn.cursor()
    query = '''
        SELECT roleID 
        FROM Person 
        WHERE userName = %s
    '''
    cursor.execute(query, (username,))
    role = cursor.fetchone()

    if not role or role['roleID'] not in ['staff', 'supervisor']:
        cursor.close()
        error = "You are not a staff member."
        return render_template('error.html', error=error)

    donorID = None
    error = None
    if request.method == 'POST':
        donorID = request.form['donorID']

        # Check if the donor exists
        query_user_exists = '''
            SELECT roleID 
            FROM Person 
            WHERE userName = %s
        '''
        cursor.execute(query_user_exists, (donorID,))
        user = cursor.fetchone()

        if not user:
            error = "The user does not exist."
            donorID = None
        elif user['roleID'] != 'donor':
            error = "The user exists but is not registered as a donor."
            donorID = None
        else:
            # Valid donor
            cursor.close()
            return render_template('acceptDonation.html', username=username, donorID=donorID)

    cursor.close()
    return render_template('acceptDonation.html', username=username, error=error, donorID=donorID)


@app.route('/validateDonor', methods=['POST'])
def validateDonor():
    if 'username' not in session:
        return redirect(url_for('login'))

    donorID = request.form['donorID']

    # Check if the donor exists
    cursor = conn.cursor()
    query_user_exists = '''
        SELECT roleID 
        FROM Person 
        WHERE userName = %s
    '''
    cursor.execute(query_user_exists, (donorID,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        # User does not exist
        error = "The user does not exist."
        return render_template('acceptDonation.html', username=session['username'], error=error)

    # Check if the role is 'donor'
    if user['roleID'] != 'donor':
        # User exists but is not a donor
        error = "The user exists but is not registered as a donor."
        return render_template('acceptDonation.html', username=session['username'], error=error)

    # Proceed to donation form (next step)
    return render_template('acceptDonation.html', username=session['username'])



if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
