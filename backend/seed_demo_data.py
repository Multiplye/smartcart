"""
Seed the database with a realistic demo dataset.

Why this exists: an empty shop cannot demonstrate an AI recommender.
The recommendation engine learns from ORDER HISTORY, so with zero
orders every visitor gets the popularity fallback - which is correct
behaviour but proves nothing. This script creates a handful of
believable customers, places orders for them, and writes reviews.

The result is a database where you can log in as a returning customer,
open the recommendations page, and see it genuinely responding to what
that account bought.

Run it from the backend folder:

    ./venv/Scripts/python.exe seed_demo_data.py

It is safe to run more than once - it checks for each account first
and tells you what it found. To start clean instead:

    ./venv/Scripts/python.exe seed_demo_data.py --reset

--reset removes ONLY the demo accounts below and their data. It never
touches the 30 real products.

PASSWORDS ARE ALL "demo1234" - this is demonstration data for a
college project, not production. Do not reuse these anywhere real.
"""

import sys

from app import (
    app,
    db,
    User,
    Product,
    CartItem,
    Order,
    OrderItem,
    Review,
)

# ---------------------------------------------------------------------
# THE DEMO CAST
# ---------------------------------------------------------------------

# Each person has a taste, so their recommendations differ. That is the
# point of the exercise: two accounts should NOT see the same list.
DEMO_PASSWORD = "demo1234"

DEMO_USERS = [
    {
        "name": "Aarav Sharma",
        "email": "aarav@demo.smartcart",
        "role": "buyer",
        # An electronics person.
        "buys": ["Wireless Headphones", "Mechanical Keyboard", "Power Bank"],
        "reviews": [
            ("Mechanical Keyboard", 5, "Typing on this is a pleasure. Solid build."),
            ("Power Bank", 4, "Charges my phone about twice. Good for travel."),
        ],
    },
    {
        "name": "Priya Thapa",
        "email": "priya@demo.smartcart",
        "role": "buyer",
        # A home and living person.
        "buys": ["Scented Candle", "Kitchen Organizer", "Desk Lamp"],
        "reviews": [
            ("Scented Candle", 5, "Smells wonderful and burns for ages."),
            ("Desk Lamp", 4, "Perfect brightness for evening study."),
        ],
    },
    {
        "name": "Bikash Gurung",
        "email": "bikash@demo.smartcart",
        "role": "buyer",
        # Fashion and accessories.
        "buys": ["Running Shoes", "Classic Backpack", "Sunglasses"],
        "reviews": [
            ("Running Shoes", 4, "Comfortable on long walks."),
            ("Classic Backpack", 3, "Good size but the zip feels a little thin."),
        ],
    },
    {
        "name": "Sunita Rai",
        "email": "sunita@demo.smartcart",
        "role": "seller",
        # A seller who has also bought a couple of things, so the
        # recommendations page works for this account too.
        "buys": ["Wireless Mouse", "Laptop Stand"],
        "reviews": [],
    },
    {
        "name": "SmartCart Admin",
        "email": "admin@demo.smartcart",
        "role": "admin",
        "buys": [],
        "reviews": [],
    },
]

DEMO_EMAILS = [person["email"] for person in DEMO_USERS]


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def find_user(email):
    return User.query.filter_by(email=email).first()


def find_product(name):
    return Product.query.filter_by(name=name).first()


def wipe_demo_data():
    """Remove the demo accounts and everything belonging to them.

    Deliberately explicit about what it deletes. It never touches
    products, because the 30 real ones are the catalogue this whole
    project is about.
    """

    users = User.query.filter(User.email.in_(DEMO_EMAILS)).all()

    if not users:
        print("  Nothing to remove - no demo accounts found.")
        return 0

    user_ids = [user.id for user in users]

    order_ids = [
        row.id
        for row in db.session.query(Order.id)
        .filter(Order.user_id.in_(user_ids))
        .all()
    ]

    if order_ids:
        removed_lines = OrderItem.query.filter(
            OrderItem.order_id.in_(order_ids)
        ).delete(synchronize_session=False)
    else:
        removed_lines = 0

    removed_orders = Order.query.filter(
        Order.user_id.in_(user_ids)
    ).delete(synchronize_session=False)

    removed_cart = CartItem.query.filter(
        CartItem.user_id.in_(user_ids)
    ).delete(synchronize_session=False)

    removed_reviews = Review.query.filter(
        Review.user_id.in_(user_ids)
    ).delete(synchronize_session=False)

    # Hand any listings back to the shop rather than deleting them, so
    # no order line loses its product.
    Product.query.filter(Product.seller_id.in_(user_ids)).update(
        {"seller_id": None}, synchronize_session=False
    )

    db.session.commit()

    # Clear the test reviews those accounts left on REAL products, so
    # the product ratings return to a clean state.
    for user in users:
        db.session.delete(user)

    db.session.commit()

    print(f"  Removed {len(users)} demo account(s).")
    print(f"    order lines: {removed_lines}")
    print(f"    orders:      {removed_orders}")
    print(f"    cart rows:   {removed_cart}")
    print(f"    reviews:     {removed_reviews}")

    return len(users)


def place_order_for(user, product_names):
    """Create a real, delivered order so the recommender can learn.

    We build the Order and OrderItem rows directly rather than going
    through the HTTP API. That keeps the script independent of a
    running server, and lets us mark the orders Delivered - which an
    order placed through the API could not do without an admin
    advancing it step by step.
    """

    lines = []
    total = 0.0

    for name in product_names:
        product = find_product(name)

        if product is None:
            print(f"    ! skipped '{name}' - not in the catalogue")
            continue

        price = float(product.price)
        lines.append((product, price))
        total += price

    if not lines:
        return None

    order = Order(
        user_id=user.id,
        full_name=user.name,
        phone="98" + str(40000000 + user.id * 137),
        address=f"House {user.id * 7}, Demo Tole",
        city="Kathmandu",
        payment_method="Cash on Delivery",
        total=round(total, 2),
        status="Delivered",
    )

    db.session.add(order)

    # flush() gives the order an id without committing, so the lines
    # below can point at it. Same pattern as the real checkout route.
    db.session.flush()

    for product, price in lines:
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                # Snapshot the name and price, exactly as checkout does.
                product_name=product.name,
                unit_price=price,
                quantity=1,
            )
        )

    return order


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------


def main():
    reset = "--reset" in sys.argv

    with app.app_context():
        print("=" * 62)
        print("SMARTCART DEMO DATA")
        print("=" * 62)

        catalogue = Product.query.count()

        print(f"\nCatalogue: {catalogue} product(s)")

        if catalogue == 0:
            print("\nThere are no products. Import them first:")
            print("  ./venv/Scripts/python.exe import_products.py")
            return

        # -----------------------------------------------------------------
        if reset:
            print("\nRESET - removing demo accounts")
            wipe_demo_data()

        # -----------------------------------------------------------------
        print("\nCREATING ACCOUNTS")

        created_users = []

        for person in DEMO_USERS:
            existing = find_user(person["email"])

            if existing:
                print(f"  {person['name']:<20} already exists - skipped")
                created_users.append((existing, person))
                continue

            user = User(
                name=person["name"],
                email=person["email"],
                role=person["role"],
            )

            user.set_password(DEMO_PASSWORD)

            db.session.add(user)
            db.session.commit()

            print(f"  {person['name']:<20} created ({person['role']})")
            created_users.append((user, person))

        # -----------------------------------------------------------------
        print("\nPLACING ORDERS")

        for user, person in created_users:
            if not person["buys"]:
                print(f"  {person['name']:<20} (no purchases - tests the fallback)")
                continue

            # Skip if they already have orders, so re-running the script
            # does not pile up duplicates.
            already = Order.query.filter_by(user_id=user.id).count()

            if already:
                print(f"  {person['name']:<20} already has {already} order(s) - skipped")
                continue

            order = place_order_for(user, person["buys"])
            db.session.commit()

            if order:
                print(
                    f"  {person['name']:<20} ordered {len(person['buys'])} "
                    f"item(s), Rs. {order.total:,.0f}"
                )

        # -----------------------------------------------------------------
        print("\nWRITING REVIEWS")

        for user, person in created_users:
            for name, rating, comment in person["reviews"]:
                product = find_product(name)

                if product is None:
                    continue

                existing = Review.query.filter_by(
                    user_id=user.id, product_id=product.id
                ).first()

                if existing:
                    print(f"  {person['name']:<20} already reviewed {name}")
                    continue

                db.session.add(
                    Review(
                        user_id=user.id,
                        product_id=product.id,
                        rating=rating,
                        comment=comment,
                    )
                )

                print(f"  {person['name']:<20} rated {name} {rating}/5")

        db.session.commit()

        # -----------------------------------------------------------------
        print("\n" + "=" * 62)
        print("DONE")
        print("=" * 62)

        print(f"\nUsers:    {User.query.count()}")
        print(f"Products: {Product.query.count()}")
        print(f"Orders:   {Order.query.count()}")
        print(f"Reviews:  {Review.query.count()}")

        print("\nLog in with any of these, password 'demo1234':")
        for person in DEMO_USERS:
            print(f"  {person['email']:<28} {person['role']}")

        print("\nWHAT TO TRY IN THE VIVA")
        print("-" * 62)
        print("1. Log in as aarav@demo.smartcart and open /recommendations.")
        print("   You should see an electronics-leaning list, and a row")
        print("   of chips showing what he bought.")
        print("2. Log in as priya@demo.smartcart and open the same page.")
        print("   Her list should lean towards home products instead.")
        print("3. Log out and open it again - you now get 'popularity'")
        print("   instead of a personal list. That is the cold-start")
        print("   fallback, and it is working correctly.")
        print("4. Log in as admin@demo.smartcart for the admin panel -")
        print("   this account has ordered nothing, so its")
        print("   recommendations also fall back to popular.")


if __name__ == "__main__":
    main()
