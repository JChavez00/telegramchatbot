import json
from groq import Groq
from config import Config
import db_manager
from sessions import (add_to_cart, get_cart_details, clear_cart, remove_from_cart, 
                      save_customer_name, get_customer_name, get_chat_history, add_message_to_history)

client = Groq(api_key=Config.GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant" 

# --- HERRAMIENTAS ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_full_catalog",
            "description": "Obtiene el catálogo.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_item_to_cart",
            "description": "Añade producto.",
            "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}}, "required": ["product_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_item_from_cart",
            "description": "Borra producto.",
            "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}}, "required": ["product_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_shopping_cart",
            "description": "Ver carrito.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_name",
            "description": "Guarda el nombre. USAR SOLO cuando el usuario dice un nombre propio.",
            "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_order",
            "description": "Finaliza el pedido.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# --- LÓGICA ---
def get_full_catalog_logic():
    products = db_manager.get_products()
    if not products: return "⚠️ Base de datos vacía."
    text = "SYSTEM_COMMAND: MUESTRA ESTA LISTA EXACTA SIN RESUMIR:\n\n📋 *CATÁLOGO DISPONIBLE:*\n"
    for p in products:
        text += f"🔹 ID {p['id']}: {p['nombre']} (S/ {p['precio']:.2f})\n"
    text += "\n(Escribe 'quiero el 1' para comprar)"
    return text

def add_item_to_cart_logic(user_id, product_id):
    try:
        product = db_manager.get_product_by_id(int(product_id))
        if not product: return "❌ ID no existe."
        add_to_cart(user_id, product)
        return f"✅ Agregado: {product['nombre']}"
    except: return "❌ Error."

def remove_item_from_cart_logic(user_id, product_id):
    if remove_from_cart(user_id, product_id): return f"🗑️ ID {product_id} eliminado."
    return "⚠️ No se pudo borrar."

def view_shopping_cart_logic(user_id):
    items, total = get_cart_details(user_id)
    if not items: return "Carrito vacío 🛒."
    text = "SYSTEM_COMMAND: MUESTRA ESTA LISTA DE CARRITO EXACTA SIN RESUMIR:\n\n🛒 *TU CARRITO:*\n"
    for id, i in items.items():
        text += f"▪ [ID {id}] {i['name']} (x{i['quantity']}) - S/ {i['price']*i['quantity']:.2f}\n"
    text += f"\n💰 Total: S/ {total:.2f}\nEscribe 'confirmar' para pedir."
    return text

def register_name_logic(user_id, name):
    # 1. Guardar en RAM
    save_customer_name(user_id, name)
    # 2. Guardar en BD INMEDIATAMENTE (Esto es lo que faltaba)
    db_manager.find_or_create_customer(str(user_id), name)
    
    return f"✅ Nombre '{name}' registrado en el sistema. SISTEMA: El usuario ya tiene nombre. EJECUTA 'confirm_order' AHORA MISMO."

def confirm_order_logic(user_id):
    name = get_customer_name(user_id)
    if not name:
        return "FALTA_NOMBRE" 
    
    items, total = get_cart_details(user_id)
    if not items: return "❌ Carrito vacío. Agrega productos antes de confirmar."

    try:
        # Aquí ya tendremos el nombre seguro
        customer_id = db_manager.find_or_create_customer(str(user_id), name)
        order_id = db_manager.save_order(customer_id, items, total)
        if order_id:
            clear_cart(user_id)
            return f"🎉 ¡PEDIDO CONFIRMADO, {name}! Orden #{order_id}. Gracias por tu compra."
        return "❌ Error BD."
    except Exception as e: return f"Error: {e}"

# --- CEREBRO ---
def get_groq_response(user_id, user_message):
    history = get_chat_history(user_id)
    add_message_to_history(user_id, "user", user_message)

    system_instruction = """
    Eres VentasBot. 
    
    REGLAS ESTRICTAS:
    1. Si usas 'get_full_catalog' o 'view_shopping_cart':
       - EL SISTEMA MOSTRARÁ LA LISTA AUTOMÁTICAMENTE.
       - TÚ NO DEBES REPETIR LA LISTA.
       - Tu única tarea es preguntar amablemente: "¿Qué deseas hacer ahora?" o "¿Te ayudo a elegir?".
    2. PROTOCOLO DE CONFIRMACIÓN:
       - Si el usuario dice "confirmar", intenta usar 'confirm_order'.
       - Si recibes "FALTA_NOMBRE", RESPONDE SOLO CON TEXTO: "¿Cuál es tu nombre?". NO USES HERRAMIENTAS.
       - Si el usuario te da su nombre, usa 'register_name'.
    3. NUNCA inventes nombres ("anonimo", "cliente").
    5. 'remove_item_from_cart': Úsala si dicen 'borrar', 'quitar', 'sacar' o 'eliminar'.
    6. Si usas 'view_shopping_cart': MUESTRA TODOS LOS PRODUCTOS DEL CARRITO DETALLADAMENTE. NO RESUMAS.

    """

    messages = [{"role": "system", "content": system_instruction}]
    messages.extend(history)

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, tools=tools, tool_choice="auto", temperature=0.0
        )
        msg = resp.choices[0].message
        final_response_text = msg.content
        forced_text_output = ""

        if msg.tool_calls:
            messages.append(msg)
            for tool in msg.tool_calls:
                fname = tool.function.name
                try:
                    args = json.loads(tool.function.arguments) if tool.function.arguments else {}
                    if args is None: args = {}
                except: args = {}

                res = ""
                pid = args.get("product_id")
                name = args.get("name")

                if fname == "get_full_catalog": 
                    res = get_full_catalog_logic()
                    forced_text_output = res
                elif fname == "view_shopping_cart":
                    res = view_shopping_cart_logic(user_id)
                    forced_text_output = res
                elif fname == "add_item_to_cart": res = add_item_to_cart_logic(user_id, pid) if pid else "Falta ID"
                elif fname == "remove_item_from_cart": res = remove_item_from_cart_logic(user_id, pid) if pid else "Falta ID"
                elif fname == "register_name": res = register_name_logic(user_id, name) if name else "Falta Nombre"
                elif fname == "confirm_order": 
                    res = confirm_order_logic(user_id)
                    if res == "FALTA_NOMBRE":
                        forced_text_output = "No tengo tu nombre registrado. ¿Podrías decírmelo para la factura?"
                        res = "SISTEMA: Se requiere nombre. PREGUNTA AL USUARIO."

                print(f"\n🔎 [DEBUG] {fname} > {str(res)[:50]}...\n")
                messages.append({"tool_call_id": tool.id, "role": "tool", "name": fname, "content": str(res)})
            
            final = client.chat.completions.create(model=MODEL_NAME, messages=messages, temperature=0.0)
            final_response_text = final.choices[0].message.content
        
        if forced_text_output:
            if "No tengo tu nombre" in forced_text_output:
                final_output = forced_text_output
            else:
                final_output = f"{forced_text_output}\n\n{final_response_text}"
        else:
            final_output = final_response_text
        
        if final_output:
            add_message_to_history(user_id, "assistant", final_output)
        
        return final_output or "..."

    except Exception as e:
        print(f"❌ Error: {e}")
        return "Ocurrió un error. Intenta de nuevo."