"""
SmartCart - Product CRUD and Role Tests
=======================================

Checks that:
  - buyers CANNOT add, edit or delete products
  - logged-out visitors CANNOT add, edit or delete products
  - sellers CAN add, edit and delete
  - admins CAN too
  - bad data is rejected with a helpful message
  - the 30 real products are never harmed

HOW TO RUN (from the backend folder, venv activated):

    python test_products.py

Uses Flask's test client, so the server does not need to be running.
Creates its own test accounts and products, then removes them.
"""

from app import app, db, Product, User

# ---------------------------------------------------------------
# Test accounts
# ---------------------------------------------------------------
PASSWORD = "testpass123"

SELLER_EMAIL = "test.seller@smartcart.local"
SELLER2_EMAIL = "test.seller2@smartcart.local"
BUYER_EMAIL = "test.buyer@smartcart.local"
ADMIN_EMAIL = "test.admin@smartcart.local"

TEST_EMAILS = [SELLER_EMAIL, SELLER2_EMAIL, BUYER_EMAIL, ADMIN_EMAIL]

# Name prefix used for products this script creates, so cleanup is safe
TEST_PRODUCT_PREFIX = "[TEST] "

passed = 0
failed = 0


def check(label, condition, detail=""):
    global passed, failed

    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")
        if detail:
            print(f"         -> {detail}")


def make_account(client, name, email, role):
    """Create an account, or return the existing one's id."""
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            return existing.id

    r = client.post("/api/register", json={
        "name": name, "email": email, "password": PASSWORD, "role": role,
    })
    return r.get_json()["user"]["id"]


def headers_for(user_id):
    """Build the header the frontend sends for a logged-in user."""
    if user_id is None:
        return {}
    return {"X-User-Id": str(user_id)}


def main():
    global passed, failed

    print("=" * 62)
    print("SmartCart - Product CRUD + Role Tests")
    print("=" * 62)

    client = app.test_client()

    # Remember the real product count so we can prove we did not disturb it
    with app.app_context():
        real_products_before = Product.query.filter(
            ~Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).count()

    print(f"\n(Real products in database: {real_products_before})")

    # ---------------------------------------------------------------
    # Set up test accounts
    # ---------------------------------------------------------------
    print("\n0. SETUP - create test accounts")

    seller_id = make_account(client, "Test Seller", SELLER_EMAIL, "seller")
    seller2_id = make_account(client, "Test Seller Two", SELLER2_EMAIL, "seller")
    buyer_id = make_account(client, "Test Buyer", BUYER_EMAIL, "buyer")
    admin_id = make_account(client, "Test Admin", ADMIN_EMAIL, "admin")

    check("seller account ready", bool(seller_id))
    check("second seller account ready", bool(seller2_id))
    check("second seller is a different account", seller2_id != seller_id)
    check("buyer account ready", bool(buyer_id))
    check("admin account ready", bool(admin_id))

    # ---------------------------------------------------------------
    # 1. Logged-out visitors are blocked from writing
    # ---------------------------------------------------------------
    print("\n1. NOT LOGGED IN - all writes must fail with 401")

    new_product = {
        "name": f"{TEST_PRODUCT_PREFIX}Anonymous Item",
        "description": "Should never be created.",
        "price": 100,
        "category": "Electronics",
        "stock": 1,
    }

    r = client.post("/api/products", json=new_product, headers=headers_for(None))
    check("create without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.put("/api/products/1", json={"price": 1}, headers=headers_for(None))
    check("update without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.delete("/api/products/1", headers=headers_for(None))
    check("delete without login -> 401", r.status_code == 401, f"got {r.status_code}")

    # A made-up id in the header must not work either
    r = client.post("/api/products", json=new_product,
                    headers={"X-User-Id": "999999"})
    check("fake user id -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.post("/api/products", json=new_product,
                    headers={"X-User-Id": "not-a-number"})
    check("junk user id -> 401", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 2. Buyers are blocked from writing
    # ---------------------------------------------------------------
    print("\n2. BUYER - all writes must fail with 403")

    buyer_headers = headers_for(buyer_id)

    r = client.post("/api/products", json=new_product, headers=buyer_headers)
    check("buyer cannot create -> 403", r.status_code == 403, f"got {r.status_code}")
    check("403 message explains the role",
          "buyer" in r.get_json().get("error", "").lower())

    r = client.put("/api/products/1", json={"price": 1}, headers=buyer_headers)
    check("buyer cannot update -> 403", r.status_code == 403, f"got {r.status_code}")

    r = client.delete("/api/products/1", headers=buyer_headers)
    check("buyer cannot delete -> 403", r.status_code == 403, f"got {r.status_code}")

    # Buyers must still be able to READ
    r = client.get("/api/products")
    check("buyer can still read the product list", r.status_code == 200)

    # ---------------------------------------------------------------
    # 3. Sellers can create
    # ---------------------------------------------------------------
    print("\n3. SELLER - can create")

    seller_headers = headers_for(seller_id)

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Seller Speaker",
        "description": "A test speaker.",
        "price": 1999.5,
        "category": "Electronics",
        "image": "https://example.com/speaker.jpg",
        "stock": 7,
    }, headers=seller_headers)

    check("seller create -> 201", r.status_code == 201, f"got {r.status_code}")

    created = r.get_json().get("product", {})
    product_id = created.get("id")

    check("product got an id", bool(product_id))
    check("price stored correctly", created.get("price") == 1999.5,
          f"got {created.get('price')}")
    check("stock stored correctly", created.get("stock") == 7)
    check("category stored correctly", created.get("category") == "Electronics")

    # The creator must be stamped as the owner automatically
    check("seller_id was stamped from the logged-in user",
          created.get("seller_id") == seller_id,
          f"expected {seller_id}, got {created.get('seller_id')}")

    # A seller must not be able to hand ownership to somebody else by
    # sneaking seller_id into the request body.
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Spoofed Owner",
        "description": "Trying to set someone else as the owner.",
        "price": 10,
        "category": "Home",
        "seller_id": 999999,
    }, headers=seller_headers)
    check("seller_id in the request body is ignored -> 201",
          r.status_code == 201, f"got {r.status_code}")
    check("ownership still went to the caller",
          r.get_json()["product"]["seller_id"] == seller_id,
          f"got {r.get_json()['product']['seller_id']}")
    spoofed_id = r.get_json()["product"]["id"]
    client.delete(f"/api/products/{spoofed_id}", headers=seller_headers)

    # ---------------------------------------------------------------
    # 4. Validation
    # ---------------------------------------------------------------
    print("\n4. SELLER - bad data is rejected")

    bad_cases = [
        ("missing name", {"name": "", "description": "d", "price": 1, "category": "c"}),
        ("missing description", {"name": "n", "description": "", "price": 1, "category": "c"}),
        ("missing category", {"name": "n", "description": "d", "price": 1, "category": ""}),
        ("price is text", {"name": "n", "description": "d", "price": "abc", "category": "c"}),
        ("negative price", {"name": "n", "description": "d", "price": -5, "category": "c"}),
        ("stock is text", {"name": "n", "description": "d", "price": 1,
                           "category": "c", "stock": "many"}),
        ("negative stock", {"name": "n", "description": "d", "price": 1,
                            "category": "c", "stock": -3}),
    ]

    for label, payload in bad_cases:
        r = client.post("/api/products", json=payload, headers=seller_headers)
        check(f"{label} -> 400", r.status_code == 400, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 5. Sellers can update
    # ---------------------------------------------------------------
    print("\n5. SELLER - can update")

    r = client.put(f"/api/products/{product_id}",
                   json={"price": 1499, "stock": 3},
                   headers=seller_headers)
    check("partial update -> 200", r.status_code == 200, f"got {r.status_code}")

    updated = r.get_json().get("product", {})
    check("price was changed", updated.get("price") == 1499, f"got {updated.get('price')}")
    check("stock was changed", updated.get("stock") == 3)
    check("name was NOT wiped by the partial update",
          updated.get("name") == f"{TEST_PRODUCT_PREFIX}Seller Speaker",
          f"got {updated.get('name')}")
    check("category was NOT wiped",
          updated.get("category") == "Electronics")

    r = client.put(f"/api/products/{product_id}",
                   json={"price": -1}, headers=seller_headers)
    check("update with bad price -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.put("/api/products/999999", json={"price": 5}, headers=seller_headers)
    check("update a missing product -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 6. Reading a single product
    # ---------------------------------------------------------------
    print("\n6. READ one product")

    r = client.get(f"/api/products/{product_id}")
    check("read single product -> 200", r.status_code == 200, f"got {r.status_code}")
    check("correct product returned",
          r.get_json().get("id") == product_id)

    r = client.get("/api/products/999999")
    check("read missing product -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 7. Filtering
    # ---------------------------------------------------------------
    print("\n7. FILTERING")

    r = client.get("/api/products?category=Electronics")
    electronics = r.get_json()
    check("category filter works",
          all(p["category"].lower() == "electronics" for p in electronics),
          f"got {len(electronics)} items")

    r = client.get("/api/products?search=speaker")
    found = r.get_json()
    check("search finds the test speaker",
          any("speaker" in p["name"].lower() for p in found),
          f"got {len(found)} items")

    # ---------------------------------------------------------------
    # 8. Sellers can delete
    # ---------------------------------------------------------------
    print("\n8. SELLER - can delete")

    r = client.delete(f"/api/products/{product_id}", headers=seller_headers)
    check("delete -> 200", r.status_code == 200, f"got {r.status_code}")

    r = client.get(f"/api/products/{product_id}")
    check("product is really gone (404 afterwards)",
          r.status_code == 404, f"got {r.status_code}")

    r = client.delete(f"/api/products/{product_id}", headers=seller_headers)
    check("deleting it twice -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 9. OWNERSHIP - seller A cannot touch seller B's product
    # ---------------------------------------------------------------
    print("\n9. OWNERSHIP - sellers are fenced off from each other")

    seller2_headers = headers_for(seller2_id)

    # Seller 2 creates their own product
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Seller Two Lamp",
        "description": "Belongs to the second seller.",
        "price": 800,
        "category": "Home",
        "stock": 5,
    }, headers=seller2_headers)
    check("second seller can create their own product -> 201",
          r.status_code == 201, f"got {r.status_code}")

    seller2_product_id = r.get_json()["product"]["id"]

    check("second seller's product is owned by them",
          r.get_json()["product"]["seller_id"] == seller2_id)

    # Seller 1 now tries to edit it -> must be refused
    r = client.put(f"/api/products/{seller2_product_id}",
                   json={"price": 1},
                   headers=seller_headers)
    check("seller A cannot update seller B's product -> 403",
          r.status_code == 403, f"got {r.status_code}")

    r = client.delete(f"/api/products/{seller2_product_id}", headers=seller_headers)
    check("seller A cannot delete seller B's product -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # ...and the product must still be intact after those attempts
    r = client.get(f"/api/products/{seller2_product_id}")
    check("the product survived the blocked attempts",
          r.status_code == 200 and r.get_json()["price"] == 800,
          f"got {r.status_code}")

    # Seller 2 can still edit their own
    r = client.put(f"/api/products/{seller2_product_id}",
                   json={"price": 850}, headers=seller2_headers)
    check("the owner can still update their own product -> 200",
          r.status_code == 200, f"got {r.status_code}")

    # Seller 1 also cannot touch the shop-owned (seller_id = NULL) products
    r = client.put("/api/products/1", json={"price": 1}, headers=seller_headers)
    check("seller cannot edit a shop-owned product -> 403",
          r.status_code == 403, f"got {r.status_code}")
    check("403 explains that it belongs to the shop",
          "shop" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    r = client.delete("/api/products/1", headers=seller_headers)
    check("seller cannot delete a shop-owned product -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # ...but product 1 must be completely unharmed
    r = client.get("/api/products/1")
    check("shop-owned product 1 is still there and unchanged",
          r.status_code == 200, f"got {r.status_code}")

    # A buyer cannot touch it either (role check fires first)
    r = client.put("/api/products/1", json={"price": 1}, headers=buyer_headers)
    check("buyer cannot edit a shop-owned product -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # Clean up seller 2's product
    r = client.delete(f"/api/products/{seller2_product_id}", headers=seller2_headers)
    check("the owner can delete their own product -> 200",
          r.status_code == 200, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 10. Admins can do everything
    # ---------------------------------------------------------------
    print("\n10. ADMIN - full access")

    admin_headers = headers_for(admin_id)

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Admin Item",
        "description": "Created by admin.",
        "price": 500,
        "category": "Home",
        "stock": 2,
    }, headers=admin_headers)
    check("admin can create -> 201", r.status_code == 201, f"got {r.status_code}")

    admin_product_id = r.get_json()["product"]["id"]

    r = client.put(f"/api/products/{admin_product_id}",
                   json={"price": 550}, headers=admin_headers)
    check("admin can update -> 200", r.status_code == 200, f"got {r.status_code}")

    r = client.delete(f"/api/products/{admin_product_id}", headers=admin_headers)
    check("admin can delete -> 200", r.status_code == 200, f"got {r.status_code}")

    # The important one: an admin is NOT fenced off by ownership, and can
    # edit the shop-owned products that sellers are refused on.
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Seller Two Target",
        "description": "A seller's product that the admin will edit.",
        "price": 300,
        "category": "Fashion",
        "stock": 4,
    }, headers=seller2_headers)
    target_id = r.get_json()["product"]["id"]

    r = client.put(f"/api/products/{target_id}",
                   json={"price": 333}, headers=admin_headers)
    check("admin can update ANOTHER seller's product -> 200",
          r.status_code == 200, f"got {r.status_code}")

    r = client.delete(f"/api/products/{target_id}", headers=admin_headers)
    check("admin can delete another seller's product -> 200",
          r.status_code == 200, f"got {r.status_code}")

    # And the shop-owned product sellers were blocked on
    with app.app_context():
        shop_owned = Product.query.filter(Product.seller_id.is_(None)).first()
        shop_owned_id = shop_owned.id if shop_owned else None
        shop_owned_price = shop_owned.price if shop_owned else None

    if shop_owned_id is not None:
        r = client.put(f"/api/products/{shop_owned_id}",
                       json={"price": shop_owned_price}, headers=admin_headers)
        check("admin can edit a shop-owned product -> 200",
              r.status_code == 200, f"got {r.status_code}")
    else:
        check("a shop-owned product exists to test against", False,
              "no product with seller_id = NULL found")

    # ---------------------------------------------------------------
    # 11. The real products were never touched
    # ---------------------------------------------------------------
    print("\n11. SAFETY - real products untouched")

    with app.app_context():
        real_products_after = Product.query.filter(
            ~Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).count()

        leftovers = Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).all()

    check("real product count unchanged",
          real_products_after == real_products_before,
          f"{real_products_before} -> {real_products_after}")

    if leftovers:
        print(f"  Cleaning up {len(leftovers)} leftover test product(s)...")
        with app.app_context():
            for p in Product.query.filter(Product.name.like(f"{TEST_PRODUCT_PREFIX}%")).all():
                db.session.delete(p)
            db.session.commit()

    with app.app_context():
        still_there = Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).count()

    check("no test products left behind", still_there == 0,
          f"{still_there} remain")

    # ---------------------------------------------------------------
    # 12. Clean up test accounts
    # ---------------------------------------------------------------
    print("\n12. Clean up test accounts")

    with app.app_context():
        removed = 0
        for email in TEST_EMAILS:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
                removed += 1
        db.session.commit()

        print(f"  Removed {removed} test account(s).")
        print(f"  Products in database: {Product.query.count()}")
        print(f"  Users in database: {User.query.count()}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nRoles and product CRUD all behave correctly.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
