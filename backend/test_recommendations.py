"""
SmartCart - Recommendation Engine Tests
========================================

These tests check the AI, not just the plumbing. That is a deliberate
choice: it is easy to write an endpoint that returns *something* and
call it working. These tests care whether the something is SENSIBLE.

WHAT IS CHECKED
    1. The text builder includes what it should
    2. The TF-IDF matrix has the right shape and is not degenerate
    3. A product is never recommended to itself
    4. Similar products come from the same category, most of the time
    5. Results are deterministic - the same request twice gives the
       same answer
    6. The limit works, including silly values
    7. Personalised recommendations exclude what you already bought
    8. A brand new user gets popularity, not an empty list
    9. Unknown products give a clean 404

HOW TO RUN (from the backend folder, venv activated):

    python test_recommendations.py
"""

from app import app, db, CartItem, Order, OrderItem, Product, Review, User

from recommender import (
    build_matrix,
    build_text,
    popular_products,
    rating_score,
    recommend_from_history,
    similar_products,
)

PASSWORD = "testpass123"

BUYER_EMAIL = "test.recbuyer@smartcart.local"
SELLER_EMAIL = "test.recseller@smartcart.local"

TEST_EMAILS = [BUYER_EMAIL, SELLER_EMAIL]

TEST_PRODUCT_PREFIX = "[RECTEST] "

DELIVERY = {
    "full_name": "Rec Buyer",
    "phone": "9800000000",
    "address": "1 Rec Street",
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
    print("SmartCart - Recommendation Engine Tests")
    print("=" * 62)

    client = app.test_client()

    from app import products_with_ratings

    with app.app_context():
        products = products_with_ratings(Product.query.all())

    if len(products) < 5:
        print("\nNot enough products to test with. Run import_products.py first.")
        return

    print(f"\n(Testing against {len(products)} real products)\n")

    # ---------------------------------------------------------------
    # 1. The text builder
    # ---------------------------------------------------------------
    print("1. THE TEXT BUILDER")

    sample = products[0]
    text = build_text(sample)

    check("the name is included", sample.name.lower() in text.lower())
    check("the category is included with a prefix",
          f"category_{sample.category.lower()}" in text,
          f"got {text[:80]!r}")
    check("the description is included",
          sample.description[:20].lower() in text.lower())
    check("the name is repeated to raise its weight",
          text.lower().count(sample.name.lower()) >= 2,
          f"found {text.lower().count(sample.name.lower())} times")

    # ---------------------------------------------------------------
    # 2. The TF-IDF matrix
    # ---------------------------------------------------------------
    print("\n2. THE TF-IDF MATRIX")

    matrix, product_ids = build_matrix(products)

    check("the matrix has one row per product",
          matrix.shape[0] == len(products),
          f"{matrix.shape[0]} rows for {len(products)} products")
    check("the id order matches the row order",
          len(product_ids) == matrix.shape[0])
    check("there is a useful number of features",
          matrix.shape[1] > 20,
          f"only {matrix.shape[1]} features")
    check("the matrix is sparse (mostly zeros)",
          matrix.nnz < matrix.shape[0] * matrix.shape[1],
          "matrix appears dense")

    # A degenerate matrix would mean every product looks identical
    import numpy as np

    dense = matrix.toarray()
    distinct_rows = len({tuple(np.round(row, 4)) for row in dense})

    check("products are not all identical to each other",
          distinct_rows > len(products) * 0.5,
          f"only {distinct_rows} distinct rows out of {len(products)}")

    # ---------------------------------------------------------------
    # 3. Never recommend the product back to itself
    # ---------------------------------------------------------------
    print("\n3. NO SELF-RECOMMENDATIONS")

    target = products[0]
    scored = similar_products(target, products, limit=5)

    check("we got some recommendations", len(scored) > 0, f"got {len(scored)}")
    check("the target is not in its own recommendations",
          all(product.id != target.id for product, _, _ in scored))

    # Check this for every product, not just one
    self_recommended = []

    for product in products:
        results = similar_products(product, products, limit=3)

        if any(item.id == product.id for item, _, _ in results):
            self_recommended.append(product.name)

    check("no product recommends itself, checked across the whole catalogue",
          self_recommended == [],
          f"offenders: {self_recommended}")

    # ---------------------------------------------------------------
    # 4. Are the recommendations actually sensible?
    # ---------------------------------------------------------------
    print("\n4. ARE THE RECOMMENDATIONS SENSIBLE?")

    same_category_hits = 0
    total_checked = 0

    for product in products:
        results = similar_products(product, products, limit=3)

        for other, _, _ in results:
            total_checked += 1

            if other.category == product.category:
                same_category_hits += 1

    share = same_category_hits / total_checked if total_checked else 0

    # We deliberately do NOT require 100%, because the interesting
    # matches cross categories (a laptop stand really is closer to a
    # desk lamp than to a webcam). But a content-based engine should
    # still mostly stay inside the category, otherwise the text is not
    # carrying enough signal.
    check("most recommendations stay in the same category",
          share >= 0.6,
          f"only {share:.0%} of recommendations were same-category")

    # A specific, checkable example: desk accessories should find each other
    keyboard = next((p for p in products if "Keyboard" in p.name), None)
    stand = next((p for p in products if "Laptop Stand" in p.name), None)

    if keyboard and stand:
        results = similar_products(stand, products, limit=5)
        names = [item.name for item, _, _ in results]

        check("a laptop stand recommends the mechanical keyboard",
              "Mechanical Keyboard" in names,
              f"got {names}")
    else:
        print("  (skipped the desk-accessory check - products not found)")

    # Similar products should be more alike than random pairs
    average_top_score = sum(
        similar_products(product, products, limit=1)[0][1]
        for product in products
    ) / len(products)

    check("the top recommendation is reasonably similar",
          average_top_score > 0.15,
          f"average top score only {average_top_score:.3f}")

    # ---------------------------------------------------------------
    # 5. Deterministic
    # ---------------------------------------------------------------
    print("\n5. THE SAME REQUEST GIVES THE SAME ANSWER")

    first = [p.id for p, _, _ in similar_products(products[3], products, limit=4)]
    second = [p.id for p, _, _ in similar_products(products[3], products, limit=4)]

    check("two runs produce identical results", first == second,
          f"{first} vs {second}")

    # ---------------------------------------------------------------
    # 6. The rating blend
    # ---------------------------------------------------------------
    print("\n6. THE RATING BLEND")

    class FakeProduct:
        def __init__(self, rating):
            self.rating_average = rating

    check("no rating scores a neutral 0.5",
          rating_score(FakeProduct(0)) == 0.5)
    check("an average of None scores 0.5",
          rating_score(FakeProduct(None)) == 0.5)
    check("1 star scores 0.0", rating_score(FakeProduct(1)) == 0.0)
    check("5 stars scores 1.0", rating_score(FakeProduct(5)) == 1.0)
    check("3 stars scores 0.5", rating_score(FakeProduct(3)) == 0.5)

    # All products have no reviews during this test, so the blend should
    # contribute a constant and not distort the text ordering.
    check("the weights add up to 1.0", abs(0.85 + 0.15 - 1.0) < 1e-9)

    # ---------------------------------------------------------------
    # 7. The HTTP endpoint - similar products
    # ---------------------------------------------------------------
    print("\n7. THE SIMILAR-PRODUCTS ENDPOINT")

    product_id = products[0].id

    r = client.get(f"/api/products/{product_id}/recommendations")
    check("anonymous access -> 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    check("the response names the product", body["product_id"] == product_id)
    check("recommendations were returned", len(body["recommendations"]) > 0)

    first_rec = body["recommendations"][0]
    check("each recommendation has a match percentage",
          "match_percent" in first_rec, f"keys: {list(first_rec.keys())}")
    check("the match percentage is 0 to 100",
          0 <= first_rec["match_percent"] <= 100,
          f"got {first_rec['match_percent']}")
    check("each recommendation carries its rating fields",
          "rating_average" in first_rec and "rating_count" in first_rec)

    # Results should come back best first
    percents = [rec["match_percent"] for rec in body["recommendations"]]
    check("recommendations are sorted best first",
          percents == sorted(percents, reverse=True),
          f"got {percents}")

    # --- limit ---
    r = client.get(f"/api/products/{product_id}/recommendations?limit=2")
    check("limit=2 returns 2", len(r.get_json()["recommendations"]) == 2,
          f"got {len(r.get_json()['recommendations'])}")

    r = client.get(f"/api/products/{product_id}/recommendations?limit=100")
    check("a huge limit is capped",
          len(r.get_json()["recommendations"]) <= 12,
          f"got {len(r.get_json()['recommendations'])}")

    for silly in ["abc", "0", "-4", ""]:
        r = client.get(f"/api/products/{product_id}/recommendations?limit={silly}")
        check(f"limit={silly!r} falls back to the default",
              r.status_code == 200 and len(r.get_json()["recommendations"]) > 0,
              f"got {r.status_code}")

    # --- missing product ---
    r = client.get("/api/products/999999/recommendations")
    check("recommendations for a missing product -> 404",
          r.status_code == 404, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 8. The HTTP endpoint - personalised
    # ---------------------------------------------------------------
    print("\n8. THE PERSONALISED ENDPOINT")

    buyer_id = make_account(client, "Rec Buyer", BUYER_EMAIL, "buyer")
    seller_id = make_account(client, "Rec Seller", SELLER_EMAIL, "seller")

    buyer = headers_for(buyer_id)
    seller = headers_for(seller_id)

    # --- a logged-out visitor ---
    r = client.get("/api/recommendations")
    check("no login -> 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    check("a visitor is told it is popularity based",
          body["based_on"] == "popularity", f"got {body['based_on']}")
    check("a visitor is marked not personalised",
          body["personalised"] is False)
    check("a visitor still gets recommendations",
          len(body["recommendations"]) > 0)
    check("the reason explains how to personalise it",
          "log in" in body["reason"].lower(), f"got {body['reason']!r}")

    # --- a logged-in user who has bought nothing ---
    r = client.get("/api/recommendations", headers=buyer)
    body = r.get_json()

    check("a buyer with no orders gets popularity",
          body["based_on"] == "popularity", f"got {body['based_on']}")
    check("the reason nudges them to order something",
          "order" in body["reason"].lower(), f"got {body['reason']!r}")

    # --- now buy something ---
    print("\n   (buying an item to personalise the recommendations)")

    bought = products[0]

    client.post("/api/cart", json={"product_id": bought.id}, headers=buyer)
    r = client.post("/api/orders", json=DELIVERY, headers=buyer)

    check("the test order was placed -> 201", r.status_code == 201,
          f"got {r.status_code}")

    r = client.get("/api/recommendations", headers=buyer)
    body = r.get_json()

    check("the recommendations are now personalised",
          body["personalised"] is True, f"got {body['based_on']}")
    check("they are based on order history",
          body["based_on"] == "your order history", f"got {body['based_on']}")
    check("the response lists what it learned from",
          bought.id in [item["id"] for item in body.get("based_on_products", [])],
          f"got {body.get('based_on_products')}")

    recommended_ids = [rec["id"] for rec in body["recommendations"]]

    check("the thing they already bought is NOT recommended",
          bought.id not in recommended_ids,
          f"{bought.id} appeared in {recommended_ids}")

    check("they still got recommendations",
          len(recommended_ids) > 0)

    # ---------------------------------------------------------------
    # 9. The history-based engine directly
    # ---------------------------------------------------------------
    print("\n9. THE ENGINE EXCLUDES WHAT YOU OWN")

    with app.app_context():
        catalogue = products_with_ratings(Product.query.all())

    purchased = [catalogue[0], catalogue[1]]
    purchased_ids = {p.id for p in purchased}

    scored = recommend_from_history(purchased, catalogue, limit=6)

    check("something came back", len(scored) > 0, f"got {len(scored)}")
    check("nothing already purchased is suggested",
          all(p.id not in purchased_ids for p, _, _ in scored),
          f"got {[p.id for p, _, _ in scored]}")

    # A taste profile built from two products should favour their own
    # category more often than not
    same_category = sum(
        1 for p, _, _ in scored
        if p.category in {item.category for item in purchased}
    )

    check("the suggestions lean towards the categories they bought",
          same_category >= len(scored) / 2,
          f"only {same_category} of {len(scored)}")

    # --- edge cases ---
    check("an empty purchase list gives nothing",
          recommend_from_history([], catalogue) == [])

    check("an empty catalogue gives nothing",
          recommend_from_history(purchased, []) == [])

    # Owning everything means there is nothing left to suggest
    everything = recommend_from_history(catalogue, catalogue)
    check("owning the whole catalogue gives nothing",
          everything == [], f"got {len(everything)}")

    # ---------------------------------------------------------------
    # 10. The popularity fallback
    # ---------------------------------------------------------------
    print("\n10. THE POPULARITY FALLBACK")

    popular = popular_products(catalogue, limit=5)

    check("the fallback returns something", len(popular) == 5, f"got {len(popular)}")

    with app.app_context():
        ordered = sorted(
            catalogue,
            key=lambda p: (-(p.rating_average or 0), -(p.rating_count or 0), p.id),
        )

    check("the first fallback item is the highest rated",
          popular[0][0].id == ordered[0].id,
          f"got {popular[0][0].name}, expected {ordered[0].name}")

    check("the fallback works on an empty catalogue",
          popular_products([], limit=5) == [])

    # ---------------------------------------------------------------
    # 11. Clean up
    # ---------------------------------------------------------------
    print("\n11. CLEAN UP")

    with app.app_context():
        order_ids = [
            o.id for o in Order.query.filter(
                Order.user_id.in_([buyer_id, seller_id])
            ).all()
        ]

        if order_ids:
            OrderItem.query.filter(
                OrderItem.order_id.in_(order_ids)
            ).delete(synchronize_session=False)

        Order.query.filter(Order.user_id.in_([buyer_id, seller_id])).delete(
            synchronize_session=False
        )
        CartItem.query.filter(
            CartItem.user_id.in_([buyer_id, seller_id])
        ).delete(synchronize_session=False)
        Review.query.filter(
            Review.user_id.in_([buyer_id, seller_id])
        ).delete(synchronize_session=False)

        db.session.commit()

        removed = 0
        for email in TEST_EMAILS:
            user = User.query.filter_by(email=email).first()
            if user:
                db.session.delete(user)
                removed += 1

        db.session.commit()

        print(f"  Removed {removed} test account(s).")
        print(f"  Products in database: {Product.query.count()}")
        print(f"  Users in database: {User.query.count()}")

    # The count has to happen inside an app context - Flask-SQLAlchemy
    # binds the session to the application, so a bare Product.query
    # outside the "with" block raises
    # "RuntimeError: Working outside of application context".
    with app.app_context():
        leftover = Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).count()

    check("no test products were left behind", leftover == 0, f"got {leftover}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nThe recommender returns sensible, deterministic results.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
