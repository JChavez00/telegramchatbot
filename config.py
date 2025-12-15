import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- Configuración de Base de Datos ---
    DB_SERVER = os.getenv('DB_SERVER')
    DB_NAME = os.getenv('DB_NAME')
    
    # --- ESTA ES LA LÍNEA QUE FALTABA ---
    # Crea el texto mágico que permite a Python entrar a SQL Server
    CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;'
    
    # --- Credenciales de API ---
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')