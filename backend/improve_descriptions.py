"""Give every seeded product a real description.

WHY THIS MATTERS FOR THE AI
---------------------------
The recommendation engine works purely from the words in a product's
name, category and description. When it was first run, the descriptions
were placeholders that our import script generated:

    "Wireless Headphones - a reliable electronic product for everyday use."
    "Wireless Mouse - a reliable electronic product for everyday use."

Every Electronics product therefore contained the SAME sentence, so the
only differences between them were their names. After the TF-IDF step
filtered out words that appear in fewer than two products, three
products reduced to an identical set of features and all scored a
similarity of exactly 1.0000 - a tie.

Ties are not wrong, but they are not useful either. Good
recommendations depend on good text, and this is the lesson worth
taking to your report: a content-based recommender is only as
informative as the descriptions you feed it.

This script replaces the filler with descriptions that describe what
each product actually IS and WHAT IT IS FOR. You can now see the
engine separate them sensibly: a laptop stand and a mechanical keyboard
are both desk accessories, so they should sit closer to each other than
either does to a pair of running shoes.

SAFE TO RUN MORE THAN ONCE - it just overwrites the descriptions.

USAGE
    cd backend
    python improve_descriptions.py
"""

import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "instance", "smartcart.db")

# Keyed by product name. Chosen to overlap meaningfully with related
# products - note how "portable", "wireless" and "travel" recur across
# the electronics, and how the desk items share "desk" and "work".
DESCRIPTIONS = {
    # ---------------- Electronics ----------------
    "Wireless Headphones": (
        "Over-ear wireless headphones with active noise cancelling, "
        "a thirty hour battery and a built in microphone for calls. "
        "Padded ear cups make them comfortable for long listening "
        "sessions on a commute or while studying."
    ),
    "Smart Watch": (
        "A fitness smart watch that tracks heart rate, daily steps and "
        "sleep, and shows phone notifications on your wrist. Water "
        "resistant, with a seven day battery, for workouts and everyday wear."
    ),
    "Bluetooth Speaker": (
        "A portable Bluetooth speaker with rich bass and a splash "
        "resistant body. Connects wirelessly to any phone or laptop and "
        "runs for twelve hours, making it easy to carry to a picnic or "
        "use around the house."
    ),
    "Wireless Mouse": (
        "An ergonomic wireless mouse with a silent click and adjustable "
        "sensitivity. Connects over Bluetooth or a small USB receiver, "
        "so it works with a laptop, a desktop or a tablet."
    ),
    "Mechanical Keyboard": (
        "A compact mechanical keyboard with tactile switches and "
        "adjustable backlighting. The satisfying key feel suits long "
        "typing sessions, programming work and gaming alike."
    ),
    "Power Bank": (
        "A high capacity portable power bank that charges a phone "
        "several times over. Dual USB output lets you charge two devices "
        "at once, and fast charging tops up a phone in under an hour."
    ),
    "USB-C Charger": (
        "A fast charging USB-C wall adapter with a braided cable. Small "
        "enough to carry in a bag for travel, and powerful enough to "
        "charge a laptop as well as a phone."
    ),
    "Laptop Stand": (
        "An adjustable aluminium laptop stand that raises your screen to "
        "eye level. Worth having for a home desk setup, because it "
        "improves posture and keeps the laptop cool during long work sessions."
    ),
    "Webcam": (
        "A full HD webcam with a built in microphone and automatic light "
        "correction. Clips onto a monitor or laptop screen for video "
        "calls, online classes and streaming."
    ),
    "Wireless Earbuds": (
        "Compact wireless earbuds with touch controls and a charging "
        "case that adds extra hours of listening. Sweat resistant, so "
        "they suit both workouts and everyday commutes."
    ),

    # ---------------- Fashion ----------------
    "Running Shoes": (
        "Lightweight running shoes with a cushioned sole and a breathable "
        "mesh upper. Designed for jogging, gym sessions and long walks on "
        "paved surfaces."
    ),
    "Classic Backpack": (
        "A water resistant backpack with a padded laptop sleeve and "
        "several compartments. Comfortable shoulder straps make it "
        "practical for university, commuting or a short trip."
    ),
    "Casual T-Shirt": (
        "A soft cotton t-shirt with a relaxed fit and a ribbed neckline. "
        "An everyday basic that pairs easily with jeans or a jacket."
    ),
    "Denim Jacket": (
        "A classic denim jacket with button fastening and two chest "
        "pockets. Durable cotton denim that layers well over a t-shirt "
        "in cooler weather."
    ),
    "Classic Sneakers": (
        "Everyday canvas sneakers with a rubber sole and a lace up "
        "front. Simple, comfortable and easy to wear with almost anything."
    ),
    "Leather Wallet": (
        "A slim leather wallet with multiple card slots and a note "
        "compartment. Compact enough for a front pocket, with a "
        "stitched finish that holds up to daily use."
    ),
    "Sunglasses": (
        "Polarised sunglasses with UV protection and a lightweight "
        "frame. Cuts glare on bright days and comes with a hard case."
    ),
    "Wrist Watch": (
        "A minimalist analogue wrist watch with a leather strap and a "
        "stainless steel case. Water resistant, and smart enough for "
        "work without being fussy."
    ),
    "Hoodie": (
        "A fleece lined hoodie with a drawstring hood and a front "
        "pocket. Warm and comfortable, ideal for cool mornings and "
        "relaxed weekends."
    ),
    "Canvas Tote Bag": (
        "A roomy canvas tote bag with reinforced handles. Carries "
        "groceries, books or a laptop, and folds flat when not in use."
    ),

    # ---------------- Home ----------------
    "Coffee Maker": (
        "A drip coffee maker that brews several cups at once into a "
        "glass carafe. Simple controls and a reusable filter make it an "
        "easy addition to a kitchen counter."
    ),
    "Desk Lamp": (
        "A dimmable LED desk lamp with adjustable colour temperature and "
        "a flexible neck. Kind to your eyes for reading, studying or "
        "working late at a desk."
    ),
    "Ceramic Vase": (
        "A glazed ceramic vase with a matte finish. Holds fresh or dried "
        "flowers, and looks good on its own on a shelf or dining table."
    ),
    "Table Clock": (
        "A silent analogue table clock with a clear dial and a wooden "
        "base. No ticking, so it sits comfortably on a bedside table."
    ),
    "Decorative Plant": (
        "An artificial potted plant that needs no watering or sunlight. "
        "Adds greenery to a desk, shelf or corner that gets little "
        "natural light."
    ),
    "Throw Pillow": (
        "A soft decorative cushion with a removable, washable cover. "
        "Brightens up a sofa, armchair or bed without much effort."
    ),
    "Water Bottle": (
        "An insulated stainless steel water bottle that keeps drinks "
        "cold for hours. Leak proof lid, so it is safe to carry in a "
        "backpack."
    ),
    "Kitchen Organizer": (
        "A stackable kitchen organizer for utensils, spices and "
        "containers. Tidies up cluttered cupboards and makes better use "
        "of shelf space."
    ),
    "Scented Candle": (
        "A soy wax scented candle in a reusable glass jar. Burns cleanly "
        "for many hours and fills a room with a warm, calm scent."
    ),
    "Storage Basket": (
        "A woven storage basket with handles, useful for blankets, "
        "toys or laundry. Keeps a room tidy while looking good left out "
        "in the open."
    ),
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database found at:\n  {DB_PATH}")
        return 1

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, description FROM product")
    rows = cursor.fetchall()

    if not rows:
        print("The product table is empty. Run import_products.py first.")
        connection.close()
        return 1

    print("=" * 62)
    print("Improving product descriptions")
    print("=" * 62)

    updated = 0
    unchanged = []
    unknown = []

    for product_id, name, old_description in rows:
        new_description = DESCRIPTIONS.get(name)

        if new_description is None:
            unknown.append(name)
            continue

        if old_description == new_description:
            unchanged.append(name)
            continue

        cursor.execute(
            "UPDATE product SET description = ? WHERE id = ?",
            (new_description, product_id),
        )

        updated += 1

    connection.commit()

    # --- Report ---
    print(f"\nUpdated {updated} product(s).")

    if unchanged:
        print(f"Already current: {len(unchanged)} product(s).")

    if unknown:
        print(f"\nNo description written for {len(unknown)} product(s):")
        for name in unknown:
            print(f"  - {name}")
        print("These keep whatever description they already had.")

    cursor.execute("SELECT COUNT(*) FROM product")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT description) FROM product"
    )
    distinct_descriptions = cursor.fetchone()[0]

    connection.close()

    print(f"\nProducts in database: {total}")
    print(f"Distinct descriptions: {distinct_descriptions}")

    if distinct_descriptions == total:
        print("\nEvery product now has its own description, which is what the")
        print("recommendation engine needs to tell them apart.")
    else:
        print(
            f"\nWarning: {total - distinct_descriptions} product(s) share a "
            "description."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
