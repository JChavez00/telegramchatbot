import pyodbc

print("--- DRIVERS ODBC INSTALADOS ---")
drivers = pyodbc.drivers()
for d in drivers:
    print(f"- {d}")

if "ODBC Driver 17 for SQL Server" in drivers:
    print("\n✅ ¡TIENES EL DRIVER CORRECTO!")
else:
    print("\n❌ TE FALTA EL DRIVER 'ODBC Driver 17 for SQL Server'.")