from functools import wraps

from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask application
app = Flask(__name__)

# Allow requests from React frontend
CORS(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///smartcart.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create database object
db = SQLAlchemy(app)

# The three user roles in SmartCart
ROLES = ["buyer", "seller", "admin"]


# =========================
# Product Model
# =========================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(500), nullable=True)
    stock = db.Column(db.Integer, default=0)

    # WHO OWNS THIS LISTING.
    #
    # This is a "foreign key": the number stored here must match the id
    # of a row in the user table. That is what lets us say "seller 7 owns
    # this product" and then refuse to let seller 9 edit it.
    #
    # nullable=True is deliberate. The 30 products we imported from
    # products.js have no owner - they were seeded by us, not by a
    # seller. They behave like "shop-owned" stock that only an admin
    # may edit. If we made this nullable=False we could not have added
    # the column to a table that already had rows in it.
    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )


# =========================
# User Model
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Full name the user typed when registering
    name = db.Column(db.String(150), nullable=False)

    # Login email. unique=True stops two accounts sharing an email.
    email = db.Column(db.String(200), unique=True, nullable=False)

    # IMPORTANT: we never store the real password, only a hash of it.
    # The hash is a one-way scramble - you cannot turn it back into the
    # password, so even if someone reads the database they cannot log in.
    password_hash = db.Column(db.String(300), nullable=False)

    # "buyer", "seller" or "admin"
    role = db.Column(db.String(20), nullable=False, default="buyer")

    def set_password(self, plain_password):
        """Scramble and store the password."""
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        """Return True if the typed password matches the stored hash."""
        return check_password_hash(self.password_hash, plain_password)


# =========================
# Home Route
# =========================

@app.route("/")
def home():
    return {
        "message": "SmartCart Backend is running!"
    }


# =========================
# HELPER: Product -> dictionary
# =========================

def product_to_dict(product):
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "image": product.image,
        "stock": product.stock,
        "seller_id": product.seller_id,
    }


def user_to_dict(user):
    """Convert a User into safe JSON.

    Notice we deliberately leave out password_hash - that value must never
    travel to the browser.
    """
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


# =========================
# ROLE PROTECTION
# =========================
#
# How this works:
#
#   1. The React app remembers which user is logged in.
#   2. When it calls a protected route, it sends that user's id in a
#      request header called "X-User-Id".
#   3. The decorator below looks the id up in the database and checks
#      the user's role before letting the request through.
#
# Why look the user up in the database instead of trusting the header?
# Because the header only carries an id, not a role. Even if someone
# edits the header to claim a different id, the role still comes from
# the database - so a buyer cannot pretend to be a seller.
#
# NOTE for the report: this is a simplified approach suitable for a
# coursework project. A production system would send a signed token
# (e.g. JWT) instead, so the identity could not be guessed at all.

def get_current_user():
    """Read the X-User-Id header and return the matching User, or None."""
    raw_id = request.headers.get("X-User-Id")

    if not raw_id:
        return None

    try:
        user_id = int(raw_id)
    except (TypeError, ValueError):
        # Header was not a number - treat as "not logged in"
        return None

    return db.session.get(User, user_id)


def roles_required(*allowed_roles):
    """Decorator: only let through users whose role is in allowed_roles.

    Usage:
        @app.route("/api/products", methods=["POST"])
        @roles_required("seller", "admin")
        def create_product():
            ...

    Returns:
        401 if nobody is logged in
        403 if logged in but the role is not allowed
    """

    def decorator(view_function):

        @wraps(view_function)
        def wrapper(*args, **kwargs):

            user = get_current_user()

            if user is None:
                return {
                    "error": "You must be logged in to do that."
                }, 401

            if user.role not in allowed_roles:
                return {
                    "error": (
                        f"Your account is a '{user.role}' account. "
                        f"This action needs one of: {', '.join(allowed_roles)}."
                    )
                }, 403

            # Handy for the view function: it can read who made the request
            request.current_user = user

            return view_function(*args, **kwargs)

        return wrapper

    return decorator


def can_manage_product(user, product):
    """Decide whether this user is allowed to edit or delete this product.

    The rule, in plain English:

        - An admin can manage ANY product, including the 30 seeded ones.
        - A seller can manage only the products THEY created.
        - Products with seller_id = None (the seeded ones) belong to the
          shop, so only an admin can touch them.
        - A buyer can never manage anything.

    Returns (allowed, error_message, status_code).
    """

    if user.role == "admin":
        return True, None, None

    if product.seller_id is None:
        return False, (
            "This product belongs to the shop, not to a seller account. "
            "Only an admin can change it."
        ), 403

    if product.seller_id != user.id:
        return False, (
            "This product belongs to a different seller, so you cannot "
            "change it."
        ), 403

    return True, None, None


# =========================
# PRODUCTS - READ (public)
# =========================

@app.route("/api/products", methods=["GET"])
def get_products():
    """List products. Optional ?category= and ?search= filters."""

    query = Product.query

    # Filter by category, e.g. /api/products?category=Electronics
    category = request.args.get("category")
    if category:
        query = query.filter(
            Product.category.ilike(category.strip())
        )

    # Search across name and description, e.g. /api/products?search=watch
    search = request.args.get("search")
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            Product.name.ilike(term) | Product.description.ilike(term)
        )

    products = query.all()

    return [product_to_dict(product) for product in products]


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_single_product(product_id):
    """Return one product, or 404 if it does not exist."""

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    return product_to_dict(product)


# =========================
# PRODUCTS - CREATE (seller / admin)
# =========================

def read_product_payload(data, existing=None):
    """Validate incoming product data.

    Returns (values, error_message).

    `existing` is the Product being updated, if any. When updating we
    allow the caller to send only the fields they want to change - any
    field they leave out keeps its current value.
    """

    def current(field, default=None):
        """Value from the request, falling back to the existing product."""
        if field in data:
            return data[field]
        if existing is not None:
            return getattr(existing, field)
        return default

    name = (current("name") or "").strip()
    description = (current("description") or "").strip()
    category = (current("category") or "").strip()
    image = current("image")
    price = current("price")
    stock = current("stock", 0)

    # --- Required text fields ---
    if not name:
        return None, "Product name is required."

    if not description:
        return None, "Product description is required."

    if not category:
        return None, "Product category is required."

    # --- Price must be a number and cannot be negative ---
    try:
        price = float(price)
    except (TypeError, ValueError):
        return None, "Price must be a number."

    if price < 0:
        return None, "Price cannot be negative."

    # --- Stock must be a whole number and cannot be negative ---
    try:
        stock = int(stock)
    except (TypeError, ValueError):
        return None, "Stock must be a whole number."

    if stock < 0:
        return None, "Stock cannot be negative."

    values = {
        "name": name,
        "description": description,
        "price": price,
        "category": category,
        "image": image,
        "stock": stock,
    }

    return values, None


@app.route("/api/products", methods=["POST"])
@roles_required("seller", "admin")
def create_product():
    """Add a new product. Sellers and admins only."""

    data = request.get_json(silent=True)

    if not data:
        return {"error": "No product data was sent."}, 400

    values, error = read_product_payload(data)

    if error:
        return {"error": error}, 400

    product = Product(**values)

    # Stamp the product with the person who created it. We take the id
    # from the logged-in user rather than from the request body, so a
    # seller cannot create a listing owned by somebody else.
    product.seller_id = request.current_user.id

    db.session.add(product)
    db.session.commit()

    return {
        "message": "Product created successfully!",
        "product": product_to_dict(product)
    }, 201


# =========================
# PRODUCTS - UPDATE (seller / admin)
# =========================

@app.route("/api/products/<int:product_id>", methods=["PUT"])
@roles_required("seller", "admin")
def update_product(product_id):
    """Edit a product. Sellers and admins only.

    The caller may send only the fields they want to change.
    """

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    # Ownership check comes BEFORE we read the body, so a seller who does
    # not own this product learns nothing about what a valid edit looks
    # like.
    allowed, error, status = can_manage_product(request.current_user, product)

    if not allowed:
        return {"error": error}, status

    data = request.get_json(silent=True)

    if not data:
        return {"error": "No product data was sent."}, 400

    values, error = read_product_payload(data, existing=product)

    if error:
        return {"error": error}, 400

    for field, value in values.items():
        setattr(product, field, value)

    db.session.commit()

    return {
        "message": "Product updated successfully!",
        "product": product_to_dict(product)
    }, 200


# =========================
# PRODUCTS - DELETE (seller / admin)
# =========================

@app.route("/api/products/<int:product_id>", methods=["DELETE"])
@roles_required("seller", "admin")
def delete_product(product_id):
    """Remove a product. Sellers and admins only."""

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    allowed, error, status = can_manage_product(request.current_user, product)

    if not allowed:
        return {"error": error}, status

    name = product.name

    db.session.delete(product)
    db.session.commit()

    return {
        "message": f"'{name}' was deleted.",
        "deleted_id": product_id
    }, 200


# =========================
# REGISTER
# =========================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    # --- 1. Make sure every field we need was sent ---
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "buyer").strip().lower()

    if not name or not email or not password:
        return {"error": "Name, email and password are all required."}, 400

    # --- 2. Basic password rule ---
    if len(password) < 6:
        return {"error": "Password must be at least 6 characters."}, 400

    # --- 3. Role must be one of the allowed values ---
    # Without this check someone could POST role="admin" and grant
    # themselves an admin account.
    if role not in ROLES:
        return {"error": f"Role must be one of: {', '.join(ROLES)}."}, 400

    # --- 4. Email must not already be taken ---
    existing = User.query.filter_by(email=email).first()
    if existing:
        return {"error": "An account with that email already exists."}, 409

    # --- 5. Create the user and hash the password ---
    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {
        "message": "Account created successfully!",
        "user": user_to_dict(user)
    }, 201


# =========================
# LOGIN
# =========================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return {"error": "Email and password are required."}, 400

    user = User.query.filter_by(email=email).first()

    # Same message whether the email is unknown or the password is wrong.
    # This avoids telling an attacker which emails have accounts.
    if user is None or not user.check_password(password):
        return {"error": "Incorrect email or password."}, 401

    return {
        "message": f"Welcome back, {user.name}!",
        "user": user_to_dict(user)
    }, 200


# =========================
# CREATE DATABASE TABLES
# =========================

with app.app_context():
    db.create_all()


# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)