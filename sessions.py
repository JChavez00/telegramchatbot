# sessions.py

# Diccionario en memoria: { user_id: { product_id: {datos...} } }
CARTS = {}

def get_session(user_id):
    """Obtiene o crea el carrito del usuario."""
    if user_id not in CARTS:
        CARTS[user_id] = {}
    return CARTS[user_id]

def add_to_cart(user_id, product):
    """Agrega un producto al carrito."""
    cart = get_session(user_id)
    product_id = product['id']
    
    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product['nombre'],
            'price': product['precio'],
            'quantity': 1
        }

def remove_from_cart(user_id, product_id):
    """Elimina un producto del carrito dado su ID."""
    cart = get_session(user_id)
    # Convertimos a entero por si acaso viene como texto
    try:
        pid = int(product_id)
    except:
        return False

    if pid in cart:
        del cart[pid]
        return True
    return False

def get_cart_details(user_id):
    """Devuelve los items y el total."""
    cart = get_session(user_id)
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return cart, total

def clear_cart(user_id):
    """Vacía el carrito (usar al confirmar compra)."""
    if user_id in CARTS:
        CARTS[user_id] = {}