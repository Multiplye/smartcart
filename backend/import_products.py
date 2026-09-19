"""
SmartCart - Import Products Script
==================================

PURPOSE
-------
Copy the ~30 demo products that live in the React frontend file:

    smartcart/smartcart/src/data/products.js

into the SQLite database (backend/instance/smartcart.db) so the backend
becomes the single source of truth for product data.

HOW TO RUN (from the backend folder, with venv activated):

    python import_products.py

SAFETY
------
This script DELETES all existing rows in the Product table first, so the
database always ends up in exactly the same state as products.js.
(Otherwise running it twice would create duplicate products.)

It only touches the Product table. No other table is affected.
"""

import re
from pathlib import Path

from app import app, db, Product

# -------------------------------------------------------------------
# 1. Where is products.js?
# -------------------------------------------------------------------
# This file lives at:  .../smartcart/backend/import_products.py
# The frontend file is at: .../smartcart/smartcart/smartcart/src/data/products.js
#
# So we go:  backend/  ->  parent (smartcart/)  ->  smartcart/smartcart/src/data/
PRODUCTS_JS = (
    Path(__file__).resolve().parent          # .../smartcart/backend
    .parent                                  # .../smartcart
    / "smartcart"                            # .../smartcart/smartcart
    / "smartcart"
    / "src"
    / "data"
    / "products.js"
)

# -------------------------------------------------------------------
# 2. Placeholder description builder
# -------------------------------------------------------------------
# products.js has no description field, but our Product column is
# nullable=False, so every product needs some text.
# Step 1 writes this placeholder; later (in product CRUD) the seller/admin
# will edit real descriptions.
DESCRIPTION_TEMPLATES = {
    "Electronics": "{name} - a reliable electronic product for everyday use.",
    "Fashion": "{name} - comfortable and stylish, made for daily wear.",
    "Home": "{name} - a practical addition for your home and living space.",
}

DEFAULT_DESCRIPTION = "{name} - quality product available at SmartCart."
DEFAULT_STOCK = 10


def build_description(name, category):
    template = DESCRIPTION_TEMPLATES.get(category, DEFAULT_DESCRIPTION)
    return template.format(name=name)


# -------------------------------------------------------------------
# 3. Parse products.js
# -------------------------------------------------------------------
def parse_products_js(file_path):
    """Read products.js as plain text and pull out each product object.

    We deliberately use a simple regex instead of importing JavaScript,
    because Python cannot run .js files and we do not want to add a
    Node.js dependency to the backend.
    """
    text = file_path.read_text(encoding="utf-8")

    # Each product in the file looks like:
    #   {
    #     id: 1,
    #     name: "Wireless Headphones",
    #     category: "Electronics",
    #     price: 2500,
    #     image:
    #       "https://images.unsplash.com/...",
    #   },
    # The fields always appear in this order, so we match them one by one.
    # re.DOTALL lets "\s*" also eat the newlines between fields.
    object_pattern = re.compile(
        r"id:\s*(\d+),\s*"
        r'name:\s*"([^"]+)",\s*'
        r'category:\s*"([^"]+)",\s*'
        r"price:\s*(\d+(?:\.\d+)?),\s*"
        r'image:\s*"([^"]+)"',
        re.DOTALL,
    )

    products = []
    for match in object_pattern.finditer(text):
        product_id, name, category, price, image = match.groups()
        products.append(
            {
                "name": name,
                "category": category,
                "price": float(price),
                "image": image,
            }
        )

    return products


# -------------------------------------------------------------------
# 4. Main import routine
# -------------------------------------------------------------------
def main():
    print("=" * 60)
    print("SmartCart - Import products.js into SQLite")
    print("=" * 60)

    # --- Check the source file exists ---
    if not PRODUCTS_JS.exists():
        print(f"\n[ERROR] Could not find:\n   {PRODUCTS_JS}")
        print("\nCheck that the path to products.js is still correct.")
        return

    print(f"\n[1/3] Reading: {PRODUCTS_JS}")
    products = parse_products_js(PRODUCTS_JS)
    print(f"      Found {len(products)} products in products.js")

    if not products:
        print("\n[ERROR] No products were parsed. The file format may have changed.")
        return

    # --- Write them into the database ---
    with app.app_context():
        print("\n[2/3] Clearing old rows from the Product table...")
        deleted = db.session.query(Product).delete()
        db.session.commit()
        print(f"      Deleted {deleted} existing product row(s).")

        print("\n[3/3] Inserting products...")
        for item in products:
            product = Product(
                name=item["name"],
                description=build_description(item["name"], item["category"]),
                price=item["price"],
                category=item["category"],
                image=item["image"],
                stock=DEFAULT_STOCK,
            )
            db.session.add(product)

        db.session.commit()

        total = Product.query.count()

    print(f"      Done. Product table now contains {total} products.")

    # --- Summary by category ---
    print("\nProducts per category:")
    counts = {}
    for item in products:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    for category, count in sorted(counts.items()):
        print(f"   {category:<15} {count}")

    print("\n" + "=" * 60)
    print("Import complete. Restart the Flask server to see the data")
    print("at http://127.0.0.1:5000/api/products")
    print("=" * 60)


if __name__ == "__main__":
    main()
