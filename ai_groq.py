import json
from groq import Groq
from config import Config
import db_manager
# Importamos la nueva función remove_from_cart
from sessions import add_to_cart, get_cart_details, clear_cart, remove_from_cart

client = Groq(api_key=Config.GROQ_API_KEY)
MODEL_NAME = "llama-3.3-70b-versatile"

# --- DEFINICIÓN DE HERRAMIENTAS ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_full_catalog",
            "description": "Obtiene el catálogo de productos.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_item_to_cart",
            "description": "Añade un producto al carrito. Requiere product_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID numérico"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_item_from_cart",
            "description": "Elimina/Quita un producto del carrito. Requiere product_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID numérico del producto a borrar"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_shopping_cart",
            "description": "Muestra el carrito.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_order",
            "description": "Confirma la compra y guarda en BD.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# --- LÓGICA DE HERRAMIENTAS ---
def get_full_catalog_logic():
    products = db_manager.get_products()
    if not products: return "⚠️ Base de datos vacía."
    text = "SYSTEM_COMMAND: MUESTRA ESTA LISTA EXACTA SIN RESUMIR:\n\n"
    text += "📋 *CATÁLOGO DISPONIBLE:*\n"
    for p in products:
        text += f"🔹 *ID {p['id']}*: {p['nombre']} (S/ {p['precio']:.2f})\n"
    text += "\n(Escribe 'quiero el 1' para comprar)"
    return text

def add_item_to_cart_logic(user_id, product_id):
    try:
        product = db_manager.get_product_by_id(int(product_id))
        if not product: return f"❌ ID {product_id} no existe."
        add_to_cart(user_id, product)
        return f"✅ Agregado: {product['nombre']}"
    except: return "❌ Error al añadir."

def remove_item_from_cart_logic(user_id, product_id):
    success = remove_from_cart(user_id, product_id)
    if success:
        return f"🗑️ Producto ID {product_id} eliminado del carrito."
    else:
        return f"⚠️ No pude borrar el ID {product_id}. ¿Seguro que estaba en tu carrito?"

def view_shopping_cart_logic(user_id):
    items, total = get_cart_details(user_id)
    if not items: return "Tu carrito está vacío 🛒."
    text = "🛒 *CARRITO ACTUAL:*\n"
    for item_id, i in items.items():
        # Mostramos también el ID para que el usuario sepa cuál borrar
        text += f"▪ [ID {item_id}] {i['name']} (x{i['quantity']}) - S/ {i['price']*i['quantity']:.2f}\n"
    text += f"\n💰 Total: S/ {total:.2f}\nEscribe 'confirmar' para pedir o 'borrar [ID]' para quitar."
    return text

def confirm_order_logic(user_id):
    items, total = get_cart_details(user_id)
    if not items: return "❌ Carrito vacío."
    try:
        customer_id = db_manager.find_or_create_customer(str(user_id))
        order_id = db_manager.save_order(customer_id, items, total)
        if order_id:
            clear_cart(user_id)
            return f"🎉 ¡PEDIDO CONFIRMADO! Orden #{order_id}. Gracias."
        return "❌ Error al guardar."
    except Exception as e: return f"Error: {e}"

# --- CEREBRO PRINCIPAL ---
def get_groq_response(user_id, user_message):
    system_instruction = """
    Eres VentasBot. 
    REGLA: Si usas una herramienta, muestra su resultado EXACTO.
    Si el usuario dice 'confirmar', USA la herramienta 'confirm_order'.
    IMPORTANTE:
    1. Si recibes una lista de productos de una herramienta, TU OBLIGACIÓN es mostrarla COMPLETA.
    2. NO resumas la lista.
    3. NO ocultes items.
    4. Copia y pega el texto que te dé la herramienta tal cual.
    5. 'remove_item_from_cart': Úsala si dicen 'borrar', 'quitar', 'sacar' o 'eliminar' un producto.
    Eres VentasBot. Tu misión es vender y ayudar.
    Siempre responde con el resultado que te den las herramientas.
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message}
    ]
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME, 
            messages=messages, 
            tools=tools, 
            tool_choice="auto",
            temperature=0.0
        )
        msg = resp.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tool in msg.tool_calls:
                func_name = tool.function.name
                args = json.loads(tool.function.arguments)
                
                result = ""
                pid = args.get("product_id")

                if func_name == "get_full_catalog": result = get_full_catalog_logic()
                elif func_name == "add_item_to_cart": 
                    if pid: result = add_item_to_cart_logic(user_id, pid)
                    else: result = "Falta ID."
                elif func_name == "remove_item_from_cart": # <--- NUEVA LÓGICA
                    if pid: result = remove_item_from_cart_logic(user_id, pid)
                    else: result = "Falta ID para borrar."
                elif func_name == "view_shopping_cart": result = view_shopping_cart_logic(user_id)
                elif func_name == "confirm_order": result = confirm_order_logic(user_id)
                
                print(f"\n🔎 [DEBUG] {func_name} > {str(result)[:50]}...\n")
                
                messages.append({
                    "tool_call_id": tool.id,
                    "role": "tool",
                    "name": func_name,
                    "content": str(result)
                })
            
            final = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.0)
            return final.choices[0].message.content
        
        return msg.content

    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error técnico."