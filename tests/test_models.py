import asyncio
import sys

from sqlalchemy import inspect
from sqlmodel import SQLModel

sys.path.append(".")


async def test_create_tables():
    from app.core.database import engine

    print("\n--- INICIANDO REVISIÓN DE MODELOS EN POSTGRESQL ---")

    print("Sincronizando metadatos (tablas) con la base de datos...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("¡Tablas creadas o verificadas exitosamente!")

        def inspect_tables(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            print(f"Tablas detectadas: {tables}")

            if "users" not in tables:
                raise RuntimeError("La tabla users no fue creada correctamente.")

            columns = inspector.get_columns("users")
            print("\nColumnas detectadas en users:")
            for col in columns:
                print(f"- {col['name']} | {col['type']}")

        await conn.run_sync(inspect_tables)

    await engine.dispose()
    print("\n--- REVISIÓN DE MODELOS FINALIZADA ---")


if __name__ == "__main__":
    try:
        asyncio.run(test_create_tables())
    except KeyboardInterrupt:
        pass
