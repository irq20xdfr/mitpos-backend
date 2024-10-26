import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def get_db_connection():
    """Create and return a database connection."""
    try:
        connection = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return connection
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
        return None

def insert_product_sale(name, size, price, quantity, barcode):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res

    try:
        cursor = connection.cursor()
        insert_query = sql.SQL("""
            INSERT INTO product_sales (name, size, price, quantity, barcode)
            VALUES (%s, %s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (name, size, price, quantity, barcode))
        connection.commit()
        print("Product sale inserted successfully")
        res = True
    except (Exception, psycopg2.Error) as error:
        print(f"Error while inserting product sale: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

    return res


def get_inventory():
    inventory = []
    connection = get_db_connection()
    if connection is None:
        return inventory
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, description, quantity, confirmed FROM inventory ORDER BY id ASC")
        inventory_db = cursor.fetchall()
        for item in inventory_db:
            inventory.append({
                "id": item[0],
                "name": item[1],
                "description": item[2],
                "quantity": item[3],
                "confirmed": item[4]
            })
    except (Exception, psycopg2.Error) as error:
        print(f"Error while getting inventory: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return inventory

def add_elements_to_inventory(elements):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        for element in elements:
            # Check if the element already exists
            cursor.execute("SELECT id, quantity FROM inventory WHERE name = %s", (element['name'],))
            existing_element = cursor.fetchone()
            
            if existing_element:
                # If the element exists, update the quantity
                new_quantity = existing_element[1] + (element['quantity'] if type(element['quantity']) == int else int(element['quantity']))
                update_query = sql.SQL("""
                    UPDATE inventory
                    SET quantity = %s, confirmed = -1
                    WHERE id = %s
                """)
                cursor.execute(update_query, (new_quantity, existing_element[0]))
            else:
                # If the element doesn't exist, insert a new one
                insert_query = sql.SQL("""
                    INSERT INTO inventory (name, description, quantity)
                    VALUES (%s, %s, %s)
                """)
                cursor.execute(insert_query, (element['name'], element['description'], element['quantity']))
        
        connection.commit()
        res = True
    except (Exception, psycopg2.Error) as error:
        print(f"Error while adding elements to inventory: {error}")
        return res
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res

def confirm_element_db(id):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE inventory SET confirmed = 1 WHERE id = %s", (id,))
        connection.commit()
        res = True
    except (Exception, psycopg2.Error) as error:
        print(f"Error while confirming element: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res

def add_product_to_inventory_db(barcode, inventory_id):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        
        # Check if the product already exists
        cursor.execute("SELECT COUNT(*) FROM products WHERE barcode = %s", (barcode,))
        product_exists = cursor.fetchone()[0] > 0
        
        if not product_exists:
            cursor.execute("INSERT INTO products (barcode, inventory_id) VALUES (%s, %s)", (barcode, inventory_id))
            connection.commit()
            res = True
        else:
            print(f"Product with barcode {barcode} already exists in inventory.")
    except (Exception, psycopg2.Error) as error:
        print(f"Error while adding product to inventory: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res


def decrease_inventory_quantity(barcode, quantity):
    final_quantity = 0
    connection = get_db_connection()
    if connection is None:
        return final_quantity
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE id IN (SELECT inventory_id FROM products WHERE barcode = %s)", (quantity, barcode))
        connection.commit()

        # Get the current quantity
        cursor.execute("SELECT quantity FROM inventory WHERE id IN (SELECT inventory_id FROM products WHERE barcode = %s)", (barcode,))
        result = cursor.fetchone()
        if result:
            final_quantity = result[0]
    except (Exception, psycopg2.Error) as error:
        print(f"Error while decreasing inventory quantity: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return final_quantity

def get_product_info_db(barcode):
    product_info = None
    connection = get_db_connection()
    if connection is None:
        return product_info
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT i.name, i.description, i.quantity, p.price, p.size FROM inventory i JOIN products p ON i.id = p.inventory_id WHERE p.barcode = %s", (barcode,))
        product_info_db = cursor.fetchone()
        if product_info_db:
            product_info = {
                "name": product_info_db[0],
                "description": product_info_db[1],
                "quantity": product_info_db[2],
                "price": float(product_info_db[3]),
                "size": product_info_db[4]
            }
    except (Exception, psycopg2.Error) as error:
        print(f"Error while getting product info: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return product_info

def update_product_info_db(item):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE products SET price = %s, size = %s WHERE barcode = %s", (item.price, item.size, item.barcode))

        cursor.execute("UPDATE inventory SET name = %s WHERE id IN (SELECT inventory_id FROM products WHERE barcode = %s)", (item.name, item.barcode))
        res = True
        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print(f"Error while updating product info: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res

def delete_from_inventory_db(item_id):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
        connection.commit()
        res = True
    except (Exception, psycopg2.Error) as error:
        print(f"Error while deleting from inventory: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res

def update_name_and_description_db(id, name, description):
    res = False
    connection = get_db_connection()
    if connection is None:
        return res
    
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE inventory SET name = %s, description = %s WHERE id = %s", (name, description, id))
        connection.commit()
        res = True
    except (Exception, psycopg2.Error) as error:
        print(f"Error while updating name and description: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
    return res