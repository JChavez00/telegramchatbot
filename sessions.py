# sessions.py

# Diccionario en memoria para guardar los carritos: { user_id: { product_id: {datos...} } }
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

def get_cart_details(user_id):
    """Devuelve los items y el total."""
    cart = get_session(user_id)
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return cart, total

def clear_cart(user_id):
    """Vacía el carrito del usuario (úsalo después de confirmar compra)."""
    if user_id in CARTS:
        CARTS[user_id] = {}