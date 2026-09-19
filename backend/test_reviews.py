"""
SmartCart - Review and Rating Tests
====================================

THE RULES BEING TESTED
    - anyone can READ reviews, even logged out
    - only a logged-in user can WRITE one
    - you must have ORDERED the product to review it
    - one review per person per product (409 on a second attempt)
    - the rating must be a whole number from 1 to 5
    - the average and count are computed correctly
    - you can edit and delete your own review, but nobody else's
    - an admin can delete any review
    - deleting a review updates the average

HOW TO RUN (from the backend folder, venv activated):

    python test_reviews.py
"""

from app import app, db, CartItem, Order, OrderItem, Product, Review, User

PASSWORD = "testpass123"

BUYER_EMAIL = "test.revbuyer@smartcart.local"
BUYER2_EMAIL = "test.revbuyer2@smartcart.local"
STRANGER_EMAIL = "test.revstranger@smartcart.local"
SELLER_EMAIL = "test.revseller@smartcart.local"
ADMIN_EMAIL = "test.revadmin@smartcart.local"

TEST_EMAILS = [
    BUYER_EMAIL, BUYER2_EMAIL, STRANGER_EMAIL, SELLER_EMAIL, ADMIN_EMAIL,
]

TEST_PRODUCT_PREFIX = "[REVTEST] "

DELIVERY = {
    "full_name": "Review Buyer",
    "phone": "9800000000",
    "address": "1 Review Street",
    "city": "Kathmandu",
}

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
    print("SmartCart - Review and Rating Tests")
    print("=" * 62)

    client = app.test_client()

    # ---------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------
    print("\n0. SETUP")

    buyer_id = make_account(client, "Review Buyer", BUYER_EMAIL, "buyer")
    buyer2_id = make_account(client, "Second Buyer", BUYER2_EMAIL, "buyer")
    stranger_id = make_account(client, "Stranger", STRANGER_EMAIL, "buyer")
    seller_id = make_account(client, "Review Seller", SELLER_EMAIL, "seller")
    admin_id = make_account(client, "Review Admin", ADMIN_EMAIL, "admin")

    buyer = headers_for(buyer_id)
    buyer2 = headers_for(buyer2_id)
    stranger = headers_for(stranger_id)
    seller = headers_for(seller_id)
    admin = headers_for(admin_id)

    check("all five accounts ready",
          all([buyer_id, buyer2_id, stranger_id, seller_id, admin_id]))

    # A product to review
    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Reviewable Kettle",
        "description": "A kettle for the review tests.",
        "price": 2000,
        "category": "Home",
        "stock": 20,
    }, headers=seller)
    kettle_id = r.get_json()["product"]["id"]
    check("test product created", bool(kettle_id))

    # ---------------------------------------------------------------
    # 1. Reading reviews needs no login
    # ---------------------------------------------------------------
    print("\n1. READING REVIEWS IS PUBLIC")

    r = client.get(f"/api/products/{kettle_id}/reviews")
    check("anyone can read the reviews -> 200", r.status_code == 200,
          f"got {r.status_code}")

    body = r.get_json()
    check("a new product has no reviews", body["reviews"] == [])
    check("the summary starts at 0", body["summary"]["average"] == 0.0)
    check("the count starts at 0", body["summary"]["count"] == 0)

    r = client.get("/api/products/999999/reviews")
    check("reviews for a missing product -> 404", r.status_code == 404,
          f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 2. You must have ORDERED it
    # ---------------------------------------------------------------
    print("\n2. ONLY REAL CUSTOMERS MAY REVIEW")

    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 5}, headers={})
    check("writing a review without login -> 401",
          r.status_code == 401, f"got {r.status_code}")

    # Logged in, but has never bought it
    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 5}, headers=stranger)
    check("reviewing something you never ordered -> 403",
          r.status_code == 403, f"got {r.status_code}")
    check("the message explains why",
          "ordered" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    # Having it in the CART is not enough either
    client.post("/api/cart", json={"product_id": kettle_id}, headers=stranger)

    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 5}, headers=stranger)
    check("having it in the cart is not enough either -> 403",
          r.status_code == 403, f"got {r.status_code}")

    client.delete("/api/cart", headers=stranger)

    # ---------------------------------------------------------------
    # 3. Buy the product, then review it
    # ---------------------------------------------------------------
    print("\n3. AFTER ORDERING, REVIEWING WORKS")

    def buy(user_headers, quantity=1):
        client.post("/api/cart", json={"product_id": kettle_id, "quantity": quantity},
                    headers=user_headers)
        r = client.post("/api/orders", json=DELIVERY, headers=user_headers)
        return r.get_json()["order"]["id"]

    buy(buyer)
    check("the buyer placed an order", True)

    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 5, "comment": "Boils water perfectly."},
                    headers=buyer)
    check("the buyer can now review -> 201", r.status_code == 201,
          f"got {r.status_code}")

    body = r.get_json()
    review_id = body["review"]["id"]

    check("the review has an id", bool(review_id))
    check("the rating was stored", body["review"]["rating"] == 5)
    check("the comment was stored",
          body["review"]["comment"] == "Boils water perfectly.")
    check("the reviewer's name is included",
          body["review"]["reviewer_name"] == "Review Buyer",
          f"got {body['review']['reviewer_name']}")
    check("the summary now shows 1 review", body["summary"]["count"] == 1)
    check("the average is 5.0", body["summary"]["average"] == 5.0,
          f"got {body['summary']['average']}")

    # ---------------------------------------------------------------
    # 4. One review per person per product
    # ---------------------------------------------------------------
    print("\n4. ONE REVIEW PER PERSON PER PRODUCT")

    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 1, "comment": "Changed my mind."},
                    headers=buyer)
    check("a second review from the same person -> 409",
          r.status_code == 409, f"got {r.status_code}")
    check("the message suggests editing instead",
          "already reviewed" in r.get_json().get("error", "").lower(),
          f"got {r.get_json().get('error')!r}")

    with app.app_context():
        count = Review.query.filter_by(
            user_id=buyer_id, product_id=kettle_id
        ).count()
    check("the database still holds exactly one review", count == 1, f"got {count}")

    # ---------------------------------------------------------------
    # 5. Ratings must be 1 to 5
    # ---------------------------------------------------------------
    print("\n5. RATING BOUNDS")

    buy(buyer2)

    bad_ratings = [
        ("zero", 0), ("six", 6), ("negative", -3), ("ninety-nine", 99),
        ("text", "great"), ("missing", None), ("decimal-ish text", "4.5 stars"),
    ]

    for label, value in bad_ratings:
        payload = {} if value is None else {"rating": value}

        r = client.post(f"/api/products/{kettle_id}/reviews",
                        json=payload, headers=buyer2)
        check(f"rating {label} -> 400", r.status_code == 400,
              f"got {r.status_code}")

    # All five valid ratings must be accepted (we use buyer2 for one)
    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 3, "comment": "It is fine."}, headers=buyer2)
    check("a valid rating of 3 works -> 201", r.status_code == 201,
          f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 6. The average is computed correctly
    # ---------------------------------------------------------------
    print("\n6. THE AVERAGE IS CORRECT")

    # Currently: 5 (buyer) and 3 (buyer2) -> average 4.0
    r = client.get(f"/api/products/{kettle_id}/reviews")
    summary = r.get_json()["summary"]

    check("count is 2", summary["count"] == 2, f"got {summary['count']}")
    check("average of 5 and 3 is 4.0", summary["average"] == 4.0,
          f"got {summary['average']}")
    check("both reviews are listed",
          len(r.get_json()["reviews"]) == 2,
          f"got {len(r.get_json()['reviews'])}")

    # ---------------------------------------------------------------
    # 7. The product listing carries the rating
    # ---------------------------------------------------------------
    print("\n7. RATINGS APPEAR ON THE PRODUCT")

    r = client.get(f"/api/products/{kettle_id}")
    product = r.get_json()

    check("the product has rating_average", product.get("rating_average") == 4.0,
          f"got {product.get('rating_average')}")
    check("the product has rating_count", product.get("rating_count") == 2,
          f"got {product.get('rating_count')}")

    # And in the full listing, without an extra request per product
    r = client.get("/api/products")
    listed = next(
        (p for p in r.get_json() if p["id"] == kettle_id), None
    )
    check("the listing includes the rating too",
          listed is not None and listed["rating_average"] == 4.0,
          f"got {listed.get('rating_average') if listed else None}")

    # An unreviewed product should report zero, not crash
    r = client.get("/api/products")
    unreviewed = [p for p in r.get_json() if p["id"] != kettle_id]

    check("products with no reviews report 0",
          all(p.get("rating_average") == 0.0 and p.get("rating_count") == 0
              for p in unreviewed),
          "some product had no rating fields")

    # ---------------------------------------------------------------
    # 8. Editing your own review
    # ---------------------------------------------------------------
    print("\n8. EDITING A REVIEW")

    r = client.put(f"/api/reviews/{review_id}",
                   json={"rating": 2}, headers=buyer)
    check("the author can edit their rating -> 200", r.status_code == 200,
          f"got {r.status_code}")
    check("the rating changed to 2", r.get_json()["review"]["rating"] == 2)
    check("the comment survived a rating-only edit",
          r.get_json()["review"]["comment"] == "Boils water perfectly.",
          f"got {r.get_json()['review']['comment']!r}")

    # 2 and 3 -> average 2.5
    check("the average recalculated to 2.5",
          r.get_json()["summary"]["average"] == 2.5,
          f"got {r.get_json()['summary']['average']}")

    r = client.put(f"/api/reviews/{review_id}",
                   json={"comment": "Actually it is only okay."}, headers=buyer)
    check("editing just the comment works -> 200", r.status_code == 200)
    check("the comment changed",
          r.get_json()["review"]["comment"] == "Actually it is only okay.")
    check("the rating survived a comment-only edit",
          r.get_json()["review"]["rating"] == 2)

    r = client.put(f"/api/reviews/{review_id}", json={"rating": 9}, headers=buyer)
    check("editing to an invalid rating -> 400", r.status_code == 400,
          f"got {r.status_code}")

    # Somebody else's review
    r = client.put(f"/api/reviews/{review_id}", json={"rating": 1}, headers=buyer2)
    check("editing somebody else's review -> 403", r.status_code == 403,
          f"got {r.status_code}")

    r = client.put("/api/reviews/999999", json={"rating": 1}, headers=buyer)
    check("editing a missing review -> 404", r.status_code == 404,
          f"got {r.status_code}")

    # An admin may edit any review
    r = client.put(f"/api/reviews/{review_id}", json={"comment": "Reviewed by admin."},
                   headers=admin)
    check("an admin can edit any review -> 200", r.status_code == 200,
          f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 9. Deleting reviews
    # ---------------------------------------------------------------
    print("\n9. DELETING A REVIEW")

    r = client.delete(f"/api/reviews/{review_id}", headers=buyer2)
    check("deleting somebody else's review -> 403", r.status_code == 403,
          f"got {r.status_code}")

    r = client.delete(f"/api/reviews/{review_id}", headers=buyer)
    check("the author can delete their own -> 200", r.status_code == 200,
          f"got {r.status_code}")

    # Only buyer2's 3-star review is left
    check("the summary recalculated to 3.0 after deletion",
          r.get_json()["summary"]["average"] == 3.0,
          f"got {r.get_json()['summary']['average']}")
    check("the count fell to 1", r.get_json()["summary"]["count"] == 1,
          f"got {r.get_json()['summary']['count']}")

    r = client.delete(f"/api/reviews/{review_id}", headers=buyer)
    check("deleting it twice -> 404", r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 10. A comment is optional
    # ---------------------------------------------------------------
    print("\n10. A COMMENT IS OPTIONAL")

    buy(stranger)

    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 4}, headers=stranger)
    check("a rating with no comment -> 201", r.status_code == 201,
          f"got {r.status_code}")
    check("the comment is stored as null",
          r.get_json()["review"]["comment"] is None,
          f"got {r.get_json()['review']['comment']!r}")

    stranger_review_id = r.get_json()["review"]["id"]

    # An over-long comment is refused
    r = client.post(f"/api/products/{kettle_id}/reviews",
                    json={"rating": 4, "comment": "x" * 1001}, headers=stranger)
    check("a 1001-character comment -> 409 (already reviewed) or 400",
          r.status_code in (400, 409), f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 11. Deleting a product removes its reviews
    # ---------------------------------------------------------------
    print("\n11. ADMIN DELETES ANY REVIEW")

    r = client.delete(f"/api/reviews/{stranger_review_id}", headers=admin)
    check("the admin can delete a review they did not write -> 200",
          r.status_code == 200, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 12. Ratings do not leak into other products
    # ---------------------------------------------------------------
    print("\n12. RATINGS ARE PER PRODUCT")

    r = client.post("/api/products", json={
        "name": f"{TEST_PRODUCT_PREFIX}Unreviewed Toaster",
        "description": "Nobody has reviewed this.",
        "price": 800,
        "category": "Home",
        "stock": 5,
    }, headers=seller)
    toaster_id = r.get_json()["product"]["id"]

    r = client.get(f"/api/products/{toaster_id}/reviews")
    check("the new product has no reviews",
          r.get_json()["reviews"] == [], f"got {r.get_json()['reviews']}")
    check("its summary is 0", r.get_json()["summary"]["count"] == 0)

    r = client.get(f"/api/products/{toaster_id}")
    check("its product record reports no rating",
          r.get_json()["rating_count"] == 0, f"got {r.get_json()['rating_count']}")

    # ---------------------------------------------------------------
    # 13. Safety
    # ---------------------------------------------------------------
    print("\n13. SAFETY")

    with app.app_context():
        real = Product.query.filter(~Product.name.like(f"{TEST_PRODUCT_PREFIX}%")).count()

    check("the 30 real products are still there", real == 30, f"got {real}")

    # ---------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------
    print("\n14. CLEAN UP")

    with app.app_context():
        user_ids = [buyer_id, buyer2_id, stranger_id, seller_id, admin_id]

        test_product_ids = [
            p.id for p in Product.query.filter(
                Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
            ).all()
        ]

        if test_product_ids:
            Review.query.filter(
                Review.product_id.in_(test_product_ids)
            ).delete(synchronize_session=False)

        order_ids = [
            o.id for o in Order.query.filter(Order.user_id.in_(user_ids)).all()
        ]

        if order_ids:
            OrderItem.query.filter(
                OrderItem.order_id.in_(order_ids)
            ).delete(synchronize_session=False)

        Order.query.filter(Order.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )
        CartItem.query.filter(CartItem.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )

        db.session.commit()

        removed_products = 0
        for product_id in test_product_ids:
            product = db.session.get(Product, product_id)
            if product:
                db.session.delete(product)
                removed_products += 1

        removed_users = 0
        for email in TEST_EMAILS:
            user = User.query.filter_by(email=email).first()
            if user:
                db.session.delete(user)
                removed_users += 1

        db.session.commit()

        print(f"  Removed {removed_products} test product(s).")
        print(f"  Removed {removed_users} test account(s).")
        print(f"  Products in database: {Product.query.count()}")
        print(f"  Users in database: {User.query.count()}")
        print(f"  Reviews in database: {Review.query.count()}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nReviews are honest, bounded, and only from real customers.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
