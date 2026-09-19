"""
A live walkthrough of the admin panel, over real HTTP.

The test suite (test_admin.py) uses Flask's built-in test client, which
never opens a socket. This script is different: it talks to the server
that is actually running on localhost:5000, on the same routes the
React app calls. That makes it the right thing to demo in a viva,
because it shows the whole stack working rather than one layer.

Start the backend first:

    cd backend
    ./venv/Scripts/python.exe app.py

Then in another terminal:

    cd backend
    ./venv/Scripts/python.exe live_demo_admin.py

The script creates its own accounts, exercises the panel, and deletes
everything it made before it finishes.
"""

import json
import urllib.error
import urllib.request

# ---------------------------------------------------------------------
# TWO WINDOWS-ONLY GOTCHAS BAKED INTO THIS SCRIPT
# ---------------------------------------------------------------------
#
# 1. PROXY BYPASS
#
#    On a machine with an HTTP proxy configured (corporate network, a
#    VPN, or a dev tool running one on a local port), Python's urllib
#    routes even a localhost request through that proxy. The proxy then
#    answers with its own 404 page and the script looks like the
#    backend is broken. So we build an opener that never consults a
#    proxy and call it directly - installing it globally is not
#    reliable enough, because some environments still inject one.
#
# 2. 127.0.0.1, NOT localhost
#
#    "localhost" can resolve to IPv6 ::1 first. If anything else is
#    listening on [::1]:5000 - and on this machine something is - the
#    request lands there instead of on Flask, and you get a
#    mysterious 404 from a server you did not write. Flask's dev server
#    binds 127.0.0.1, so we address exactly that.
#
# Both of these cost real debugging time. Being explicit avoids them
# entirely.
# ---------------------------------------------------------------------

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

HOST = "http://127.0.0.1:5000"
BASE = f"{HOST}/api"

ADMIN = {
    "name": "Demo Admin",
    "email": "demo.admin@smartcart.test",
    "password": "demoadmin123",
    "role": "admin",
}

SELLER = {
    "name": "Demo Seller",
    "email": "demo.seller@smartcart.test",
    "password": "demoseller123",
    "role": "seller",
}

BUYER = {
    "name": "Demo Buyer",
    "email": "demo.buyer@smartcart.test",
    "password": "demobuyer123",
    "role": "buyer",
}


def call(method, path, body=None, user_id=None, root=False):
    """Make a request and return (status_code, parsed_json).

    `path` is relative to /api unless root=True, which is used for the
    health check at "/". (Getting that wrong is an easy way to spend
    ten minutes staring at a 404 that is entirely your own fault.)

    Not every answer is JSON. If the backend is down, something in
    front of it (a proxy, or the OS) may return an HTML error page.
    Blindly calling json.loads on that gives a confusing
    "Expecting value: line 1 column 1" traceback that tells you
    nothing about the real problem. So we check the content type and
    fall back to a plain string.
    """

    url = f"{HOST}{path}" if root else f"{BASE}{path}"

    data = json.dumps(body).encode("utf-8") if body is not None else None

    request = urllib.request.Request(url, data=data, method=method)

    request.add_header("Content-Type", "application/json")

    if user_id is not None:
        # This is the whole trick behind SmartCart's login: the client
        # sends the user id, the server looks up the role itself.
        request.add_header("X-User-Id", str(user_id))

    def parse(response):
        raw = response.read().decode("utf-8", errors="replace")

        if not raw.strip():
            return {}

        content_type = response.headers.get("Content-Type", "")

        if "json" not in content_type:
            return {"error": f"non-JSON response: {raw[:160]}"}

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": f"unreadable JSON: {raw[:160]}"}

    try:
        with OPENER.open(request, timeout=10) as response:
            return response.status, parse(response)

    except urllib.error.HTTPError as error:
        return error.code, parse(error)

    except urllib.error.URLError as error:
        # Genuinely could not reach the server at all.
        return 0, {"error": f"could not reach the server: {error.reason}"}


def line(title):
    print("\n" + "=" * 62)
    print(title)
    print("=" * 62)


def show(label, value):
    print(f"  {label:<46} {value}")


def main():
    line("STEP 0 - IS THE SERVER UP?")

    status, body = call("GET", "/", root=True)

    show("GET /", status)

    if status != 200:
        print(f"\n  The backend is not answering properly ({status}).")
        print(f"  Detail: {body.get('error', 'unknown')}")
        print("\n  Start it in another terminal with:")
        print("    cd backend && ./venv/Scripts/python.exe app.py")
        return

    # -----------------------------------------------------------------
    line("STEP 1 - CREATE THE ACCOUNTS WE WILL USE")

    accounts = {}

    for key, person in [("admin", ADMIN), ("seller", SELLER), ("buyer", BUYER)]:
        status, body = call("POST", "/register", person)

        # 409 means a previous run left the account behind. Log in
        # instead so the script is re-runnable.
        if status == 409:
            status, body = call(
                "POST",
                "/login",
                {"email": person["email"], "password": person["password"]},
            )
            show(f"{person['name']} (already existed)", f"{status} - logged in")
        else:
            show(f"{person['name']} created", status)

        accounts[key] = body["user"]["id"]

    admin_id = accounts["admin"]
    seller_id = accounts["seller"]
    buyer_id = accounts["buyer"]

    # -----------------------------------------------------------------
    line("STEP 2 - A BUYER TRIES TO OPEN THE ADMIN PANEL")

    for method, path in [
        ("GET", "/admin/users"),
        ("GET", "/admin/stats"),
        ("GET", "/admin/products"),
    ]:
        status, body = call(method, path, user_id=buyer_id)

        show(f"buyer {method} {path}", f"{status} - {body.get('error', '')}")

    print("\n  The buyer is refused. That is the backend doing the")
    print("  checking, not the React app.")

    # -----------------------------------------------------------------
    line("STEP 3 - THE ADMIN LOOKS AROUND")

    status, body = call("GET", "/admin/stats", user_id=admin_id)

    show("GET /admin/stats", status)

    if status == 200:
        for key in [
            "users",
            "sellers",
            "admins",
            "products",
            "out_of_stock",
            "orders",
            "reviews",
            "revenue",
        ]:
            show(f"  {key}", body.get(key))

        show("  orders_by_status", body.get("orders_by_status"))

    status, body = call("GET", "/admin/users", user_id=admin_id)

    show("GET /admin/users", f"{status} - {body.get('count')} account(s)")

    for user in body.get("users", [])[:6]:
        show(
            f"  #{user['id']} {user['name']}",
            f"{user['role']}, {user['order_count']} order(s)",
        )

    status, body = call("GET", "/admin/products", user_id=admin_id)

    show("GET /admin/products", f"{status} - {body.get('count')} product(s)")

    # Show a couple that a seller owns, to prove seller_name is real
    owned = [p for p in body.get("products", []) if p.get("seller_name")]

    if owned:
        for product in owned[:3]:
            show(f"  {product['name'][:34]}", f"owner: {product['seller_name']}")
    else:
        print("  (no seller-owned products in the catalogue right now)")

    # -----------------------------------------------------------------
    line("STEP 4 - CHANGE SOMEBODY'S ROLE")

    status, body = call(
        "PUT",
        f"/admin/users/{buyer_id}/role",
        {"role": "seller"},
        user_id=admin_id,
    )

    show("promote the buyer to seller", f"{status} - {body.get('message', body.get('error'))}")

    # Prove the promotion is live immediately - no re-login.
    status, body = call(
        "POST",
        "/products",
        {
            "name": "Demo Admin Walkthrough Item",
            "description": "A listing created to prove the role changed.",
            "price": 999,
            "category": "Home",
            "image": "https://example.com/demo.jpg",
            "stock": 2,
        },
        user_id=buyer_id,
    )

    show("the same user now lists a product", f"{status} - {body.get('message', body.get('error'))}")

    new_product_id = body.get("product", {}).get("id") if status == 201 else None

    status, body = call(
        "PUT",
        f"/admin/users/{buyer_id}/role",
        {"role": "buyer"},
        user_id=admin_id,
    )

    show("demote them back to buyer", f"{status} - {body.get('message', body.get('error'))}")

    # -----------------------------------------------------------------
    line("STEP 5 - THE RULES THAT STOP AN ADMIN LOCKING EVERYONE OUT")

    status, body = call(
        "PUT",
        f"/admin/users/{admin_id}/role",
        {"role": "buyer"},
        user_id=admin_id,
    )

    show("an admin changes their OWN role", f"{status} - {body.get('error')}")

    status, body = call("DELETE", f"/admin/users/{admin_id}", user_id=admin_id)

    show("an admin deletes their OWN account", f"{status} - {body.get('error')}")

    status, body = call(
        "PUT",
        f"/admin/users/{admin_id}/role",
        {"role": "wizard"},
        user_id=admin_id,
    )

    show("an invented role name", f"{status} - {body.get('error')}")

    # -----------------------------------------------------------------
    line("STEP 6 - DELETE AN ACCOUNT AND WATCH IT CLEAN UP")

    # Give the account something to lose: a cart, an order and a review.
    call("POST", "/cart", {"product_id": 1, "quantity": 1}, user_id=seller_id)

    status, _ = call(
        "POST",
        "/orders",
        {
            "full_name": "Demo Seller",
            "phone": "9800000000",
            "address": "Demo Street, Kathmandu",
            "city": "Kathmandu",
        },
        user_id=seller_id,
    )

    show("the seller placed an order", status)

    status, _ = call(
        "POST",
        "/products/1/reviews",
        {"rating": 5, "comment": "Written so the delete has something to remove."},
        user_id=seller_id,
    )

    show("the seller wrote a review", status)

    status, body = call("DELETE", f"/admin/users/{seller_id}", user_id=admin_id)

    show("admin deletes the seller", f"{status} - {body.get('message', body.get('error'))}")

    # Their session must be dead
    status, body = call("GET", "/cart", user_id=seller_id)

    show("the deleted user's old session", f"{status} - {body.get('error')}")

    # -----------------------------------------------------------------
    line("STEP 7 - CLEAN UP")

    if new_product_id:
        status, body = call(
            "DELETE", f"/products/{new_product_id}", user_id=admin_id
        )

        show("removed the walkthrough product", status)

    status, body = call("DELETE", f"/admin/users/{buyer_id}", user_id=admin_id)

    show("removed the demo buyer", status)

    status, body = call("GET", "/products")

    show("products still in the shop", len(body))

    print("\n  The admin account is left in place on purpose - the")
    print("  backend refuses to let an admin delete themselves. Remove")
    print("  it by hand if you want a completely clean database.")

    print("\n" + "=" * 62)
    print("WALKTHROUGH COMPLETE")
    print("=" * 62)
    print("\nEvery check above ran over real HTTP against the server.")
    print("Open http://localhost:5173/admin in the browser to see the")
    print("same thing as a page.")


if __name__ == "__main__":
    main()
