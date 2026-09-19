"""Add the seller_id column to the product table.

WHY THIS FILE EXISTS
--------------------
In app.py we wrote:

    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"))

and then app.py runs db.create_all() at startup. But db.create_all()
only creates tables that do NOT exist yet. It will not go back and add
a new column to a table that already has rows in it - because doing so
would be a guess about what to put in the existing rows.

So our database still has a product table with no seller_id column, and
the app would crash with "no such column: product.seller_id".

This script does that one change by hand. It is a MIGRATION: a small,
one-off program that moves the database from one shape to the next.

Real projects use a tool called Alembic (or Django migrations, or
Flyway) to do this automatically. For a coursework project a short
script you can read is clearer - and easier to explain in a viva.

SAFE TO RUN MORE THAN ONCE
--------------------------
It checks whether the column already exists and does nothing if so.

USAGE
-----
    cd backend
    python migrate_add_seller_id.py
"""

import os
import sqlite3
import sys

# app.py points SQLAlchemy at "sqlite:///smartcart.db", which for
# Flask-SQLAlchemy means backend/instance/smartcart.db.
HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "instance", "smartcart.db")


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database found at:\n  {DB_PATH}")
        print("\nNothing to migrate - just start the app and it will be created fresh.")
        return 0

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # --- Step 1: what columns does the product table have right now? ---
    cursor.execute("PRAGMA table_info(product)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if not existing_columns:
        print("The product table does not exist yet. Nothing to migrate.")
        connection.close()
        return 0

    print(f"product table currently has {len(existing_columns)} columns:")
    print("  " + ", ".join(existing_columns))

    # --- Step 2: bail out early if we have already done this ---
    if "seller_id" in existing_columns:
        print("\nseller_id is already present - nothing to do.")
        connection.close()
        return 0

    # --- Step 3: count the rows first, so we can report what happened ---
    cursor.execute("SELECT COUNT(*) FROM product")
    row_count = cursor.fetchone()[0]

    # --- Step 4: add the column ---
    #
    # "ALTER TABLE ... ADD COLUMN" with no DEFAULT leaves every existing
    # row as NULL. That is exactly what we want: those products were
    # seeded by us, so they have no seller.
    cursor.execute("ALTER TABLE product ADD COLUMN seller_id INTEGER")

    connection.commit()

    # --- Step 5: prove it worked ---
    cursor.execute("PRAGMA table_info(product)")
    new_columns = [row[1] for row in cursor.fetchall()]

    connection.close()

    if "seller_id" not in new_columns:
        print("\nSomething went wrong - seller_id is still missing.")
        return 1

    print("\nDone. Added seller_id to the product table.")
    print(f"{row_count} existing product(s) now have seller_id = NULL,")
    print("which means they are shop-owned and only an admin can edit them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
