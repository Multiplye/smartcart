"""
SmartCart - remove the 9 products whose photos never matched them.

WHY THIS EXISTS
---------------
15 Nepali-market products were added in seed_nepali_products.py, but
their image URLs were composed from memory rather than looked up. A
check confirmed the URLs returned HTTP 200, which proved only that the
file existed - not that it showed the right thing.

An audit (downloading and viewing every image) found 9 of the 15 showed
something completely unrelated:

    32  OnePlus Nord CE 4 Lite        showed an iPhone
    33  Xiaomi 20000mAh Power Bank    showed a newspaper crossword
    35  Type-C Fast Charging Cable    showed a portrait of a man
    36  Pashmina Wool Shawl           showed jackets on a rack
    38  Dhaka Topi                    showed a Prada handbag
    40  Handwoven Cotton Tote Bag     showed folded clothes
    41  Hawkins 5L Pressure Cooker    showed a blender of fruit
    42  Vacuum Insulated Steel Tumbler showed tea and biscuits
    44  Rattan Storage Basket Set     showed Chanel perfume

These are removed on the user's instruction. The 6 whose photos ARE
correct are kept:

    31  Samsung Galaxy A15
    34  boAt Airdopes 141 Earbuds
    37  Himalayan Fleece Hoodie
    39  Goldstar Canvas Shoes
    43  Copper Water Bottle
    45  Block Print Cushion Covers

Products are identified by NAME, not by id. SQLite reuses ids when a
row is deleted, so a hard coded id list is a trap: this script deletes
product id 32, and the next product created will very likely also be
id 32. A second run would then delete an innocent product. Names are
stable; ids are not.

SAFE TO RUN REPEATEDLY. A name that is already gone is simply skipped.

Usage (from the backend folder):
    venv/Scripts/python.exe remove_bad_photo_products.py

    # See what would happen without changing anything:
    venv/Scripts/python.exe remove_bad_photo_products.py --dry-run
"""

import sys

from app import app, db, Product, CartItem, Review, OrderItem

# The products to delete, by exact name.
REMOVE = [
    "OnePlus Nord CE 4 Lite",
    "Xiaomi 20000mAh Power Bank",
    "Type-C Fast Charging Cable",
    "Pashmina Wool Shawl",
    "Dhaka Topi",
    "Handwoven Cotton Tote Bag",
    "Hawkins 5L Pressure Cooker",
    "Vacuum Insulated Steel Tumbler",
    "Rattan Storage Basket Set",
]

# The products kept, listed so the script can prove they are untouched.
KEEP = [
    "Samsung Galaxy A15",
    "boAt Airdopes 141 Earbuds",
    "Himalayan Fleece Hoodie",
    "Goldstar Canvas Shoes",
    "Copper Water Bottle",
    "Block Print Cushion Covers",
]


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    print("=" * 62)
    print("SmartCart - remove products with wrong photos")
    if dry_run:
        print("MODE: dry run, nothing will be changed")
    print("=" * 62)

    with app.app_context():
        before = Product.query.count()
        print(f"\nCatalogue currently holds {before} product(s).\n")

        # ---------------------------------------------------------
        # Safety check: refuse to delete anything that has been used.
        #
        # An order_item or a review points at the product, so deleting
        # the product would leave those rows referring to something that
        # no longer exists. A cart_item is less serious but still means
        # someone is looking at it right now.
        # ---------------------------------------------------------
        blocked = []
        for name in REMOVE:
            product = Product.query.filter_by(name=name).first()

            if not product:
                continue

            used_by = []
            if OrderItem.query.filter_by(product_id=product.id).count():
                used_by.append("an order")
            if Review.query.filter_by(product_id=product.id).count():
                used_by.append("a review")
            if CartItem.query.filter_by(product_id=product.id).count():
                used_by.append("a cart")

            if used_by:
                blocked.append((name, used_by))

        if blocked:
            print("[STOP] Some products are in use and were NOT removed:")
            for name, used_by in blocked:
                print(f"   {name}  - referenced by {', '.join(used_by)}")
            print("\nDelete those orders/reviews first, or leave them be.")
            return

        # ---------------------------------------------------------
        # Remove
        # ---------------------------------------------------------
        print("Removing:")
        removed = 0

        for name in REMOVE:
            product = Product.query.filter_by(name=name).first()

            if not product:
                print(f"   [skip] not in catalogue: {name}")
                continue

            print(f"   [del ] #{product.id:<3} {name}")

            if not dry_run:
                db.session.delete(product)

            removed += 1

        if not dry_run:
            db.session.commit()

        # ---------------------------------------------------------
        # Verify - read back from the database, not from the list
        # ---------------------------------------------------------
        after = Product.query.count()

        print("\nKept (photos verified correct):")
        missing = []
        for name in KEEP:
            row = Product.query.filter_by(name=name).first()
            if row:
                print(f"   [ok  ] #{row.id:<3} {name}")
            else:
                missing.append(name)

        if missing:
            print("\n[WARN] These should still exist but do not:")
            for name in missing:
                print(f"   {name}")

        print("\nProducts per category now:")
        for category in ["Electronics", "Fashion", "Home"]:
            count = Product.query.filter_by(category=category).count()
            print(f"   {category:<14} {count}")

    print(f"\nRemoved {removed}. Catalogue: {before} -> {after}.")
    print("=" * 62)

    if dry_run:
        print("\nDry run only - nothing was written. Re-run without")
        print("--dry-run to apply.")


if __name__ == "__main__":
    main()
