"""Live walkthrough of the review flow.

Run with the Flask backend already running:
    python live_demo_reviews.py

Creates its own accounts and product, posts reviews, and cleans up.
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


DELIVERY = {
    "full_name": "Live Reviewer",
    "phone": "9800000000",
    "address": "9 Demo Lane",
    "city": "Lalitpur",
}


def main():
    seller = account("Live Seller", "live.revseller@sc.local", "seller")
    alice = account("Alice Reviewer", "live.alice@sc.local", "buyer")
    bob = account("Bob Reviewer", "live.bob@sc.local", "buyer")
    nosy = account("Nosy Visitor", "live.nosy@sc.local", "buyer")

    product_id = None

    try:
        print("=" * 60)
        print("SMARTCART LIVE REVIEW WALKTHROUGH")
        print("=" * 60)

        status, result = call("POST", "/api/products", {
            "name": "Live Review Kettle",
            "description": "A kettle for the live review demo.",
            "price": 2500,
            "category": "Home",
            "stock": 10,
        }, uid=seller)

        product_id = result["product"]["id"]
        print(f"\n1. Seller created product #{product_id}")

        # --- Someone who never bought it ---
        print("\n2. SOMEONE WHO NEVER BOUGHT IT TRIES TO REVIEW")
        status, result = call("POST", f"/api/products/{product_id}/reviews",
                              {"rating": 5, "comment": "Looks great!"}, uid=nosy)
        print(f"   {status} - {result.get('error')}")

        # --- Alice buys, then reviews ---
        print("\n3. ALICE BUYS IT, THEN REVIEWS IT")
        call("POST", "/api/cart", {"product_id": product_id}, uid=alice)
        status, result = call("POST", "/api/orders", DELIVERY, uid=alice)
        print(f"   order placed: {result['message']}")

        status, result = call("POST", f"/api/products/{product_id}/reviews",
                              {"rating": 5, "comment": "Excellent kettle."},
                              uid=alice)
        print(f"   reviewing: {status} - {result.get('message')}")
        print(f"   summary now: {result['summary']}")

        # --- A second review from Alice is refused ---
        status, result = call("POST", f"/api/products/{product_id}/reviews",
                              {"rating": 1}, uid=alice)
        print(f"\n4. ALICE TRIES AGAIN: {status} - {result.get('error')}")

        # --- Bob buys and gives 3 stars ---
        print("\n5. BOB BUYS IT AND GIVES 3 STARS")
        call("POST", "/api/cart", {"product_id": product_id}, uid=bob)
        call("POST", "/api/orders", DELIVERY, uid=bob)
        status, result = call("POST", f"/api/products/{product_id}/reviews",
                              {"rating": 3, "comment": "Does the job."}, uid=bob)
        print(f"   summary now: {result['summary']}")
        print("   (5 and 3 -> average 4.0)")

        # --- The average shows on the product ---
        print("\n6. THE PRODUCT CARRIES THE RATING")
        status, result = call("GET", f"/api/products/{product_id}")
        print(f"   rating_average: {result['rating_average']}, "
              f"rating_count: {result['rating_count']}")

        # --- Public reading ---
        print("\n7. ANYONE CAN READ THE REVIEWS (NO LOGIN)")
        status, result = call("GET", f"/api/products/{product_id}/reviews")
        print(f"   {status} - {result['summary']['count']} review(s), "
              f"average {result['summary']['average']}")
        for review in result["reviews"]:
            print(f"   {review['reviewer_name']}: {review['rating']} stars"
                  f" - {review['comment']}")

        # --- Bob tries to edit Alice's review ---
        alice_review_id = next(
            r["id"] for r in result["reviews"]
            if r["reviewer_name"] == "Alice Reviewer"
        )

        print("\n8. BOB TRIES TO EDIT ALICE'S REVIEW")
        status, result = call("PUT", f"/api/reviews/{alice_review_id}",
                              {"rating": 1}, uid=bob)
        print(f"   {status} - {result.get('error')}")

        print("\n" + "=" * 60)
        print("WALKTHROUGH COMPLETE")
        print("=" * 60)

    finally:
        connection = sqlite3.connect("instance/smartcart.db")
        cursor = connection.cursor()

        user_ids = (seller, alice, bob, nosy)

        if product_id is not None:
            cursor.execute("DELETE FROM review WHERE product_id = ?", (product_id,))

        cursor.execute(
            'DELETE FROM order_item WHERE order_id IN '
            '(SELECT id FROM "order" WHERE user_id IN (?, ?, ?, ?))',
            user_ids
        )
        cursor.execute(
            'DELETE FROM "order" WHERE user_id IN (?, ?, ?, ?)', user_ids
        )
        cursor.execute(
            "DELETE FROM cart_item WHERE user_id IN (?, ?, ?, ?)", user_ids
        )

        if product_id is not None:
            cursor.execute("DELETE FROM product WHERE id = ?", (product_id,))

        cursor.execute("DELETE FROM user WHERE id IN (?, ?, ?, ?)", user_ids)
        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM product")
        products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM review")
        reviews = cursor.fetchone()[0]
        connection.close()

        print(f"\nCleaned up. Products: {products}, Reviews: {reviews}")


if __name__ == "__main__":
    main()
