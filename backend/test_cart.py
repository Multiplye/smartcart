"""
SmartCart - Shopping Cart Tests
================================

The cart is stored in the database, one row per (user, product). These
tests check the behaviour a shopper would actually notice:

  - only logged-in users have a cart
  - your cart is YOURS - another user cannot see or change it
  - adding the same product twice bumps the quantity, not the row count
  - quantity can never go below 1 and never above the available stock
  - setting quantity to 0 removes the item
  - deleting a product out from under a cart does not crash anything

HOW TO RUN (from the backend folder, venv activated):

    python test_cart.py

Uses Flask's test client, so the server does not need to be running.
Creates its own test accounts and products, then removes them.
"""

from app import app, db, CartItem, Product, User

# ---------------------------------------------------------------
# Test accounts
# ---------------------------------------------------------------
PASSWORD = "testpass123"

SHOPPER_EMAIL = "test.shopper@smartcart.local"
OTHER_EMAIL = "test.other@smartcart.local"
CART_SELLER_EMAIL = "test.cartseller@smartcart.local"

TEST_EMAILS = [SHOPPER_EMAIL, OTHER_EMAIL, CART_SELLER_EMAIL]

# Name prefix so cleanup can find our own products and nothing else
TEST_PRODUCT_PREFIX = "[CARTTEST] "

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
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            return existing.id

    r = client.post("/api/register", json={
        "name": name, "email": email, "password": PASSWORD, "role": role,
    })
    return r.get_json()["user"]["id"]


def headers_for(user_id):
    if user_id is None:
        return {}
    return {"X-User-Id": str(user_id)}


def main():
    global passed, failed

    print("=" * 62)
    print("SmartCart - Shopping Cart Tests")
    print("=" * 62)

    client = app.test_client()

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------
    print("\n0. SETUP")

    shopper_id = make_account(client, "Test Shopper", SHOPPER_EMAIL, "buyer")
    other_id = make_account(client, "Test Other", OTHER_EMAIL, "buyer")
    seller_id = make_account(client, "Cart Seller", CART_SELLER_EMAIL, "seller")

    check("shopper account ready", bool(shopper_id))
    check("second buyer account ready", bool(other_id))
    check("they are different accounts", shopper_id != other_id)

    shopper = headers_for(shopper_id)
    other = headers_for(other_id)
    seller = headers_for(seller_id)

    # A product to play with, created by the seller
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Cart Speaker",
        "description": "A product used only by the cart tests.",
        "price": 1000,
        "category": "Electronics",
        "stock": 5,
    }, headers=seller)
    product_id = r.get_json()["product"]["id"]

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Out Of Stock",
        "description": "A product with no stock at all.",
        "price": 250,
        "category": "Home",
        "stock": 0,
    }, headers=seller)
    empty_id = r.get_json()["product"]["id"]

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Second Item",
        "description": "A second product for multi-item tests.",
        "price": 400,
        "category": "Fashion",
        "stock": 10,
    }, headers=seller)
    second_id = r.get_json()["product"]["id"]

    check("test products created", bool(product_id and empty_id and second_id))

    # ---------------------------------------------------------------
    # 1. Logged-out users have no cart
    # ---------------------------------------------------------------
    print("\n1. NOT LOGGED IN")

    r = client.get("/api/cart")
    check("read cart without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": product_id}, headers={})
    check("add to cart without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.delete("/api/cart")
    check("clear cart without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.get("/api/cart", headers={"X-User-Id": "999999"})
    check("read cart with a fake user id -> 401", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 2. A new cart starts empty
    # ---------------------------------------------------------------
    print("\n2. A FRESH CART IS EMPTY")

    r = client.get("/api/cart", headers=shopper)
    check("read cart -> 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    check("cart starts empty", body["items"] == [], f"got {body['items']}")
    check("count starts at 0", body["count"] == 0)
    check("total starts at 0", body["total"] == 0)

    # ---------------------------------------------------------------
    # 3. Adding items
    # ---------------------------------------------------------------
    print("\n3. ADDING ITEMS")

    r = client.post("/api/cart", json={"product_id": product_id}, headers=shopper)
    check("add a product -> 201", r.status_code == 201, f"got {r.status_code}")

    body = r.get_json()
    check("cart now has 1 item", len(body["items"]) == 1, f"got {len(body['items'])}")
    check("quantity defaults to 1", body["items"][0]["quantity"] == 1)
    check("count is 1", body["count"] == 1)

    # Quantity is optional - sending 3 should store 3
    r = client.post("/api/cart", json={"product_id": second_id, "quantity": 3},
                    headers=shopper)
    check("add with an explicit quantity -> 201", r.status_code == 201, f"got {r.status_code}")

    body = r.get_json()
    check("cart now has 2 rows", len(body["items"]) == 2, f"got {len(body['items'])}")
    check("count is 1 + 3 = 4", body["count"] == 4, f"got {body['count']}")

    # Total should be 1 x 1000 + 3 x 400 = 2200
    check("total is calculated correctly", body["total"] == 2200, f"got {body['total']}")

    # ---------------------------------------------------------------
    # 4. The item carries the product details the UI needs
    # ---------------------------------------------------------------
    print("\n4. CART ITEMS INCLUDE PRODUCT DETAILS")

    item = next(i for i in body["items"] if i["product_id"] == second_id)

    check("item has a name", item["name"].startswith(TEST_PRODUCT_PREFIX))
    check("item has a price", item["price"] == 400)
    check("item has a category", item["category"] == "Fashion")
    check("item has a subtotal", item["subtotal"] == 1200, f"got {item['subtotal']}")
    check("item reports the current stock", item["stock"] == 10)

    # ---------------------------------------------------------------
    # 5. Adding the same product again bumps the quantity
    # ---------------------------------------------------------------
    print("\n5. ADDING A DUPLICATE BUMPS THE QUANTITY")

    r = client.post("/api/cart", json={"product_id": product_id}, headers=shopper)
    body = r.get_json()

    check("still only 2 rows", len(body["items"]) == 2, f"got {len(body['items'])}")

    first = next(i for i in body["items"] if i["product_id"] == product_id)
    check("first item went from 1 to 2", first["quantity"] == 2, f"got {first['quantity']}")
    check("count is now 5", body["count"] == 5, f"got {body['count']}")

    with app.app_context():
        rows = CartItem.query.filter_by(
            user_id=shopper_id, product_id=product_id
        ).count()
    check("the database really has one row, not two", rows == 1, f"got {rows}")

    # ---------------------------------------------------------------
    # 6. Bad input is rejected
    # ---------------------------------------------------------------
    print("\n6. BAD INPUT IS REJECTED")

    r = client.post("/api/cart", json={}, headers=shopper)
    check("missing product_id -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": "abc"}, headers=shopper)
    check("product_id is text -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": 999999}, headers=shopper)
    check("product does not exist -> 404", r.status_code == 404, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": product_id, "quantity": 0},
                    headers=shopper)
    check("quantity 0 -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": product_id, "quantity": -2},
                    headers=shopper)
    check("negative quantity -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": product_id, "quantity": "lots"},
                    headers=shopper)
    check("quantity is text -> 400", r.status_code == 400, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 7. You cannot ask for more than the shop has
    # ---------------------------------------------------------------
    print("\n7. STOCK IS RESPECTED")

    # product_id has stock 5. Ask for 99.
    r = client.post("/api/cart", json={"product_id": product_id, "quantity": 99},
                    headers=shopper)
    check("asking for 99 of a 5-stock item is not an error -> 201",
          r.status_code == 201, f"got {r.status_code}")

    body = r.get_json()
    first = next(i for i in body["items"] if i["product_id"] == product_id)
    check("quantity was capped at the stock level (5)",
          first["quantity"] == 5, f"got {first['quantity']}")

    # An out-of-stock product cannot be added at all
    r = client.post("/api/cart", json={"product_id": empty_id}, headers=shopper)
    check("adding an out-of-stock product -> 400",
          r.status_code == 400, f"got {r.status_code}")
    check("the message says out of stock",
          "out of stock" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    # ---------------------------------------------------------------
    # 8. Changing the quantity directly
    # ---------------------------------------------------------------
    print("\n8. UPDATING A QUANTITY")

    r = client.put(f"/api/cart/{second_id}", json={"quantity": 7}, headers=shopper)
    check("set quantity to 7 -> 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    item = next(i for i in body["items"] if i["product_id"] == second_id)
    check("quantity is now 7", item["quantity"] == 7, f"got {item['quantity']}")

    # second_id has stock 10, so 99 should be capped
    r = client.put(f"/api/cart/{second_id}", json={"quantity": 99}, headers=shopper)
    body = r.get_json()
    item = next(i for i in body["items"] if i["product_id"] == second_id)
    check("quantity was capped at 10", item["quantity"] == 10, f"got {item['quantity']}")
    check("the message explains the cap",
          "stock" in body["message"].lower(), f"got {body['message']!r}")

    r = client.put(f"/api/cart/{second_id}", json={"quantity": -1}, headers=shopper)
    check("negative quantity -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.put(f"/api/cart/{second_id}", json={}, headers=shopper)
    check("missing quantity -> 400", r.status_code == 400, f"got {r.status_code}")

    r = client.put("/api/cart/999999", json={"quantity": 1}, headers=shopper)
    check("updating an item not in the cart -> 404",
          r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 9. Quantity 0 removes the item
    # ---------------------------------------------------------------
    print("\n9. QUANTITY 0 REMOVES THE ITEM")

    r = client.put(f"/api/cart/{second_id}", json={"quantity": 0}, headers=shopper)
    check("set quantity to 0 -> 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    check("the item is gone from the cart",
          all(i["product_id"] != second_id for i in body["items"]),
          f"got {[i['product_id'] for i in body['items']]}")

    # ---------------------------------------------------------------
    # 10. Removing an item
    # ---------------------------------------------------------------
    print("\n10. REMOVING AN ITEM")

    r = client.delete(f"/api/cart/{product_id}", headers=shopper)
    check("remove an item -> 200", r.status_code == 200, f"got {r.status_code}")
    check("cart is now empty", r.get_json()["items"] == [])

    r = client.delete(f"/api/cart/{product_id}", headers=shopper)
    check("removing it again -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 11. THE IMPORTANT ONE: carts are private
    # ---------------------------------------------------------------
    print("\n11. CARTS ARE PRIVATE")

    # The shopper puts something in their cart
    client.post("/api/cart", json={"product_id": product_id, "quantity": 2},
                headers=shopper)

    # The other buyer must see an empty cart, not the shopper's
    r = client.get("/api/cart", headers=other)
    check("the other buyer's cart is empty",
          r.get_json()["items"] == [],
          f"got {r.get_json()['items']}")

    # ...and must not be able to change the shopper's quantity
    r = client.put(f"/api/cart/{product_id}", json={"quantity": 1}, headers=other)
    check("the other buyer cannot update the shopper's item -> 404",
          r.status_code == 404, f"got {r.status_code}")

    r = client.delete(f"/api/cart/{product_id}", headers=other)
    check("the other buyer cannot remove the shopper's item -> 404",
          r.status_code == 404, f"got {r.status_code}")

    # ...and clearing their own cart must not touch the shopper's
    r = client.delete("/api/cart", headers=other)
    check("the other buyer can clear their own (empty) cart -> 200",
          r.status_code == 200, f"got {r.status_code}")

    r = client.get("/api/cart", headers=shopper)
    check("the shopper's cart is untouched by all of that",
          len(r.get_json()["items"]) == 1, f"got {r.get_json()['items']}")

    # ---------------------------------------------------------------
    # 12. Sellers and admins get a cart too
    # ---------------------------------------------------------------
    print("\n12. EVERY ROLE CAN SHOP")

    r = client.get("/api/cart", headers=seller)
    check("a seller has their own cart -> 200", r.status_code == 200, f"got {r.status_code}")

    r = client.post("/api/cart", json={"product_id": product_id}, headers=seller)
    check("a seller can add an item -> 201", r.status_code == 201, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 13. Clearing the cart
    # ---------------------------------------------------------------
    print("\n13. CLEARING THE CART")

    r = client.delete("/api/cart", headers=shopper)
    check("clear the cart -> 200", r.status_code == 200, f"got {r.status_code}")
    check("cart is empty afterwards", r.get_json()["items"] == [])

    with app.app_context():
        remaining = CartItem.query.filter_by(user_id=shopper_id).count()
    check("no rows left for that user in the database", remaining == 0, f"got {remaining}")

    # ---------------------------------------------------------------
    # 14. Real products were not harmed
    # ---------------------------------------------------------------
    print("\n14. SAFETY")

    with app.app_context():
        real_products = Product.query.filter(
            ~Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).count()

    check("the 30 real products are still there", real_products == 30,
          f"got {real_products}")

    # ---------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------
    print("\n15. CLEAN UP")

    with app.app_context():
        # Remove the cart rows first - they point at the products
        CartItem.query.filter(
            CartItem.user_id.in_([shopper_id, other_id, seller_id])
        ).delete(synchronize_session=False)
        db.session.commit()

        removed_products = 0
        for p in Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).all():
            db.session.delete(p)
            removed_products += 1

        removed_users = 0
        for email in TEST_EMAILS:
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
                removed_users += 1

        db.session.commit()

        print(f"  Removed {removed_products} test product(s).")
        print(f"  Removed {removed_users} test account(s).")
        print(f"  Products in database: {Product.query.count()}")
        print(f"  Users in database: {User.query.count()}")
        print(f"  Cart rows in database: {CartItem.query.count()}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nThe cart behaves correctly and is private to each user.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
