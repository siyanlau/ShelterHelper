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

@app.route('/submitItem/<donorID>', methods=['GET', 'POST'])
def submitItem(donorID):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    
    cursor = conn.cursor()
    
    # Fetch category data
    query = "SELECT mainCategory, subCategory FROM Category"
    cursor.execute(query)
    categories = cursor.fetchall()
    cursor.close()

    # Organize data into a dictionary
    category_data = {}
    for row in categories:
        main = row['mainCategory']
        sub = row['subCategory']
        if main not in category_data:
            category_data[main] = []
        category_data[main].append(sub)

    # validate item form submission and redirect to submit pieces
    if request.method == 'POST':
        itemDescription = request.form['itemDescription']
        photo = request.form['photo']
        color = request.form['color']
        isNew = 1 if 'isNew' in request.form else 0
        material = request.form['material']
        mainCategory = request.form['mainCategory']
        subCategory = request.form['subCategory']
        numPieces = int(request.form['numPieces'])

        # Validate inputs
        if not itemDescription or not mainCategory or not subCategory:
            error = "Required fields are missing."
            return render_template('submitItem.html', username=username, donorID=donorID, error=error)
        
        location_data = fetch_location_data()

        # Store data in session or pass along as hidden fields
        return render_template(
            'submitPieces.html',
            username=username,
            donorID=donorID,
            itemDescription=itemDescription,
            photo=photo,
            color=color,
            isNew=isNew,
            material=material,
            mainCategory=mainCategory,
            subCategory=subCategory,
            numPieces=numPieces,
            location_data=location_data  # Pass location data here
        )

    return render_template('submitItem.html', donorID=donorID, category_data=category_data)

@app.route('/submitPieces', methods=['GET', 'POST'])
def submitPieces():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Collect hidden fields for item-level details
        donorID = request.form['donorID']
        itemDescription = request.form['itemDescription']
        photo = request.form['photo']
        color = request.form['color']
        isNew = int(request.form['isNew'])
        material = request.form['material']
        mainCategory = request.form['mainCategory']
        subCategory = request.form['subCategory']
        numPieces = int(request.form['numPieces'])

        cursor = conn.cursor()

        # Insert into Item table
        query_insert_item = '''
            INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query_insert_item, (itemDescription, photo, color, isNew, 1 if numPieces > 1 else 0, material, mainCategory, subCategory))
        conn.commit()
        itemID = cursor.lastrowid

        # Insert into Piece table
        query_insert_piece = '''
            INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        for i in range(1, numPieces + 1):
            piece_description = request.form[f'pDescription{i}']
            length = int(request.form[f'length{i}'])
            width = int(request.form[f'width{i}'])
            height = int(request.form[f'height{i}'])
            room_num = int(request.form[f'roomNum{i}'])
            shelf_num = int(request.form[f'shelfNum{i}'])
            notes = request.form.get(f'pNotes{i}', '')

            # Validate location
            query_check_location = '''
                SELECT * FROM Location 
                WHERE roomNum = %s AND shelfNum = %s
            '''
            cursor.execute(query_check_location, (room_num, shelf_num))
            location = cursor.fetchone()

            if not location:
                cursor.close()
                error = f"Invalid location specified for piece {i}."
                return render_template('submitPieces.html', error=error)

            cursor.execute(query_insert_piece, (itemID, i, piece_description, length, width, height, room_num, shelf_num, notes))
        conn.commit()

        # Insert into DonatedBy table
        query_insert_donatedby = '''
            INSERT INTO DonatedBy (ItemID, userName, donateDate)
            VALUES (%s, %s, NOW())
        '''
        cursor.execute(query_insert_donatedby, (itemID, donorID))
        conn.commit()
        cursor.close()

        return render_template('success.html', success="Donation successfully recorded.")

    location_data = fetch_location_data()
    return render_template(
        'submitPieces.html',
        donorID=request.args.get('donorID'),
        numPieces=request.args.get('numPieces'),
        location_data=location_data
    )


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

def fetch_location_data():
    cursor = conn.cursor()
    query_location_data = "SELECT roomNum, shelfNum FROM location"
    cursor.execute(query_location_data)
    locations = cursor.fetchall()
    cursor.close()

    location_data = {}
    for loc in locations:
        room = loc['roomNum']
        shelf = loc['shelfNum']
        if room not in location_data:
            location_data[room] = []
        location_data[room].append(shelf)
    
    return location_data

if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
