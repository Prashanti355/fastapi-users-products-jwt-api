import sys
import asyncio
from pathlib import Path
from sqlalchemy import text

# Agrega la raíz del proyecto al path para poder importar "app"
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import engine


async def test_connection():
    print("Iniciando prueba de conexión con PostgreSQL...")

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            value = result.scalar_one()
            print(f"Conexión exitosa. Resultado de SELECT 1: {value}")
    except Exception as e:
        print(f"Error de conexión: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        pass