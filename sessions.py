import db_manager

CARTS = {}
NAMES = {}
CHATS = {}

def get_session(user_id):
    if user_id not in CARTS: CARTS[user_id] = {}
    return CARTS[user_id]

def add_to_cart(user_id, product):
    cart = get_session(user_id)
    pid = product['id']
    if pid in cart: cart[pid]['quantity'] += 1
    else: cart[pid] = {'name': product['nombre'], 'price': product['precio'], 'quantity': 1}

def remove_from_cart(user_id, product_id):
    cart = get_session(user_id)
    try:
        pid = int(product_id)
        if pid in cart: del cart[pid]; return True
        return False
    except: return False

def get_cart_details(user_id):
    cart = get_session(user_id)
    total = sum(i['price'] * i['quantity'] for i in cart.values())
    return cart, total

def clear_cart(user_id):
    if user_id in CARTS: CARTS[user_id] = {}

def save_customer_name(user_id, name):
    NAMES[user_id] = name

def get_customer_name(user_id):
    # 1. RAM: Si existe y NO es anonimo, lo usamos
    if user_id in NAMES:
        n = NAMES[user_id]
        if n and n.lower() not in ['anonimo', 'cliente']: return n
    
    # 2. BD: Buscamos en SQL (la función ya filtra 'anonimo')
    db_name = db_manager.get_client_name(str(user_id))
    if db_name:
        NAMES[user_id] = db_name # Actualizamos RAM
        return db_name
    
    return None # Si no hay nombre válido, devolvemos None

def get_chat_history(user_id):
    if user_id not in CHATS: CHATS[user_id] = []
    return CHATS[user_id]

def add_message_to_history(user_id, role, content):
    if user_id not in CHATS: CHATS[user_id] = []
    CHATS[user_id].append({"role": role, "content": content})
    if len(CHATS[user_id]) > 10: CHATS[user_id] = CHATS[user_id][-10:]