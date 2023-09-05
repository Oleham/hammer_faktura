import sqlite3

def execute(sql, values):
    connection = sqlite3.connect("hammer_faktura.db")

    with connection:
        cursor = connection.cursor()
        cursor.execute(sql, values)

        # Get the row id of last inserted row.
        cursor.execute("SELECT last_insert_rowid() FROM invoices")
        result = cursor.fetchone()
        cursor.close()

    return result[0]

def retrieve(sql):
    connection = sqlite3.connect("hammer_faktura.db")

    with connection:
        cursor = connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
    
    return result

def retrieve_one_wvalue(sql, values):
    connection = sqlite3.connect("hammer_faktura.db")

    with connection:
        cursor = connection.cursor()
        cursor.execute(sql, values)
        result = cursor.fetchall()
        cursor.close()
    return result[0][0]

def retrieve_multi_wvalue(sql, values):
    connection = sqlite3.connect("hammer_faktura.db")

    with connection:
        cursor = connection.cursor()
        cursor.execute(sql, values)
        result = cursor.fetchall()
        cursor.close()
    
    return result

