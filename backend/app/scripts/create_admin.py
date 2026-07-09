"""Bootstrap the first admin user. Run once per environment: python -m app.scripts.create_admin

There is no public signup endpoint by design (small internal team, admin-provisioned
accounts only) — this script exists so there's a way to create the very first account.
"""

import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import async_session_maker
from app.models.user import User, UserRole


async def main() -> None:
    email = input("Admin email: ").strip()
    full_name = input("Full name: ").strip()
    password = getpass.getpass("Password: ")

    async with async_session_maker() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.admin,
        )
        db.add(user)
        await db.commit()
        print(f"Created admin user {email}.")


if __name__ == "__main__":
    asyncio.run(main())
