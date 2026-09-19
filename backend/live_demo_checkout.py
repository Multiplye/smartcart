"""Live end-to-end walkthrough of the SmartCart checkout flow.

Run with the Flask backend already running:
    python live_demo_checkout.py

It creates its own accounts and product, walks the whole journey, and
cleans up after itself. Nothing is left behind, so it is safe to run
again and again.
"""

import json
import sqlite3
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000"


def call(method, path, body=None, uid=None):
    request = urllib.request.Request(BASE + path, method=method)
    request.add_header("Content-Type", "application/json")

    if uid:
        request.add_header("X-User-Id", str(uid))

    payload = json.dumps(body).encode() if body is not None else None

    try:
        with urllib.request.urlopen(request, payload) as response:
            return response.status, json.loads(response.read() or "null")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or "null")


def account(name, email, role):
    status, result = call("POST", "/api/register", {
        "name": name, "email": email, "password": "demo12345", "role": role,
    })

    if status == 409:
        status, result = call("POST", "/api/login", {
            "email": email, "password": "demo12345",
        })

    return result["user"]["id"]


def main():
    seller = account("Demo Seller", "live.seller@sc.local", "seller")
    buyer = account("Demo Buyer", "live.buyer@sc.local", "buyer")

    created_product = None

    try:
        print("=" * 60)
        print("SMARTCART LIVE CHECKOUT WALKTHROUGH")
        print("=" * 60)

        # --- 1. Seller lists a product ---
        print("\n1. SELLER LISTS A PRODUCT")
        status, result = call("POST", "/api/products", {
            "name": "Live Demo Lamp",
            "description": "A lamp used for the live demo.",
            "price": 1500,
            "category": "Home",
            "stock": 6,
        }, uid=seller)

        product_id = result["product"]["id"]
        created_product = product_id
        print(f"   created product #{product_id}, price Rs. 1500, stock 6")

        # --- 2. Buyer fills the cart ---
        print("\n2. BUYER ADDS 2 TO THE CART")
        status, result = call("POST", "/api/cart",
                              {"product_id": product_id, "quantity": 2}, uid=buyer)
        print(f"   cart: {result['count']} item(s), total Rs. {result['total']}")

        # --- 3. Checkout ---
        print("\n3. BUYER CHECKS OUT")
        status, result = call("POST", "/api/orders", {
            "full_name": "Demo Buyer",
            "phone": "9812345678",
            "address": "5 Demo Road",
            "city": "Pokhara",
        }, uid=buyer)

        order_id = result["order"]["id"]
        order = result["order"]

        print(f"   {status} - {result['message']}")
        print(f"   order #{order_id}, total Rs. {order['total']}, "
              f"status {order['status']}")
        print(f"   deliver to: {order['full_name']}, "
              f"{order['address']}, {order['city']}")

        for item in order["items"]:
            print(f"   line: {item['product_name']} x{item['quantity']} "
                  f"@ Rs. {item['unit_price']} = Rs. {item['subtotal']}")

        # --- 4. Check the side effects ---
        print("\n4. SIDE EFFECTS")
        status, result = call("GET", f"/api/products/{product_id}")
        print(f"   stock is now {result['stock']} (was 6, ordered 2)")

        status, result = call("GET", "/api/cart", uid=buyer)
        print(f"   cart is now {result['count']} items (should be 0)")

        # --- 5. Seller moves the order along ---
        print("\n5. SELLER MOVES THE ORDER ALONG")
        for next_status in ["Confirmed", "Shipped", "Delivered"]:
            status, result = call(
                "PUT", f"/api/orders/{order_id}/status",
                {"status": next_status}, uid=seller
            )
            print(f"   -> {next_status}: {status} "
                  f"{result.get('message') or result.get('error')}")

        # --- 6. Skipping a step is refused ---
        print("\n6. THE STATUS FLOW CANNOT BE SKIPPED")
        status, result = call(
            "PUT", f"/api/orders/{order_id}/status",
            {"status": "Pending"}, uid=seller
        )
        print(f"   Delivered -> Pending: {status} | {result.get('error')}")

        # --- 7. Buyer's history ---
        print("\n7. BUYER ORDER HISTORY")
        status, result = call("GET", "/api/orders", uid=buyer)
        print(f"   the buyer sees {len(result)} order(s); "
              f"#{result[0]['id']} is {result[0]['status']}")

        print("\n" + "=" * 60)
        print("WALKTHROUGH COMPLETE")
        print("=" * 60)

    finally:
        # --- Clean up, whatever happened above ---
        connection = sqlite3.connect("instance/smartcart.db")
        cursor = connection.cursor()

        cursor.execute(
            'DELETE FROM order_item WHERE order_id IN '
            '(SELECT id FROM "order" WHERE user_id IN (?, ?))',
            (seller, buyer)
        )
        cursor.execute('DELETE FROM "order" WHERE user_id IN (?, ?)', (seller, buyer))
        cursor.execute("DELETE FROM cart_item WHERE user_id IN (?, ?)", (seller, buyer))

        if created_product is not None:
            cursor.execute("DELETE FROM product WHERE id = ?", (created_product,))

        cursor.execute("DELETE FROM user WHERE id IN (?, ?)", (seller, buyer))
        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM product")
        products = cursor.fetchone()[0]
        connection.close()

        print(f"\nCleaned up. Products remaining in the database: {products}")


if __name__ == "__main__":
    main()
