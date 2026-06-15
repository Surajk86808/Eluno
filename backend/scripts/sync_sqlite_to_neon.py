import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.dialects.postgresql import insert

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
SQLITE_DB = BACKEND_DIR / "order_management.db"

sys.path.append(str(BACKEND_DIR))

from app.database import Base  # noqa: E402
from app.models import Alert, DelayLog, Inventory, Order  # noqa: E402


TABLES = [Inventory.__table__, Order.__table__, DelayLog.__table__, Alert.__table__]


def mask_url(url: str) -> str:
    if "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    host = rest.split("@", 1)[1]
    return f"{scheme}://***@{host}"


def fetch_rows(sqlite_engine, table):
    with sqlite_engine.connect() as conn:
        return [dict(row) for row in conn.execute(select(table)).mappings()]


def upsert_rows(postgres_conn, table, rows):
    if not rows:
        return 0

    statement = insert(table).values(rows)
    primary_keys = [column.name for column in table.primary_key.columns]
    update_columns = {
        column.name: getattr(statement.excluded, column.name)
        for column in table.columns
        if column.name not in primary_keys
    }
    statement = statement.on_conflict_do_update(
        index_elements=primary_keys,
        set_=update_columns,
    )
    result = postgres_conn.execute(statement)
    return result.rowcount or 0


def reset_sequence(postgres_conn, table):
    id_column = table.c.get("id")
    if id_column is None:
        return

    max_id = postgres_conn.execute(select(func.max(id_column))).scalar() or 0
    sequence_name = postgres_conn.execute(
        text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
        {"table_name": table.name},
    ).scalar()
    if sequence_name:
        postgres_conn.execute(
            text("SELECT setval(:sequence_name, :value, :is_called)"),
            {
                "sequence_name": sequence_name,
                "value": max_id if max_id > 0 else 1,
                "is_called": max_id > 0,
            },
        )


def table_counts(engine):
    counts = {}
    with engine.connect() as conn:
        for table in TABLES:
            counts[table.name] = conn.execute(select(func.count()).select_from(table)).scalar_one()
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Copy rows from backend/order_management.db into the configured Neon/Postgres database."
    )
    parser.add_argument("--apply", action="store_true", help="Write changes to Neon. Without this, only prints counts.")
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set in .env")
    if database_url.startswith("sqlite"):
        raise SystemExit("DATABASE_URL points to SQLite; set it to the Neon/Postgres URL before syncing.")
    if not SQLITE_DB.exists():
        raise SystemExit(f"SQLite database not found: {SQLITE_DB}")

    sqlite_engine = create_engine(f"sqlite:///{SQLITE_DB}")
    postgres_engine = create_engine(database_url)

    print(f"Source SQLite: {SQLITE_DB}")
    print(f"Target Postgres: {mask_url(database_url)}")
    print(f"Local counts: {table_counts(sqlite_engine)}")
    print(f"Remote counts before: {table_counts(postgres_engine)}")

    if not args.apply:
        print("Dry run only. Re-run with --apply to sync rows.")
        return

    Base.metadata.create_all(bind=postgres_engine)
    with postgres_engine.begin() as conn:
        for table in TABLES:
            rows = fetch_rows(sqlite_engine, table)
            changed = upsert_rows(conn, table, rows)
            reset_sequence(conn, table)
            print(f"Synced {table.name}: {changed} rows inserted/updated from {len(rows)} local rows")

    print(f"Remote counts after: {table_counts(postgres_engine)}")


if __name__ == "__main__":
    main()
