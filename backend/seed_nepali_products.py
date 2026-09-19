"""
SmartCart - add 6 Nepali-market products to the catalogue
(2 Electronics, 2 Fashion, 2 Home).

WHY THIS EXISTS
---------------
The original 30 products were generic (Wireless Headphones, Casual
T-Shirt) with round-number prices. For a BIT project presented in Nepal
they did not read as a real shop. This script adds products that a
Nepali customer would actually recognise, priced in realistic NPR.

IT ORIGINALLY ADDED 15, AND 9 WERE REMOVED.

Nine of the fifteen had image URLs that were composed from memory
rather than looked up. Every URL returned HTTP 200 - which proved only
that the FILE existed, not that it showed the right thing. A proper
audit (download each image and look at it) found a Prada handbag for a
Dhaka topi, a newspaper crossword for a power bank, and a portrait of a
man for a USB cable. Those 9 were deleted by
remove_bad_photo_products.py.

So this list now contains ONLY the 6 products whose photos were
verified by eye. Do not add a product here without checking its image
first - the URL returning 200 is not evidence.

SAFE TO RUN REPEATEDLY. It skips any product whose name already exists,
so running it twice adds nothing the second time and never duplicates.

Usage (run from the backend folder):
    venv/Scripts/python.exe seed_nepali_products.py

To remove everything this script adds:
    venv/Scripts/python.exe seed_nepali_products.py --remove
"""

import sys

from app import app, db, Product

# The catalogue categories. The products page hard-codes this same list,
# so a product in any other category would be invisible in the filter.
VALID_CATEGORIES = {"Electronics", "Fashion", "Home"}

# Stock given to each new product.
DEFAULT_STOCK = 12

# Photo credits: Unsplash, free to use, no attribution required.
# Every id here was checked with HTTP 200 before being written in.
IMG = "https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=600&q=80"


def img(photo_id):
    return IMG.format(id=photo_id)


NEPALI_PRODUCTS = [
    # ==========================================================
    # ELECTRONICS
    # ==========================================================
    # Priced against what these actually cost in Kathmandu. Note the
    # Mi Power Bank at 2650 sits above the generic Power Bank already
    # in the catalogue at 1800 - the generic one is the cheap kind, and
    # the gap is deliberate so the recommender has something real to
    # tell apart.
    {
        "name": "Samsung Galaxy A15",
        "category": "Electronics",
        "price": 28500,
        "stock": 8,
        "image": img("1610945265064-0e34e5519bbf"),
        "description": (
            "A 6.5 inch Super AMOLED smartphone with a 50 megapixel "
            "main camera, 5000mAh battery and 128GB of storage. The "
            "handset most commonly bought in Nepal, widely available "
            "with official warranty and local service centres in "
            "Kathmandu and Pokhara."
        ),
    },
    {
        "name": "boAt Airdopes 141 Earbuds",
        "category": "Electronics",
        "price": 3499,
        "stock": 25,
        "image": img("1606220945770-b5b6c2c55bf1"),
        "description": (
            "True wireless earbuds with 42 hours of total playback, "
            "low latency mode for video and gaming, and IPX4 water "
            "resistance for monsoon and workouts. Bluetooth 5.1 with "
            "a built in microphone for calls. One of the best selling "
            "budget earbuds in Nepal."
        ),
    },
    {
        "name": "Himalayan Fleece Hoodie",
        "category": "Fashion",
        "price": 2450,
        "stock": 18,
        "image": img("1556821840-3a63f95609a7"),
        "description": (
            "A thick fleece lined hoodie with a kangaroo pocket, made "
            "for Kathmandu winters where mornings sit near freezing "
            "and afternoons are mild. Holds warmth in the valley and "
            "packs down small enough for a trekking bag."
        ),
    },
    {
        "name": "Goldstar Canvas Shoes",
        "category": "Fashion",
        "price": 1150,
        "stock": 35,
        "image": img("1525966222134-fcfa99b8ae77"),
        "description": (
            "Classic Nepali canvas sneakers with a rubber sole and "
            "lace up front. Cheap, breathable and easy to wash, which "
            "is why they are the standard school shoe across Nepal. "
            "Suits everyday wear on dusty streets and in monsoon."
        ),
    },
    {
        "name": "Copper Water Bottle",
        "category": "Home",
        "price": 1150,
        "stock": 16,
        "image": img("1602143407151-7111542de6e8"),
        "description": (
            "A hand beaten pure copper bottle. Storing drinking water "
            "in copper overnight is a long standing household practice "
            "in South Asia, traditionally believed to have health "
            "benefits. Holds about a litre, with a leak proof cap."
        ),
    },
    {
        "name": "Block Print Cushion Covers",
        "category": "Home",
        "price": 950,
        "stock": 28,
        "image": img("1584100936595-c0654b55a2e2"),
        "description": (
            "A pair of 16 inch cotton cushion covers with hand block "
            "printed patterns, finished with a hidden zip. Sold in "
            "pairs because single cushions rarely look right on a "
            "sofa. Machine washable and the print does not run."
        ),
    },
]


def remove() -> None:
    """Delete every product this script added, by exact name."""
    names = [p["name"] for p in NEPALI_PRODUCTS]

    with app.app_context():
        rows = Product.query.filter(Product.name.in_(names)).all()

        if not rows:
            print("\nNothing to remove - none of these products are in the catalogue.")
            return

        # A product that has been ordered cannot simply be deleted - the
        # order_item rows point at it, and a foreign key would be left
        # dangling. Refuse rather than corrupt an order.
        from app import OrderItem

        blocked = []
        for row in rows:
            used = OrderItem.query.filter_by(product_id=row.id).count()
            if used:
                blocked.append((row.name, used))

        if blocked:
            print("\n[STOP] These products have been ordered and will not be removed:")
            for name, count in blocked:
                print(f"   {name}  ({count} order line(s))")
            print("\nDelete the orders first, or leave them in place.")
            return

        for row in rows:
            print(f"   removing: {row.name}")
            db.session.delete(row)

        db.session.commit()
        print(f"\nRemoved {len(rows)} product(s). Catalogue now has {Product.query.count()}.")


def main() -> None:
    if "--remove" in sys.argv:
        remove()
        return

    print("=" * 62)
    print("SmartCart - add Nepali market products")
    print("=" * 62)

    with app.app_context():
        before = Product.query.count()
        print(f"\nCatalogue currently holds {before} product(s).")

        added = 0
        skipped = 0

        for item in NEPALI_PRODUCTS:
            # Skip anything already there, so re-running is harmless.
            if Product.query.filter_by(name=item["name"]).first():
                print(f"   [skip] already present: {item['name']}")
                skipped += 1
                continue

            # Guard against a typo putting a product somewhere the
            # products page cannot filter to.
            if item["category"] not in VALID_CATEGORIES:
                print(f"   [STOP] bad category on {item['name']}: {item['category']}")
                return

            db.session.add(
                Product(
                    name=item["name"],
                    description=item["description"],
                    price=float(item["price"]),
                    category=item["category"],
                    image=item["image"],
                    stock=item.get("stock", DEFAULT_STOCK),
                )
            )
            print(f"   [add ] {item['category']:<12} Rs. {item['price']:>7,}  {item['name']}")
            added += 1

        db.session.commit()

        after = Product.query.count()

        # Summary by category, read back from the database rather than
        # from the list above, so it reflects what is actually stored.
        print("\nProducts per category now:")
        for category in sorted(VALID_CATEGORIES):
            count = Product.query.filter_by(category=category).count()
            print(f"   {category:<14} {count}")

    print(f"\nAdded {added}, skipped {skipped}. Catalogue: {before} -> {after}.")
    print("=" * 62)


if __name__ == "__main__":
    main()
