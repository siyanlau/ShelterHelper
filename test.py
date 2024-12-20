#Import Flask Library
from flask import render_template, request, session, url_for, redirect, flash
import pymysql.cursors
from app import app
import hashlib, os
from queries import query_fetch_locations_by_itemID, query_fetch_orderID, query_fetch_items_by_orderID

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='1929ulrica',
                       db='donation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# Fetch room and shelf data for GET request
cursor = conn.cursor()
query_location_data = "SELECT roomNum, shelfNum FROM location"
cursor.execute(query_location_data)
locations = cursor.fetchall()
cursor.close()

# Organize location data
location_data = {}
for loc in locations:
    room = loc['roomNum']
    shelf = loc['shelfNum']
    if room not in location_data:
        location_data[room] = []
    location_data[room].append(shelf)

# Debugging: Print location_data to confirm it's correct
print(f"location_data: {location_data}")