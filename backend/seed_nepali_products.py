"""
SmartCart - add 15 Nepali-market products (5 Electronics, 5 Fashion,
5 Home) to the catalogue.

WHY THIS EXISTS
---------------
The original 30 products were generic (Wireless Headphones, Casual
T-Shirt) with round-number prices. For a BIT project presented in Nepal
they did not read as a real shop. This script adds a second wave of
products that a Nepali customer would actually recognise, priced in
realistic NPR.

SAFE TO RUN REPEATEDLY. It skips any product whose name already exists,
so running it twice adds nothing the second time and never duplicates.

Usage (run from the backend folder):
    venv/Scripts/python.exe seed_nepali_products.py

To remove everything this script added:
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
        "name": "OnePlus Nord CE 4 Lite",
        "category": "Electronics",
        "price": 42999,
        "stock": 6,
        "image": img("1592899677977-9c10ca588bbd"),
        "description": (
            "A mid range 5G smartphone with a 120Hz AMOLED display, "
            "5500mAh battery and 80W fast charging that refills the "
            "phone in about half an hour. Snapdragon processor and "
            "clean OxygenOS, popular with students and young "
            "professionals who want speed without the flagship price."
        ),
    },
    {
        "name": "Xiaomi 20000mAh Power Bank",
        "category": "Electronics",
        "price": 2650,
        "stock": 20,
        "image": img("1585338107529-13afc5f02586"),
        "description": (
            "A 20000mAh power bank with dual USB output and 18W fast "
            "charging. Big enough to recharge a phone four or five "
            "times, which matters during load shedding and on long "
            "bus journeys on Nepal's highways. Charges two devices "
            "at once."
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
        "name": "Type-C Fast Charging Cable",
        "category": "Electronics",
        "price": 450,
        "stock": 40,
        "image": img("1583864697784-a0efc8379f70"),
        "description": (
            "A braided 1.5 metre Type-C cable rated for 3A fast "
            "charging and 480Mbps data transfer. Reinforced connectors "
            "resist the fraying that kills cheaper cables, and the "
            "extra length reaches a wall socket from a bed or a desk."
        ),
    },
    # ==========================================================
    # FASHION
    # ==========================================================
    # The Pashmina is the one genuinely high value item in the shop.
    # A real 100% pashmina shawl is 8000 rupees and up, and that price
    # is part of why it exists here: it gives the recommender a large
    # price signal to work with, alongside the 450 rupee cable at the
    # other end.
    {
        "name": "Pashmina Wool Shawl",
        "category": "Fashion",
        "price": 8500,
        "stock": 7,
        "image": img("1601924994987-69e26d50dc26"),
        "description": (
            "A handwoven shawl in a soft pashmina and wool blend, with "
            "traditional Himalayan patterning on the border. Warm "
            "without being heavy, and light enough to fold into a bag. "
            "A common gift for relatives visiting from abroad, and a "
            "staple of the Thamel craft shops."
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
        "name": "Dhaka Topi",
        "category": "Fashion",
        "price": 550,
        "stock": 30,
        "image": img("1590739225287-bd31519780c3"),
        "description": (
            "The traditional Nepali cap, handwoven from dhaka cloth in "
            "a geometric pattern. Worn for festivals, formal occasions "
            "and official dress, and given as a mark of respect. "
            "Authentic handloom cotton rather than printed imitation, "
            "so the weave varies slightly from piece to piece."
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
        "name": "Handwoven Cotton Tote Bag",
        "category": "Fashion",
        "price": 750,
        "stock": 22,
        "image": img("1544441893-675973e31985"),
        "description": (
            "A shoulder bag in handwoven cotton with a wide gusset for "
            "groceries or books, and reinforced shoulder straps. Made "
            "by women's cooperatives in Bhaktapur. A practical "
            "alternative to plastic bags for the daily vegetable "
            "market."
        ),
    },
    # ==========================================================
    # HOME
    # ==========================================================
    {
        "name": "Hawkins 5L Pressure Cooker",
        "category": "Home",
        "price": 5250,
        "stock": 9,
        "image": img("1585515320310-259814833e62"),
        "description": (
            "A five litre aluminium pressure cooker with a safety "
            "valve, used daily in most Nepali kitchens for dal bhat, "
            "rice and beans. The 5 litre size is right for a family "
            "of four. Cuts cooking time and fuel use substantially "
            "compared with an open pot."
        ),
    },
    {
        "name": "Vacuum Insulated Steel Tumbler",
        "category": "Home",
        "price": 1450,
        "stock": 24,
        "image": img("1544787219-7f47ccb76574"),
        "description": (
            "A 500ml double walled stainless steel tumbler that keeps "
            "tea hot for about six hours and cold drinks cold for "
            "twelve. The lid seals properly, so it can go in a bag "
            "without leaking, to an office or on a motorbike commute."
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
        "name": "Rattan Storage Basket Set",
        "category": "Home",
        "price": 1950,
        "stock": 12,
        "image": img("1595425970377-c9703cf48b6d"),
        "description": (
            "A set of three nested baskets woven from rattan by "
            "craftspeople in the Terai. Useful for holding fruit, "
            "folded clothes or the odds and ends that collect in a "
            "room, and sturdy enough to stack. Lighter and warmer "
            "looking than plastic storage."
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
