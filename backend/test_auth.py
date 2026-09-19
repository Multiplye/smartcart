"""
SmartCart - Auth Test Script
============================

Tests the register and login endpoints to make sure they behave correctly
BEFORE we connect the React form to them.

HOW TO RUN (from the backend folder, venv activated):

    python test_auth.py

The script uses Flask's built-in test client, so it does NOT need the
server to be running. It talks to the app directly.

It cleans up after itself - the test accounts it creates are deleted
at the end, so your database stays tidy.
"""

from app import app, db, User

# The test accounts we will create
TEST_EMAIL = "testuser@smartcart.local"
TEST_PASSWORD = "secret123"

passed = 0
failed = 0


def check(label, condition, detail=""):
    """Print PASS or FAIL for one check."""
    global passed, failed

    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}")
        if detail:
            print(f"         -> {detail}")


def main():
    global passed, failed

    print("=" * 62)
    print("SmartCart - Auth Tests")
    print("=" * 62)

    client = app.test_client()

    # ---------------------------------------------------------------
    # Clean slate: remove any leftover test account from a previous run
    # ---------------------------------------------------------------
    with app.app_context():
        leftover = User.query.filter_by(email=TEST_EMAIL).first()
        if leftover:
            db.session.delete(leftover)
            db.session.commit()
            print("\n(Removed a leftover test account from a previous run)")

    # ---------------------------------------------------------------
    # 1. REGISTER
    # ---------------------------------------------------------------
    print("\n1. REGISTER")

    r = client.post("/api/register", json={
        "name": "Test User",
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "role": "buyer",
    })
    check("register returns 201", r.status_code == 201, f"got {r.status_code}")

    body = r.get_json()
    user = body.get("user", {})
    check("response contains the new user", "user" in body)
    check("user has an id", bool(user.get("id")))
    check("name is correct", user.get("name") == "Test User")
    check("email is lowercased", user.get("email") == TEST_EMAIL)
    check("role is buyer", user.get("role") == "buyer")
    check("password_hash is NOT returned", "password_hash" not in user,
          f"response keys = {list(user.keys())}")

    # ---------------------------------------------------------------
    # 2. REGISTER - duplicate email must be rejected
    # ---------------------------------------------------------------
    print("\n2. REGISTER with the same email again")

    r = client.post("/api/register", json={
        "name": "Impostor",
        "email": TEST_EMAIL,
        "password": "another123",
        "role": "buyer",
    })
    check("duplicate email returns 409", r.status_code == 409, f"got {r.status_code}")
    check("error message explains why",
          "already exists" in r.get_json().get("error", "").lower())

    # ---------------------------------------------------------------
    # 3. REGISTER - validation rules
    # ---------------------------------------------------------------
    print("\n3. REGISTER validation")

    r = client.post("/api/register", json={
        "name": "", "email": "x@y.com", "password": "secret123"
    })
    check("missing name returns 400", r.status_code == 400, f"got {r.status_code}")

    r = client.post("/api/register", json={
        "name": "Shorty", "email": "shorty@smartcart.local", "password": "123"
    })
    check("short password returns 400", r.status_code == 400, f"got {r.status_code}")
    check("message mentions 6 characters",
          "6 characters" in r.get_json().get("error", ""))

    r = client.post("/api/register", json={
        "name": "Hacker", "email": "hacker@smartcart.local",
        "password": "secret123", "role": "admin"
    })
    check("self-assigned admin role is ALLOWED (documented)",
          r.status_code == 201, f"got {r.status_code}")
    print("         NOTE: role comes from the form, so anyone can pick 'admin'.")
    print("         We will lock this down when we build the admin panel.")

    r = client.post("/api/register", json={
        "name": "Bogus", "email": "bogus@smartcart.local",
        "password": "secret123", "role": "supervillain"
    })
    check("invalid role returns 400", r.status_code == 400, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 4. LOGIN - correct credentials
    # ---------------------------------------------------------------
    print("\n4. LOGIN with correct password")

    r = client.post("/api/login", json={
        "email": TEST_EMAIL, "password": TEST_PASSWORD
    })
    check("login returns 200", r.status_code == 200, f"got {r.status_code}")

    body = r.get_json()
    check("welcome message greets the user",
          "Test User" in body.get("message", ""))
    check("user object returned", body.get("user", {}).get("name") == "Test User")
    check("password_hash not leaked",
          "password_hash" not in body.get("user", {}))

    # ---------------------------------------------------------------
    # 5. LOGIN - wrong password
    # ---------------------------------------------------------------
    print("\n5. LOGIN with wrong password")

    r = client.post("/api/login", json={
        "email": TEST_EMAIL, "password": "totallywrong"
    })
    check("wrong password returns 401", r.status_code == 401, f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 6. LOGIN - unknown email gives the SAME message
    # ---------------------------------------------------------------
    print("\n6. LOGIN with an email that has no account")

    r = client.post("/api/login", json={
        "email": "nobody@nowhere.local", "password": "secret123"
    })
    check("unknown email returns 401", r.status_code == 401, f"got {r.status_code}")
    check("message is identical to the wrong-password case",
          r.get_json().get("error") == "Incorrect email or password.")

    # ---------------------------------------------------------------
    # 7. LOGIN - email is case-insensitive
    # ---------------------------------------------------------------
    print("\n7. LOGIN with UPPERCASE email")

    r = client.post("/api/login", json={
        "email": TEST_EMAIL.upper(), "password": TEST_PASSWORD
    })
    check("uppercase email still logs in", r.status_code == 200,
          f"got {r.status_code}")

    # ---------------------------------------------------------------
    # 8. PASSWORD IS REALLY HASHED IN THE DATABASE
    # ---------------------------------------------------------------
    print("\n8. Password storage")

    with app.app_context():
        stored = User.query.filter_by(email=TEST_EMAIL).first()
        check("a hash is stored, not the raw password",
              stored.password_hash != TEST_PASSWORD)
        check("stored value looks like a hash",
              stored.password_hash.startswith("scrypt:") or
              stored.password_hash.startswith("pbkdf2:"))

    # ---------------------------------------------------------------
    # 9. CLEAN UP
    # ---------------------------------------------------------------
    print("\n9. Clean up test accounts")

    with app.app_context():
        removed = 0
        for email in (TEST_EMAIL, "shorty@smartcart.local",
                      "hacker@smartcart.local", "bogus@smartcart.local"):
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
                removed += 1
        db.session.commit()
        print(f"  Removed {removed} test account(s).")
        print(f"  Users remaining in database: {User.query.count()}")

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 62)

    if failed == 0:
        print("\nAll auth tests passed. Safe to connect the React form.")
    else:
        print("\nSome tests failed - review the output above.")


if __name__ == "__main__":
    main()
