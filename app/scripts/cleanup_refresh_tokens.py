import argparse
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import engine
from app.services.refresh_token_service import RefreshTokenService
from app.repositories.refresh_token_repository import RefreshTokenRepository


async def run_cleanup(revoked_older_than_days: int) -> int:
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as db:
        service = RefreshTokenService(RefreshTokenRepository())
        deleted_count = await service.delete_expired_or_old_revoked(
            db,
            revoked_older_than_days=revoked_older_than_days,
        )
        return deleted_count


def parse_args():
    parser = argparse.ArgumentParser(
        description="Limpia refresh tokens expirados o revocados antiguos."
    )
    parser.add_argument(
        "--revoked-older-than-days",
        type=int,
        default=7,
        help="Borra tokens revocados hace más de N días.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    deleted_count = asyncio.run(
        run_cleanup(
            revoked_older_than_days=args.revoked_older_than_days,
        )
    )
    print(f"Refresh tokens eliminados: {deleted_count}")


if __name__ == "__main__":
    main()