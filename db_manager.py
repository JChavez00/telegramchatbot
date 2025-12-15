import pyodbc
from config import Config

def get_db_connection():
    try:
        cnxn = pyodbc.connect(Config.CONNECTION_STRING)
        return cnxn
    except Exception as e:
        print(f"Error BD: {e}")
        return None

def get_products():
    """Obtiene los productos disponibles."""
    products = []
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("SELECT id_producto, nombre, precio FROM productos WHERE stock > 0")
            for row in cursor.fetchall():
                products.append({'id': row.id_producto, 'nombre': row.nombre, 'precio': row.precio})
        except: pass
        finally: cursor.close(); cnxn.close()
    return products

def get_product_by_id(product_id):
    product = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("SELECT id_producto, nombre, precio FROM productos WHERE id_producto = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                product = {'id': row.id_producto, 'nombre': row.nombre, 'precio': row.precio}
        except: pass
        finally: cursor.close(); cnxn.close()
    return product

def get_client_name(telegram_id):
    """Recupera el nombre. Devuelve None si no existe o es 'anonimo'."""
    name = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            # Usamos id_telegram (Asegúrate de haber corrido el script SQL de cambio de nombre)
            cursor.execute("SELECT nombre FROM clientes WHERE id_telegram = ?", (telegram_id,))
            row = cursor.fetchone()
            if row and row.nombre:
                # Filtro de seguridad: Si es "anonimo", lo ignoramos
                if row.nombre.lower() not in ['anonimo', 'cliente', 'usuario']:
                    name = row.nombre
        except: pass
        finally: cursor.close(); cnxn.close()
    return name

def find_or_create_customer(telegram_id, client_name=None):
    """Busca/Crea cliente y actualiza su nombre."""
    customer_id = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("SELECT id_cliente FROM clientes WHERE id_telegram = ?", (telegram_id,))
            row = cursor.fetchone()
            
            if row:
                customer_id = row.id_cliente
                if client_name:
                    cursor.execute("UPDATE clientes SET nombre = ? WHERE id_cliente = ?", (client_name, customer_id))
                    cnxn.commit()
            else:
                cursor.execute("INSERT INTO clientes (id_telegram, nombre) VALUES (?, ?)", (telegram_id, client_name))
                cnxn.commit()
                cursor.execute("SELECT @@IDENTITY AS id;")
                customer_id = cursor.fetchone()[0]
        except Exception as e: print(f"Error cliente: {e}")
        finally: cursor.close(); cnxn.close()
    return customer_id

def save_order(customer_id, cart_items, total):
    order_id = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("INSERT INTO pedidos (id_cliente, estado, total) VALUES (?, 'confirmado', ?)", (customer_id, total))
            cnxn.commit()
            cursor.execute("SELECT @@IDENTITY AS id;")
            order_id = cursor.fetchone()[0]

            for item_id, details in cart_items.items():
                cursor.execute("INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad) VALUES (?, ?, ?)", 
                               (order_id, item_id, details['quantity']))
            cnxn.commit()
        except: pass
        finally: cursor.close(); cnxn.close()
    return order_id