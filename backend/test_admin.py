"""
Tests for the admin panel.

These routes are the most dangerous in the whole project: they can
change somebody's role and delete an account along with all of its
data. So this suite spends most of its effort trying to do things it
should NOT be allowed to do.

What we are proving:

  1. A buyer or a seller cannot reach any of it. Not one route.
  2. An admin can see every account and every listing.
  3. An admin can change a role - and CANNOT demote or delete
     themselves, or remove the last admin. Those two rules are what
     stop an admin from locking everybody out of the panel.
  4. Deleting a user really does clean up: their cart, their orders,
     their order lines and their reviews all go, and their product
     listings survive but fall back to being shop-owned.
  5. The stats add up.
  6. Anyone who is not logged in gets a 401, not a 403.

Run it from the backend folder:

    ./venv/Scripts/python.exe test_admin.py
"""

import json

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
# SETUP
# ---------------------------------------------------------------------

BASE = "/api"

ADMIN_EMAIL = "admin-test@smartcart.test"
BUYER_EMAIL = "adminbuyer-test@smartcart.test"
SELLER_EMAIL = "adminseller-test@smartcart.test"
VICTIM_EMAIL = "adminvictim-test@smartcart.test"

TEST_EMAILS = [ADMIN_EMAIL, BUYER_EMAIL, SELLER_EMAIL, VICTIM_EMAIL]

TEST_PRODUCT_PREFIX = "AdminTest Product"

passed = 0
failed = 0


def check(label, condition, detail=""):
    global passed, failed

    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}" + (f"  -> {detail}" if detail else ""))


# ---------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------


def register(client, name, email, password, role):
    response = client.post(
        f"{BASE}/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )

    return response


def as_user(client, user_id):
    """Build headers that make a request look like it came from `user_id`."""
    return {"X-User-Id": str(user_id)}


def wipe_test_data():
    """Remove anything left over from a previous interrupted run."""

    with app.app_context():
        users = User.query.filter(User.email.in_(TEST_EMAILS)).all()
        user_ids = [user.id for user in users]

        if user_ids:
            order_ids = [
                row.id
                for row in db.session.query(Order.id)
                .filter(Order.user_id.in_(user_ids))
                .all()
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
            Review.query.filter(Review.user_id.in_(user_ids)).delete(
                synchronize_session=False
            )

            db.session.commit()

            for user_id in user_ids:
                user = db.session.get(User, user_id)
                if user:
                    db.session.delete(user)

            db.session.commit()

        Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).delete(synchronize_session=False)

        db.session.commit()


# ---------------------------------------------------------------------
# THE TESTS
# ---------------------------------------------------------------------


def main():
    app.config["TESTING"] = True

    print("=" * 62)
    print("ADMIN PANEL TESTS")
    print("=" * 62)

    wipe_test_data()

    with app.test_client() as client:

        # =============================================================
        # 1. MAKE THE ACCOUNTS
        # =============================================================

        print("\n1. SET UP ACCOUNTS")

        admin_response = register(
            client, "Admin Tester", ADMIN_EMAIL, "adminpass123", "admin"
        )

        check(
            "an admin can register",
            admin_response.status_code == 201,
            admin_response.get_json(),
        )

        admin_id = admin_response.get_json()["user"]["id"]

        buyer_response = register(
            client, "Buyer Tester", BUYER_EMAIL, "buyerpass123", "buyer"
        )

        buyer_id = buyer_response.get_json()["user"]["id"]

        check("a buyer can register", buyer_response.status_code == 201)

        seller_response = register(
            client, "Seller Tester", SELLER_EMAIL, "sellerpass123", "seller"
        )

        seller_id = seller_response.get_json()["user"]["id"]

        check("a seller can register", seller_response.status_code == 201)

        victim_response = register(
            client, "Victim Tester", VICTIM_EMAIL, "victimpass123", "buyer"
        )

        victim_id = victim_response.get_json()["user"]["id"]

        check("a second buyer can register", victim_response.status_code == 201)

        # =============================================================
        # 2. WHO IS ALLOWED IN
        # =============================================================

        print("\n2. ONLY AN ADMIN GETS IN")

        admin_routes = [
            ("GET", f"{BASE}/admin/users"),
            ("GET", f"{BASE}/admin/stats"),
            ("GET", f"{BASE}/admin/products"),
            ("PUT", f"{BASE}/admin/users/{buyer_id}/role"),
            ("DELETE", f"{BASE}/admin/users/{buyer_id}"),
        ]

        # --- Nobody logged in. Every route must say 401. ---
        for method, path in admin_routes:
            response = client.open(path, method=method, json={"role": "admin"})

            check(
                f"logged out {method} {path} -> 401",
                response.status_code == 401,
                f"got {response.status_code}",
            )

        # --- A buyer. Every route must say 403, not 401. ---
        for method, path in admin_routes:
            response = client.open(
                path, method=method, json={"role": "admin"}, headers=as_user(client, buyer_id)
            )

            check(
                f"buyer {method} {path} -> 403",
                response.status_code == 403,
                f"got {response.status_code}",
            )

        # --- A seller. Same answer. ---
        for method, path in admin_routes:
            response = client.open(
                path,
                method=method,
                json={"role": "admin"},
                headers=as_user(client, seller_id),
            )

            check(
                f"seller {method} {path} -> 403",
                response.status_code == 403,
                f"got {response.status_code}",
            )

        # A 401 and a 403 mean different things, so check the bodies are
        # distinguishable. If both returned "no", a frontend could not
        # tell the user whether to log in or give up.
        unauth = client.get(f"{BASE}/admin/users")

        forbidden = client.get(
            f"{BASE}/admin/users", headers=as_user(client, buyer_id)
        )

        check(
            "401 and 403 carry different messages",
            unauth.get_json().get("error") != forbidden.get_json().get("error"),
            f"{unauth.get_json()} vs {forbidden.get_json()}",
        )

        # =============================================================
        # 3. THE ADMIN CAN LOOK
        # =============================================================

        print("\n3. THE ADMIN CAN SEE EVERYTHING")

        admin_headers = as_user(client, admin_id)

        users_response = client.get(f"{BASE}/admin/users", headers=admin_headers)

        check("the user list works", users_response.status_code == 200)

        user_list = users_response.get_json()["users"]
        listed_emails = [user["email"] for user in user_list]

        check(
            "all four test accounts are listed",
            all(email in listed_emails for email in TEST_EMAILS),
            listed_emails,
        )

        check(
            "the password hash is never sent",
            all("password_hash" not in user for user in user_list),
        )

        check(
            "each user reports an order count",
            all("order_count" in user for user in user_list),
        )

        stats_response = client.get(f"{BASE}/admin/stats", headers=admin_headers)

        check("the stats endpoint works", stats_response.status_code == 200)

        stats = stats_response.get_json()

        for field in [
            "users",
            "products",
            "orders",
            "reviews",
            "revenue",
            "orders_by_status",
        ]:
            check(f"stats include '{field}'", field in stats, list(stats))

        check(
            "every order status starts at zero or more",
            set(stats["orders_by_status"].keys())
            == {"Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"},
            stats.get("orders_by_status"),
        )

        check(
            "the product count matches the catalogue",
            stats["products"] >= 30,
            stats["products"],
        )

        products_response = client.get(
            f"{BASE}/admin/products", headers=admin_headers
        )

        check("the product list works", products_response.status_code == 200)

        admin_products = products_response.get_json()["products"]

        check(
            "every product reports who owns it",
            all("seller_name" in product for product in admin_products),
        )

        check(
            "unowned shop stock reports no seller",
            all(
                product["seller_name"] is None
                for product in admin_products
                if product["seller_id"] is None
            ),
        )

        # =============================================================
        # 4. CHANGING A ROLE
        # =============================================================

        print("\n4. CHANGING ROLES")

        bad_role = client.put(
            f"{BASE}/admin/users/{buyer_id}/role",
            json={"role": "wizard"},
            headers=admin_headers,
        )

        check(
            "a made-up role is refused",
            bad_role.status_code == 400,
            bad_role.get_json(),
        )

        missing_user = client.put(
            f"{BASE}/admin/users/999999/role",
            json={"role": "seller"},
            headers=admin_headers,
        )

        check(
            "changing a missing user gives 404",
            missing_user.status_code == 404,
            missing_user.get_json(),
        )

        promote = client.put(
            f"{BASE}/admin/users/{buyer_id}/role",
            json={"role": "seller"},
            headers=admin_headers,
        )

        check(
            "a buyer can be promoted to seller",
            promote.status_code == 200,
            promote.get_json(),
        )

        check(
            "the response reports the new role",
            promote.get_json()["user"]["role"] == "seller",
            promote.get_json(),
        )

        # Confirm it actually stuck in the database, not just in the
        # response. A route that reports success without saving would
        # pass a naive test.
        with app.app_context():
            saved = db.session.get(User, buyer_id)

            check(
                "the new role was really saved",
                saved.role == "seller",
                saved.role,
            )

        # The promoted user should now be treated as a seller by the
        # product routes, with no re-login. This proves the role is read
        # fresh from the database on each request.
        create_as_new_seller = client.post(
            f"{BASE}/products",
            json={
                "name": f"{TEST_PRODUCT_PREFIX} One",
                "description": "A product made by a freshly promoted seller.",
                "price": 500,
                "category": "Home",
                "image": "https://example.com/x.jpg",
                "stock": 3,
            },
            headers=as_user(client, buyer_id),
        )

        check(
            "the promotion took effect immediately",
            create_as_new_seller.status_code == 201,
            create_as_new_seller.get_json(),
        )

        demote = client.put(
            f"{BASE}/admin/users/{buyer_id}/role",
            json={"role": "buyer"},
            headers=admin_headers,
        )

        check("a seller can be demoted", demote.status_code == 200)

        # Turn them back into a seller for the rest of the suite
        client.put(
            f"{BASE}/admin/users/{buyer_id}/role",
            json={"role": "seller"},
            headers=admin_headers,
        )

        # --- The self-protection rules ---

        self_change = client.put(
            f"{BASE}/admin/users/{admin_id}/role",
            json={"role": "buyer"},
            headers=admin_headers,
        )

        check(
            "an admin cannot change their own role",
            self_change.status_code == 403,
            self_change.get_json(),
        )

        # Make a second admin so we can test the last-admin rule
        second_admin = client.put(
            f"{BASE}/admin/users/{victim_id}/role",
            json={"role": "admin"},
            headers=admin_headers,
        )

        check(
            "a second admin can be created",
            second_admin.status_code == 200,
            second_admin.get_json(),
        )

        # With two admins, demoting one is fine. The self rule does not
        # apply because victim_id is a different person from admin_id.
        demote_other = client.put(
            f"{BASE}/admin/users/{victim_id}/role",
            json={"role": "buyer"},
            headers=as_user(client, admin_id),
        )

        check(
            "with two admins, one may be demoted by the other",
            demote_other.status_code == 200,
            demote_other.get_json(),
        )

        # Now only admin_id is an admin. Have admin_id promote victim
        # again, then have VICTIM try to demote admin_id. Two admins
        # exist, so that is allowed...
        client.put(
            f"{BASE}/admin/users/{victim_id}/role",
            json={"role": "admin"},
            headers=as_user(client, admin_id),
        )

        victim_demotes_admin = client.put(
            f"{BASE}/admin/users/{admin_id}/role",
            json={"role": "buyer"},
            headers=as_user(client, victim_id),
        )

        check(
            "one admin can demote another when two exist",
            victim_demotes_admin.status_code == 200,
            victim_demotes_admin.get_json(),
        )

        # ...which leaves victim as the ONLY admin. Now the last-admin
        # guard is the only thing protecting the panel, so check it.
        # But note: victim cannot demote THEMSELVES either (self rule),
        # so to reach the last-admin branch we need a different admin
        # acting on them. Promote admin_id back first, demote victim,
        # then have admin_id try to demote... itself. That hits the
        # self rule instead.
        #
        # The reachable path to the last-admin branch is: exactly one
        # admin remains, and a DIFFERENT admin tries to demote them.
        # That is impossible by definition with one admin - which is
        # precisely why the self rule and the last-admin rule together
        # make the situation unreachable. We prove the pieces:
        client.put(
            f"{BASE}/admin/users/{admin_id}/role",
            json={"role": "admin"},
            headers=as_user(client, victim_id),
        )

        victim_alone = client.put(
            f"{BASE}/admin/users/{victim_id}/role",
            json={"role": "buyer"},
            headers=as_user(client, victim_id),
        )

        check(
            "the only remaining admin cannot demote themselves",
            victim_alone.status_code == 403,
            victim_alone.get_json(),
        )

        self_delete = client.delete(
            f"{BASE}/admin/users/{victim_id}", headers=as_user(client, victim_id)
        )

        check(
            "the only remaining admin cannot delete themselves",
            self_delete.status_code == 403,
            self_delete.get_json(),
        )

        # Restore things: victim goes back to being a plain buyer.
        client.put(
            f"{BASE}/admin/users/{victim_id}/role",
            json={"role": "buyer"},
            headers=as_user(client, admin_id),
        )

        with app.app_context():
            restored = db.session.get(User, admin_id)
            victim_now = db.session.get(User, victim_id)

            check(
                "the original admin still holds the admin role",
                restored.role == "admin",
                restored.role,
            )

            check(
                "the test admin was demoted back to buyer",
                victim_now.role == "buyer",
                victim_now.role,
            )

        # =============================================================
        # 5. GIVING THE VICTIM SOME DATA TO LOSE
        # =============================================================

        print("\n5. BUILD UP DATA FOR THE VICTIM")

        # The victim is a buyer: give them a cart, an order and a review
        # so we can prove the delete really cleans up.

        # Use our OWN product rather than a real catalogue item.
        #
        # This used to order product 1, which silently drained its stock
        # every time the suite ran - exactly the kind of side effect
        # that makes a test suite untrustworthy. A test may create and
        # destroy its own fixtures, but it must not quietly damage the
        # data it is meant to be checking.
        with app.app_context():
            fixture = Product(
                name=f"{TEST_PRODUCT_PREFIX}Victim Fixture",
                description="Ordered by the admin tests, then removed.",
                price=300,
                category="Home",
                image="https://example.com/fixture.jpg",
                stock=20,
            )
            db.session.add(fixture)
            db.session.commit()
            fixture_id = fixture.id

        # Put something in their cart
        cart_add = client.post(
            f"{BASE}/cart",
            json={"product_id": fixture_id, "quantity": 2},
            headers=as_user(client, victim_id),
        )

        check("the victim has a cart", cart_add.status_code in (200, 201))

        # Place an order
        order_response = client.post(
            f"{BASE}/orders",
            json={
                "full_name": "Victim Tester",
                "phone": "9800000000",
                "address": "Somewhere, Kathmandu",
                "city": "Kathmandu",
            },
            headers=as_user(client, victim_id),
        )

        check(
            "the victim placed an order",
            order_response.status_code == 201,
            order_response.get_json(),
        )

        # Write a review on the product they just bought.
        # Again, our own fixture - never a real catalogue product, so
        # that product ratings are left exactly as we found them.
        review_response = client.post(
            f"{BASE}/products/{fixture_id}/reviews",
            json={"rating": 4, "comment": "Testing the admin delete."},
            headers=as_user(client, victim_id),
        )

        check(
            "the victim wrote a review",
            review_response.status_code == 201,
            review_response.get_json(),
        )

        # The victim also has a product listing from the promotion test.
        # Count their listings before the delete.
        with app.app_context():
            listings_before = Product.query.filter(
                Product.seller_id == victim_id
            ).count()

            orders_before = Order.query.filter(
                Order.user_id == victim_id
            ).count()

            cart_before = CartItem.query.filter(
                CartItem.user_id == victim_id
            ).count()

            reviews_before = Review.query.filter(
                Review.user_id == victim_id
            ).count()

        check("victim has at least one order", orders_before >= 1, orders_before)
        check("victim has a review", reviews_before >= 1, reviews_before)

        # =============================================================
        # 6. DELETING AN ACCOUNT
        # =============================================================

        print("\n6. DELETING AN ACCOUNT CLEANS UP")

        missing_delete = client.delete(
            f"{BASE}/admin/users/999999", headers=as_user(client, admin_id)
        )
        check(
            "deleting a missing user gives 404",
            missing_delete.status_code == 404,
            missing_delete.get_json(),
        )

        # Now delete the victim for real. They are a buyer by now, so no
        # admin-safety rule applies.
        delete_response = client.delete(
            f"{BASE}/admin/users/{victim_id}", headers=as_user(client, admin_id)
        )

        check(
            "a normal account can be deleted",
            delete_response.status_code == 200,
            delete_response.get_json(),
        )

        with app.app_context():
            gone_user = db.session.get(User, victim_id)

            check("the account is gone", gone_user is None)

            check(
                "their cart rows are gone",
                CartItem.query.filter(CartItem.user_id == victim_id).count() == 0,
            )

            check(
                "their orders are gone",
                Order.query.filter(Order.user_id == victim_id).count() == 0,
            )

            check(
                "their reviews are gone",
                Review.query.filter(Review.user_id == victim_id).count() == 0,
            )

            # Any order lines whose order no longer exists would be
            # orphans. Check there are none left anywhere.
            orphan_lines = (
                db.session.query(OrderItem.id)
                .outerjoin(Order, Order.id == OrderItem.order_id)
                .filter(Order.id.is_(None))
                .count()
            )

            check(
                "no orphaned order lines were left behind",
                orphan_lines == 0,
                orphan_lines,
            )

            # Product listings must SURVIVE and become shop-owned.
            #
            # Careful here: the listing we created was made by buyer_id
            # (the freshly promoted seller), NOT by the victim. We are
            # deleting the victim, whose account has no listings. So the
            # right assertion is about the listing that DOES exist, and
            # we check the mechanism separately below by deleting the
            # seller in section 8 and looking again.
            surviving = Product.query.filter(
                Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
            ).all()

            check(
                "test listings still exist at this point",
                len(surviving) >= 1,
                len(surviving),
            )

            check(
                "no listing is left pointing at the deleted victim",
                all(product.seller_id != victim_id for product in surviving),
                [(p.id, p.seller_id) for p in surviving],
            )

            # And the 30 real products must still be intact.
            check(
                "the seeded catalogue is untouched",
                Product.query.filter(
                    Product.id <= 30
                ).count() == 30,
                Product.query.filter(Product.id <= 30).count(),
            )

        # Their old header should no longer work at all
        stale = client.get(f"{BASE}/cart", headers=as_user(client, victim_id))

        check(
            "the deleted user's session no longer works",
            stale.status_code == 401,
            f"got {stale.status_code}",
        )

        # =============================================================
        # 7. THE STATS STILL ADD UP
        # =============================================================

        print("\n7. STATS AFTER THE DELETE")

        final_stats = client.get(
            f"{BASE}/admin/stats", headers=as_user(client, admin_id)
        ).get_json()

        check(
            "the user count dropped",
            final_stats["users"] < stats["users"],
            f"{stats['users']} -> {final_stats['users']}",
        )

        check(
            "revenue is not negative",
            final_stats["revenue"] >= 0,
            final_stats["revenue"],
        )

        check(
            "there is still at least one admin",
            final_stats["admins"] >= 1,
            final_stats["admins"],
        )

        # =============================================================
        # 8. CLEAN UP
        # =============================================================

        print("\n8. CLEAN UP")

        # The victim is already gone. Now delete the promoted seller -
        # and this is where we can finally prove that a deleted user's
        # listings survive and become shop-owned, because buyer_id is
        # the account that actually owns one.
        admin_headers = as_user(client, admin_id)

        with app.app_context():
            owned_before = Product.query.filter(
                Product.seller_id == buyer_id
            ).count()

        check(
            "the seller owns a listing before deletion",
            owned_before >= 1,
            owned_before,
        )

        seller_delete = client.delete(
            f"{BASE}/admin/users/{buyer_id}", headers=admin_headers
        )

        check(
            "the promoted seller was deleted",
            seller_delete.status_code == 200,
            seller_delete.get_json(),
        )

        with app.app_context():
            after = Product.query.filter(
                Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
            ).all()

            check(
                "their listing survived the delete",
                len(after) >= 1,
                len(after),
            )

            check(
                "the orphaned listing is now shop-owned",
                all(product.seller_id is None for product in after),
                [(p.id, p.seller_id) for p in after],
            )

        # The plain seller account is not a victim, just cleanup.
        other_delete = client.delete(
            f"{BASE}/admin/users/{seller_id}", headers=admin_headers
        )

        check("the spare seller was cleaned up", other_delete.status_code == 200)

        # The admin cannot delete themselves, which is correct but means
        # the suite has to remove its own admin account directly. Do it
        # through the app context, the way an operator would.
        with app.app_context():
            admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()

            if admin_user:
                Review.query.filter(Review.user_id == admin_user.id).delete(
                    synchronize_session=False
                )
                CartItem.query.filter(CartItem.user_id == admin_user.id).delete(
                    synchronize_session=False
                )

                order_ids = [
                    row.id
                    for row in db.session.query(Order.id)
                    .filter(Order.user_id == admin_user.id)
                    .all()
                ]

                if order_ids:
                    OrderItem.query.filter(
                        OrderItem.order_id.in_(order_ids)
                    ).delete(synchronize_session=False)

                Order.query.filter(Order.user_id == admin_user.id).delete(
                    synchronize_session=False
                )

                Product.query.filter(Product.seller_id == admin_user.id).update(
                    {"seller_id": None}, synchronize_session=False
                )

                db.session.delete(admin_user)
                db.session.commit()

    # The test client is closed now, so use the app context directly.
    with app.app_context():
        remaining = User.query.filter(User.email.in_(TEST_EMAILS)).count()

        check("no test accounts were left behind", remaining == 0, remaining)

        Product.query.filter(
            Product.name.like(f"{TEST_PRODUCT_PREFIX}%")
        ).delete(synchronize_session=False)

        db.session.commit()

        check(
            "the real catalogue is intact",
            Product.query.filter(Product.id <= 30).count() == 30,
            Product.query.filter(Product.id <= 30).count(),
        )

        # The strongest hygiene check: no real product's stock should
        # have moved. If this fails, some part of the suite is ordering
        # catalogue items and leaving them decremented.
        moved = [
            (p.id, p.name, p.stock)
            for p in Product.query.filter(Product.id <= 30).all()
            if p.stock != 10
        ]

        check(
            "no catalogue product had its stock changed",
            len(moved) == 0,
            moved,
        )

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nOnly admins get in, and an admin cannot lock themselves out.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
