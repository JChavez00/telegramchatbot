import pyodbc
from config import Config

# --- Funciones para el Panel de Administrador ---

def add_product(nombre, descripcion, precio, stock):
    """Agrega un nuevo producto a la base de datos."""
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute(
                "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (?, ?, ?, ?)",
                (nombre, descripcion, precio, stock)
            )
            cnxn.commit()
            return True
        except Exception as e:
            print(f"Error al agregar producto: {e}")
            return False
        finally:
            cursor.close()
            cnxn.close()
    return False

def get_sales_stats():
    """Obtiene estadísticas básicas para el dashboard."""
    stats = {}
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            # 1. Total Ingresos
            cursor.execute("SELECT SUM(total) FROM pedidos")
            row = cursor.fetchone()
            stats['ingresos'] = row[0] if row[0] else 0

            # 2. Total Pedidos
            cursor.execute("SELECT COUNT(*) FROM pedidos")
            row = cursor.fetchone()
            stats['pedidos'] = row[0]

            # 3. Productos más vendidos (Top 5)
            cursor.execute("""
                SELECT TOP 5 p.nombre, SUM(dp.cantidad) as total
                FROM detalle_pedidos dp
                JOIN productos p ON dp.id_producto = p.id_producto
                GROUP BY p.nombre
                ORDER BY total DESC
            """)
            stats['top_productos'] = cursor.fetchall()

        except Exception as e:
            print(f"Error al obtener estadísticas: {e}")
        finally:
            cursor.close()
            cnxn.close()
    return stats



def get_db_connection():
    """Crea y devuelve un objeto de conexión a la base de datos."""
    try:
        cnxn = pyodbc.connect(Config.CONNECTION_STRING)
        return cnxn
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# --- NUEVA FUNCIÓN ---
def get_products():
    """Obtiene todos los productos de la base de datos."""
    products = []
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("SELECT id_producto, nombre, precio FROM productos WHERE stock > 0")
            # Convertimos cada fila en un diccionario para un manejo más fácil
            for row in cursor.fetchall():
                products.append({'id': row.id_producto, 'nombre': row.nombre, 'precio': row.precio})
        except Exception as e:
            print(f"Error al obtener productos: {e}")
        finally:
            cursor.close()
            cnxn.close()
    return products

# Aquí agregaremos más funciones después...


def get_product_by_id(product_id):
    """Obtiene un solo producto por su ID."""
    product = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            cursor.execute("SELECT id_producto, nombre, precio FROM productos WHERE id_producto = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                product = {'id': row.id_producto, 'nombre': row.nombre, 'precio': row.precio}
        except Exception as e:
            print(f"Error al obtener producto por ID: {e}")
        finally:
            cursor.close()
            cnxn.close()
    return product


# funcion para registrar al cliente y guardar el pedido

def find_or_create_customer(whatsapp_number):
    """Encuentra un cliente por su número o lo crea si no existe."""
    customer_id = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            # Primero, intenta encontrar al cliente
            cursor.execute("SELECT id_cliente FROM clientes WHERE numero_whatsapp = ?", (whatsapp_number,))
            row = cursor.fetchone()
            if row:
                customer_id = row.id_cliente
            else:
                # Si no existe, lo crea y obtiene su nuevo ID
                cursor.execute("INSERT INTO clientes (numero_whatsapp) VALUES (?)", (whatsapp_number,))
                cnxn.commit()
                # Obtenemos el ID del cliente recién creado
                cursor.execute("SELECT @@IDENTITY AS id;")
                customer_id = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error al buscar/crear cliente: {e}")
        finally:
            cursor.close()
            cnxn.close()
    return customer_id

def save_order(customer_id, cart_items, total):
    """Guarda el pedido en las tablas pedidos y detalle_pedidos."""
    order_id = None
    cnxn = get_db_connection()
    if cnxn:
        cursor = cnxn.cursor()
        try:
            # 1. Insertar en la tabla 'pedidos'
            cursor.execute("INSERT INTO pedidos (id_cliente, estado, total) VALUES (?, 'confirmado', ?)", (customer_id, total))
            cnxn.commit()
            # Obtenemos el ID del pedido recién creado
            cursor.execute("SELECT @@IDENTITY AS id;")
            order_id = cursor.fetchone()[0]

            # 2. Insertar cada producto en la tabla 'detalle_pedidos'
            for item_id, details in cart_items.items():
                cursor.execute(
                    "INSERT INTO detalle_pedidos (id_pedido, id_producto, cantidad) VALUES (?, ?, ?)",
                    (order_id, item_id, details['quantity'])
                )
            cnxn.commit()
        except Exception as e:
            print(f"Error al guardar el pedido: {e}")
        finally:
            cursor.close()
            cnxn.close()
    return order_id
# def get_products():
# def create_order(customer_id, cart):
# def find_or_create_customer(whatsapp_number):