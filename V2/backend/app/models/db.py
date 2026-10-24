import os
from pathlib import Path

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def _default_sqlite_path() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    data_dir = backend_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "sanctuary_nlp_submission.db"


def _build_database_url() -> str:
    explicit_url = os.getenv("SANCTUARY_DATABASE_URL")
    if explicit_url:
        return explicit_url

    custom_path = os.getenv("SANCTUARY_SQLITE_PATH")
    if custom_path:
        sqlite_path = Path(custom_path).expanduser().resolve()
    else:
        sqlite_path = _default_sqlite_path().resolve()

    # SQLAlchemy expects POSIX-style path separators in SQLite URLs.
    return f"sqlite:///{sqlite_path.as_posix()}"


DATABASE_URL = _build_database_url()
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_database_backend() -> str:
    lowered = DATABASE_URL.lower()
    if lowered.startswith("sqlite"):
        return "sqlite"
    if lowered.startswith("postgresql"):
        return "postgresql"
    return "other"


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db() -> None:
    # Import side effect registers ORM models with SQLAlchemy metadata.
    from app.models import orm  # noqa: F401

    Base.metadata.create_all(bind=engine)
