query_fetch_locations_by_itemID = '''
    SELECT 
        ItemID,
        pieceNum,
        pDescription,
        roomNum, 
        shelfNum
    FROM 
        Piece
    WHERE 
        ItemID = %s
'''

query_fetch_orderID = '''SELECT * FROM ordered WHERE orderID = %s'''

query_fetch_items_by_orderID = '''
    SELECT 
        i.ItemID, 
        i.iDescription, 
        i.color, 
        i.material, 
        i.hasPieces
    FROM 
        ItemIn ii
    JOIN 
        Item i 
    ON 
        ii.ItemID = i.ItemID
    WHERE 
        ii.orderID = %s;                                                    
'''