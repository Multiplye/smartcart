"""
SmartCart - Order Tests
========================

Checks the whole checkout flow and the rules around who can see what.

THE FLOW BEING TESTED
    cart -> place order -> stock falls -> cart empties -> order history

THE RULES BEING TESTED
    - you must be logged in to order
    - you cannot order an empty cart
    - delivery details are required
    - if any item is out of stock the WHOLE order is refused
    - placing an order REDUCES STOCK and EMPTIES THE CART
    - the order records the price paid, so later edits do not change it
    - a buyer sees only their own orders
    - a seller sees only orders containing their products
    - cancelling an order puts the stock BACK
    - the status flow cannot be skipped (Pending -> Delivered is refused)

HOW TO RUN (from the backend folder, venv activated):

    python test_orders.py
"""

from app import app, db, CartItem, Order, OrderItem, Product, User

PASSWORD = "testpass123"

BUYER_EMAIL = "test.orderbuyer@smartcart.local"
OTHER_BUYER_EMAIL = "test.orderbuyer2@smartcart.local"
SELLER_EMAIL = "test.orderseller@smartcart.local"
SELLER2_EMAIL = "test.orderseller2@smartcart.local"
ADMIN_EMAIL = "test.orderadmin@smartcart.local"

TEST_EMAILS = [
    BUYER_EMAIL, OTHER_BUYER_EMAIL,
    SELLER_EMAIL, SELLER2_EMAIL, ADMIN_EMAIL,
]

TEST_PRODUCT_PREFIX = "[ORDERTEST] "

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


DELIVERY = {
    "full_name": "Test Buyer",
    "phone": "9800000000",
    "address": "12 Test Street",
    "city": "Kathmandu",
}


def main():
    global passed, failed

    print("=" * 62)
    print("SmartCart - Order Tests")
    print("=" * 62)

    client = app.test_client()

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------
    print("\n0. SETUP")

    buyer_id = make_account(client, "Order Buyer", BUYER_EMAIL, "buyer")
    other_id = make_account(client, "Other Buyer", OTHER_BUYER_EMAIL, "buyer")
    seller_id = make_account(client, "Order Seller", SELLER_EMAIL, "seller")
    seller2_id = make_account(client, "Order Seller Two", SELLER2_EMAIL, "seller")
    admin_id = make_account(client, "Order Admin", ADMIN_EMAIL, "admin")

    buyer = headers_for(buyer_id)
    other = headers_for(other_id)
    seller = headers_for(seller_id)
    seller2 = headers_for(seller2_id)
    admin = headers_for(admin_id)

    check("buyer accounts ready", bool(buyer_id and other_id))
    check("seller accounts ready", bool(seller_id and seller2_id))
    check("admin account ready", bool(admin_id))

    # A product with known stock and price
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Order Widget",
        "description": "Used by the order tests.",
        "price": 500,
        "category": "Electronics",
        "stock": 10,
    }, headers=seller)
    widget_id = r.get_json()["product"]["id"]
    check("widget product created with stock 10", bool(widget_id))

    # A second seller's product, to prove sellers are fenced off
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Other Seller Item",
        "description": "Belongs to the second seller.",
        "price": 200,
        "category": "Home",
        "stock": 5,
    }, headers=seller2)
    other_product_id = r.get_json()["product"]["id"]

    # ---------------------------------------------------------------
    # 1. Only logged-in users can order
    # ---------------------------------------------------------------
    print("\n1. NOT LOGGED IN")

    r = client.post("/api/orders", json=DELIVERY)
    check("order without login -> 401", r.status_code == 401, f"got {r.status_code}")

    r = client.get("/api/orders")
    check("list orders without login -> 401", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 2. An empty cart cannot be ordered
    # ---------------------------------------------------------------
    print("\n2. EMPTY CART")

    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    check("ordering an empty cart -> 400", r.status_code == 400, f"got {r.status_code}")
    check("the message mentions the empty cart",
          "empty" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    # ---------------------------------------------------------------
    # 3. Delivery details are required
    # ---------------------------------------------------------------
    print("\n3. DELIVERY DETAILS ARE REQUIRED")

    client.post("/api/cart", json={"product_id": widget_id, "quantity": 2},
                headers=buyer)

    for field in ["full_name", "phone", "address", "city"]:
        payload = dict(DELIVERY)
        payload[field] = ""

        r = client.post("/api/orders", json=payload, headers=buyer)
        check(f"missing {field} -> 400", r.status_code == 400, f"got {r.status_code}")

    # Whitespace-only should count as missing too
    payload = dict(DELIVERY)
    payload["city"] = "   "

    r = client.post("/api/orders", json=payload, headers=buyer)
    check("whitespace-only city -> 400", r.status_code == 400, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 4. Placing a real order
    # ---------------------------------------------------------------
    print("\n4. PLACING AN ORDER")

    # Stock before
    r = client.get(f"/api/products/{widget_id}")
    stock_before = r.get_json()["stock"]
    check("stock is 10 before ordering", stock_before == 10, f"got {stock_before}")

    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    check("order placed -> 201", r.status_code == 201, f"got {r.status_code}")

    body = r.get_json()
    order = body["order"]
    order_id = order["id"]

    check("order got an id", bool(order_id))
    check("status starts as Pending", order["status"] == "Pending", f"got {order['status']}")
    check("payment method is cash on delivery",
          order["payment_method"] == "Cash on Delivery",
          f"got {order['payment_method']}")
    check("total is 2 x 500 = 1000", order["total"] == 1000, f"got {order['total']}")
    check("delivery name recorded", order["full_name"] == "Test Buyer")
    check("delivery city recorded", order["city"] == "Kathmandu")
    check("order has 1 line item", len(order["items"]) == 1, f"got {len(order['items'])}")
    check("the line records the product name",
          order["items"][0]["product_name"].startswith(TEST_PRODUCT_PREFIX))
    check("the line records the price paid",
          order["items"][0]["unit_price"] == 500, f"got {order['items'][0]['unit_price']}")
    check("the line subtotal is right", order["items"][0]["subtotal"] == 1000)

    # ---------------------------------------------------------------
    # 5. The order reduced stock and emptied the cart
    # ---------------------------------------------------------------
    print("\n5. SIDE EFFECTS - stock falls, cart empties")

    r = client.get(f"/api/products/{widget_id}")
    check("stock fell from 10 to 8", r.get_json()["stock"] == 8,
          f"got {r.get_json()['stock']}")

    r = client.get("/api/cart", headers=buyer)
    check("the cart is now empty", r.get_json()["items"] == [],
          f"got {r.get_json()['items']}")

    # ---------------------------------------------------------------
    # 6. Out of stock blocks the whole order
    # ---------------------------------------------------------------
    print("\n6. OUT OF STOCK BLOCKS THE ORDER")

    # A product with only 2 in stock
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Nearly Gone",
        "description": "Only two left.",
        "price": 100,
        "category": "Fashion",
        "stock": 2,
    }, headers=seller)
    scarce_id = r.get_json()["product"]["id"]

    # Cart has 5 of something with stock 2, plus 1 of the widget.
    #
    # Note: the CART route already caps quantities at stock, so we cannot
    # build this situation through the API. We write the row directly,
    # which is realistic - stock can fall AFTER an item is in the cart
    # (another shopper buys the last ones).
    client.post("/api/cart", json={"product_id": widget_id, "quantity": 1},
                headers=buyer)

    with app.app_context():
        item = CartItem.query.filter_by(
            user_id=buyer_id, product_id=scarce_id
        ).first()

        if item is None:
            item = CartItem(user_id=buyer_id, product_id=scarce_id, quantity=5)
            db.session.add(item)
        else:
            item.quantity = 5

        db.session.commit()

    r = client.get("/api/cart", headers=buyer)
    check("the cart now asks for 5 of a product with only 2 in stock",
          any(i["product_id"] == scarce_id and i["quantity"] == 5
              for i in r.get_json()["items"]),
          f"got {[(i['product_id'], i['quantity']) for i in r.get_json()['items']]}")

    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    check("order with an over-quantity item -> 400",
          r.status_code == 400, f"got {r.status_code}")

    error_text = r.get_json().get("error", "")
    check("the message names the problem product",
          "Nearly Gone" in error_text, f"got {error_text!r}")

    # Nothing at all should have changed
    r = client.get(f"/api/products/{widget_id}")
    check("the widget's stock was NOT reduced",
          r.get_json()["stock"] == 8, f"got {r.get_json()['stock']}")

    r = client.get("/api/products")
    with app.app_context():
        total_orders = Order.query.filter_by(user_id=buyer_id).count()

    check("no new order was created", total_orders == 1, f"got {total_orders}")

    r = client.get("/api/cart", headers=buyer)
    check("the cart was NOT emptied", len(r.get_json()["items"]) == 2,
          f"got {len(r.get_json()['items'])}")

    # ---------------------------------------------------------------
    # 7. A truly out-of-stock product
    # ---------------------------------------------------------------
    print("\n7. A PRODUCT WITH ZERO STOCK")

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}All Gone",
        "description": "No stock at all.",
        "price": 50,
        "category": "Home",
        "stock": 0,
    }, headers=seller)
    gone_id = r.get_json()["product"]["id"]

    # It cannot even be added to the cart
    r = client.post("/api/cart", json={"product_id": gone_id}, headers=buyer)
    check("a zero-stock product cannot be added to the cart -> 400",
          r.status_code == 400, f"got {r.status_code}")

    # But if stock drops to zero AFTER it is in the cart, ordering is refused.
    # The cart currently holds 5 x scarce_id (stock 2) from section 6.
    # Drop the stock to 0 behind the shopper's back, then remove the widget
    # so the scarce item is the ONLY problem reported.
    with app.app_context():
        p = db.session.get(Product, scarce_id)
        p.stock = 0
        db.session.commit()

    client.delete(f"/api/cart/{widget_id}", headers=buyer)

    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    check("an item that sold out while in the cart blocks the order -> 400",
          r.status_code == 400, f"got {r.status_code}")
    check("the message says out of stock",
          "out of stock" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    # Clear the cart for the next test
    client.delete("/api/cart", headers=buyer)
    check("cart cleared for the next section",
          client.get("/api/cart", headers=buyer).get_json()["items"] == [])

    # ---------------------------------------------------------------
    # 8. The order records the price paid
    # ---------------------------------------------------------------
    print("\n8. THE ORDER REMEMBERS THE PRICE PAID")

    # Seller raises the widget price from 500 to 900
    r = client.put(f"/api/products/{widget_id}", json={"price": 900},
                   headers=seller)
    check("seller raised the price to 900", r.status_code == 200)

    r = client.get(f"/api/orders/{order_id}", headers=buyer)
    check("the old order still shows 500 as the price paid",
          r.get_json()["items"][0]["unit_price"] == 500,
          f"got {r.get_json()['items'][0]['unit_price']}")
    check("the old order total is still 1000",
          r.get_json()["total"] == 1000, f"got {r.get_json()['total']}")

    # Put it back for later tests
    client.put(f"/api/products/{widget_id}", json={"price": 500}, headers=seller)

    # ---------------------------------------------------------------
    # 9. A deleted product does not break the order
    # ---------------------------------------------------------------
    print("\n9. A DELETED PRODUCT DOES NOT BREAK THE ORDER")

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Doomed Item",
        "description": "Will be deleted after being ordered.",
        "price": 300,
        "category": "Electronics",
        "stock": 3,
    }, headers=seller)
    doomed_id = r.get_json()["product"]["id"]

    client.post("/api/cart", json={"product_id": doomed_id}, headers=buyer)
    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    doomed_order_id = r.get_json()["order"]["id"]
    check("order placed for the doomed item -> 201",
          r.status_code == 201, f"got {r.status_code}")

    # Now the seller deletes the product entirely
    r = client.delete(f"/api/products/{doomed_id}", headers=seller)
    check("seller deleted the product -> 200", r.status_code == 200, f"got {r.status_code}")

    r = client.get(f"/api/orders/{doomed_order_id}", headers=buyer)
    check("the order can still be read -> 200", r.status_code == 200, f"got {r.status_code}")

    doomed_order = r.get_json()
    check("the order still shows the product name",
          doomed_order["items"][0]["product_name"].endswith("Doomed Item"),
          f"got {doomed_order['items'][0]['product_name']}")
    check("the order still shows the price", doomed_order["items"][0]["unit_price"] == 300)

    # ---------------------------------------------------------------
    # 10. Order history and privacy
    # ---------------------------------------------------------------
    print("\n10. WHO CAN SEE WHICH ORDERS")

    r = client.get("/api/orders", headers=buyer)
    buyer_orders = r.get_json()
    check("the buyer sees their own orders", len(buyer_orders) >= 2,
          f"got {len(buyer_orders)}")

    r = client.get("/api/orders", headers=other)
    check("a different buyer sees NONE of them", r.get_json() == [],
          f"got {len(r.get_json())}")

    # The other buyer must not be able to read one by id either
    r = client.get(f"/api/orders/{order_id}", headers=other)
    check("another buyer reading the order by id -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # The seller who owns the widget SHOULD see the order
    r = client.get("/api/orders", headers=seller)
    check("the owning seller can see the order",
          any(o["id"] == order_id for o in r.get_json()),
          f"got {[o['id'] for o in r.get_json()]}")

    # Seller two does NOT own any product in that order
    r = client.get(f"/api/orders/{order_id}", headers=seller2)
    check("an unrelated seller reading the order by id -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # The admin sees everything
    r = client.get("/api/orders", headers=admin)
    admin_order_ids = [o["id"] for o in r.get_json()]
    check("the admin can see the order",
          order_id in admin_order_ids, f"got {admin_order_ids}")

    r = client.get(f"/api/orders/{order_id}", headers=admin)
    check("the admin can read it by id -> 200", r.status_code == 200,
          f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 11. Status flow
    # ---------------------------------------------------------------
    print("\n11. STATUS FLOW")

    # A buyer cannot change a status at all
    r = client.put(f"/api/orders/{order_id}/status", json={"status": "Shipped"},
                   headers=buyer)
    check("a buyer cannot change a status -> 403", r.status_code == 403,
          f"got {r.status_code}")

    # Pending -> Delivered must be refused
    r = client.put(f"/api/orders/{order_id}/status", json={"status": "Delivered"},
                   headers=seller)
    check("Pending -> Delivered is refused -> 400", r.status_code == 400,
          f"got {r.status_code}")
    check("the message explains the allowed next steps",
          "Confirmed" in r.get_json().get("error", ""),
          f"got {r.get_json().get('error')!r}")

    # A made-up status is refused
    r = client.put(f"/api/orders/{order_id}/status", json={"status": "Teleported"},
                   headers=seller)
    check("an invented status -> 400", r.status_code == 400, f"got {r.status_code}")

    # The correct chain
    for expected in ["Confirmed", "Shipped", "Delivered"]:
        r = client.put(f"/api/orders/{order_id}/status", json={"status": expected},
                       headers=seller)
        check(f"moved to {expected} -> 200", r.status_code == 200, f"got {r.status_code}")
        check(f"status is really {expected}",
              r.get_json()["order"]["status"] == expected,
              f"got {r.get_json()['order']['status']}")

    # A delivered order is final
    r = client.put(f"/api/orders/{order_id}/status", json={"status": "Cancelled"},
                   headers=seller)
    check("a Delivered order cannot be changed -> 400", r.status_code == 400,
          f"got {r.status_code}")

    # A seller only sees their own products' orders when updating
    r = client.put(f"/api/orders/{doomed_order_id}/status", json={"status": "Confirmed"},
                   headers=seller2)
    check("a seller cannot update an unrelated order -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 12. Cancelling returns the stock
    # ---------------------------------------------------------------
    print("\n12. CANCELLING RETURNS THE STOCK")

    # Put 4 widgets in a cart and order them
    with app.app_context():
        p = db.session.get(Product, widget_id)
        p.stock = 20
        db.session.commit()

    client.post("/api/cart", json={"product_id": widget_id, "quantity": 4},
                headers=buyer)

    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    cancel_order_id = r.get_json()["order"]["id"]

    with app.app_context():
        stock_after_order = db.session.get(Product, widget_id).stock
    check("stock fell to 16 after ordering 4", stock_after_order == 16,
          f"got {stock_after_order}")

    r = client.delete(f"/api/orders/{cancel_order_id}", headers=buyer)
    check("the buyer can cancel their own Pending order -> 200",
          r.status_code == 200, f"got {r.status_code}")
    check("the order is marked Cancelled",
          r.get_json()["order"]["status"] == "Cancelled")

    with app.app_context():
        stock_after_cancel = db.session.get(Product, widget_id).stock
    check("the 4 items went back into stock (16 -> 20)", stock_after_cancel == 20,
          f"got {stock_after_cancel}")

    r = client.delete(f"/api/orders/{cancel_order_id}", headers=buyer)
    check("cancelling it twice -> 400", r.status_code == 400, f"got {r.status_code}")

    # A buyer cannot cancel somebody else's order
    client.post("/api/cart", json={"product_id": widget_id, "quantity": 1},
                headers=buyer)
    r = client.post("/api/orders", json=DELIVERY, headers=buyer)
    protected_order_id = r.get_json()["order"]["id"]

    r = client.delete(f"/api/orders/{protected_order_id}", headers=other)
    check("another buyer cannot cancel your order -> 403",
          r.status_code == 403, f"got {r.status_code}")

    # A buyer cannot cancel once it is past Pending
    client.put(f"/api/orders/{protected_order_id}/status",
               json={"status": "Confirmed"}, headers=seller)
    r = client.delete(f"/api/orders/{protected_order_id}", headers=buyer)
    check("a buyer cannot cancel a Confirmed order -> 400",
          r.status_code == 400, f"got {r.status_code}")

    # ...but a seller still can
    r = client.delete(f"/api/orders/{protected_order_id}", headers=seller)
    check("a seller can still cancel a Confirmed order -> 200",
          r.status_code == 200, f"got {r.status_code}")

    # A delivered order can never be cancelled
    r = client.delete(f"/api/orders/{order_id}", headers=admin)
    check("a Delivered order cannot be cancelled -> 400",
          r.status_code == 400, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 13. Reading a missing order
    # ---------------------------------------------------------------
    print("\n13. MISSING ORDERS")

    r = client.get("/api/orders/999999", headers=buyer)
    check("reading a missing order -> 404", r.status_code == 404, f"got {r.status_code}")

    r = client.delete("/api/orders/999999", headers=admin)
    check("cancelling a missing order -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 14. Status filter
    # ---------------------------------------------------------------
    print("\n14. FILTERING BY STATUS")

    r = client.get("/api/orders?status=Pending", headers=admin)
    check("status filter returns only Pending orders",
          all(o["status"] == "Pending" for o in r.get_json()),
          f"got {[o['status'] for o in r.get_json()]}")

    r = client.get("/api/orders?status=Delivered", headers=admin)
    check("status filter finds the delivered one",
          all(o["status"] == "Delivered" for o in r.get_json()),
          f"got {[o['status'] for o in r.get_json()]}")

    # ---------------------------------------------------------------
    # 15. Real products untouched
    # ---------------------------------------------------------------
    print("\n15. SAFETY")

    with app.app_context():
        real = Product.query.filter(~Product.name.like(f"{TEST_PRODUCT_PREFIX}%")).count()
        real_orders = Order.query.filter(
            Order.user_id.in_([buyer_id, other_id])
        ).count()

    check("the 30 real products are still there", real == 30, f"got {real}")
    check("test orders exist to clean up", real_orders > 0, f"got {real_orders}")

    # ---------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------
    print("\n16. CLEAN UP")

    with app.app_context():
        user_ids = [buyer_id, other_id, seller_id, seller2_id, admin_id]

        # Order items point at orders, so remove them first
        order_ids = [
            o.id for o in Order.query.filter(Order.user_id.in_(user_ids)).all()
        ]

        if order_ids:
            OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).delete(
                synchronize_session=False
            )

        Order.query.filter(Order.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )

        CartItem.query.filter(CartItem.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )

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
        print(f"  Orders in database: {Order.query.count()}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nCheckout works, stock is tracked, and orders are private.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
