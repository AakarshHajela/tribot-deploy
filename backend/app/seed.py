from __future__ import annotations

from app.core.config import get_settings
from app.data.database import get_connection, init_db
from app.repositories.users import ensure_demo_user


def main() -> None:
    settings = get_settings()
    init_db()
    with get_connection() as conn:
        ensure_demo_user(
            conn,
            username=settings.demo_email,
            password=settings.demo_password,
        )
    print(f"Seeded demo user: {settings.demo_email}")


if __name__ == "__main__":
    main()
