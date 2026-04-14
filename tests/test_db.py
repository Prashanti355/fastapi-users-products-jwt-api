import sys
import asyncio
from uuid import uuid4

sys.path.append(".")


async def create_data_test():
    from app.core.database import AsyncSessionLocal, engine
    from app.core.security import get_password_hash
    from app.models.user import User

    print("\n--- INICIANDO PRUEBA DE BASE DE DATOS ---")

    async with AsyncSessionLocal() as session:
        test_username = f"test_{str(uuid4())[:8]}"

        print(f"Creando usuario de prueba con username: {test_username}...")

        new_user = User(
            username=test_username,
            email="lore@example.com",
            password=get_password_hash("admin123"),
            first_name="Lorena",
            last_name="Martinez",
            is_superuser=True,
            is_active=True
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print("¡Usuario creado exitosamente!")

        print("\n--- RESUMEN DEL REGISTRO ---")
        print(f"ID (UUID): {new_user.id}")
        print(f"Username: {new_user.username}")
        print(f"Email: {new_user.email}")
        print(f"Password Hash: {new_user.password[:20]}...")
        print(f"Nombre Completo: {new_user.full_name}")
        print(f"Fecha Registro: {new_user.date_joined}")

        if new_user.age:
            print(f"Edad calculada: {new_user.age}")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(create_data_test())
    except KeyboardInterrupt:
        pass