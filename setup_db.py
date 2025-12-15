import pyodbc
from config import Config

def setup_data():
    print("--- COMPROBANDO BASE DE DATOS ---")
    
    try:
        # Intentar conectar
        cnxn = pyodbc.connect(Config.CONNECTION_STRING)
        cursor = cnxn.cursor()
        print("✅ Conexión Exitosa a SQL Server.")
        
        # 1. Verificar si hay productos
        print("\n🔎 Buscando productos...")
        cursor.execute("SELECT * FROM productos")
        rows = cursor.fetchall()
        
        if len(rows) > 0:
            print(f"✅ ¡Se encontraron {len(rows)} productos!")
            for row in rows:
                print(f"   - ID: {row.id_producto} | {row.nombre} | Stock: {row.stock}")
        else:
            print("⚠️ LA TABLA 'productos' ESTÁ VACÍA o no existe.")
            print("⚙️ Insertando productos de prueba...")
            
            # Insertar datos de prueba
            productos_prueba = [
                ('Polo Algodón Negro', 'Polo básico 100% algodón', 35.50, 50),
                ('Jean Azul Clásico', 'Pantalón denim corte recto', 89.90, 30),
                ('Zapatillas Urbanas', 'Zapatillas blancas casuales', 120.00, 20),
                ('Gorra con Logo', 'Gorra ajustable negra', 25.00, 15)
            ]
            
            cursor.executemany(
                "INSERT INTO productos (nombre, descripcion, precio, stock) VALUES (?, ?, ?, ?)",
                productos_prueba
            )
            cnxn.commit()
            print("✅ ¡4 Productos insertados correctamente!")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("Posible causa: Tu tabla 'productos' no existe o la cadena de conexión falla.")

    finally:
        if 'cnxn' in locals(): cnxn.close()

if __name__ == "__main__":
    setup_data()