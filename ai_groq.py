import json
from groq import Groq
from config import Config
import db_manager
# Importamos clear_cart también
from sessions import add_to_cart, get_cart_details, clear_cart

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
                    "product_id": {"type": "integer", "description": "ID numérico del producto"},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_shopping_cart",
            "description": "Muestra el contenido del carrito.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- NUEVA HERRAMIENTA ---
    {
        "type": "function",
        "function": {
            "name": "confirm_order",
            "description": "Confirma la compra, guarda el pedido en la base de datos y vacía el carrito. Úsala cuando el usuario diga 'confirmar', 'comprar' o 'finalizar pedido'.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# --- LÓGICA DE HERRAMIENTAS ---
def get_full_catalog_logic():
    products = db_manager.get_products()
    if not products: return "⚠️ Error: Base de datos vacía."
    text = "LISTA_PRODUCTOS:\n"
    for p in products:
        text += f"- ID {p['id']}: {p['nombre']} (S/ {p['precio']:.2f})\n"
    return text

def add_item_to_cart_logic(user_id, product_id):
    try:
        product = db_manager.get_product_by_id(int(product_id))
        if not product: return f"❌ ID {product_id} no existe."
        add_to_cart(user_id, product)
        return f"✅ Agregado: {product['nombre']}"
    except: return "❌ Error al añadir."

def view_shopping_cart_logic(user_id):
    items, total = get_cart_details(user_id)
    if not items: return "Tu carrito está vacío 🛒."
    text = "🛒 *CARRITO:*\n"
    for _, i in items.items():
        text += f"▪ {i['name']} (x{i['quantity']}) - S/ {i['price']*i['quantity']:.2f}\n"
    text += f"\n💰 Total: S/ {total:.2f}\nEscribe 'confirmar' para procesar."
    return text

def confirm_order_logic(user_id):
    """Lógica para guardar el pedido en SQL Server."""
    items, total = get_cart_details(user_id)
    if not items:
        return "❌ No puedes confirmar porque tu carrito está vacío."
    
    try:
        # 1. Buscar o crear cliente en la BD usando el ID de Telegram
        customer_id = db_manager.find_or_create_customer(str(user_id))
        
        # 2. Guardar el pedido
        order_id = db_manager.save_order(customer_id, items, total)
        
        if order_id:
            # 3. Vaciar el carrito si se guardó bien
            clear_cart(user_id)
            return f"🎉 ¡PEDIDO CONFIRMADO! Tu número de orden es #{order_id}. Gracias por comprar."
        else:
            return "❌ Error al guardar el pedido en la base de datos."
            
    except Exception as e:
        return f"❌ Error técnico al procesar compra: {e}"

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
            temperature=0.1
        )
        msg = resp.choices[0].message
        
        if msg.tool_calls:
            messages.append(msg)
            for tool in msg.tool_calls:
                func_name = tool.function.name
                args = json.loads(tool.function.arguments)
                
                result = ""
                if func_name == "get_full_catalog": result = get_full_catalog_logic()
                elif func_name == "add_item_to_cart": 
                    pid = args.get("product_id")
                    if pid: result = add_item_to_cart_logic(user_id, pid)
                    else: result = "Error: Falta ID."
                elif func_name == "view_shopping_cart": result = view_shopping_cart_logic(user_id)
                elif func_name == "confirm_order": result = confirm_order_logic(user_id) # <--- AQUÍ EJECUTAMOS LA CONFIRMACIÓN
                
                print(f"\n🔎 [DEBUG] Resultado de {func_name}:\n{result}\n")
                
                messages.append({
                    "tool_call_id": tool.id,
                    "role": "tool",
                    "name": func_name,
                    "content": str(result)
                })
            
            final = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.1)
            return final.choices[0].message.content
        
        return msg.content

    except Exception as e:
        print(f"❌ Error Groq: {e}")
        return "Error técnico."