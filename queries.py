query_fetch_locations_by_itemID = '''
    SELECT 
        pieceNum,
        pDescription,
        roomNum, 
        shelfNum, 
        shelfDescription
    FROM 
        Piece
    NATURAL JOIN
        Location
    WHERE 
        ItemID = %s
'''