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
# CartItem Model
# =========================
#
# One row = "this user wants N of this product".
#
# Note what is NOT stored here: the price. Only the product id and the
# quantity. That is deliberate, because a product's price can change.
# If we copied the price into the cart, a shopper could add an item at
# Rs. 100, wait for the seller to raise it to Rs. 200, and then check
# out at the old price. By storing just the id, the price is always
# looked up fresh from the product table.

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    # A user should never end up with two separate rows for the same
    # product. This constraint makes the database itself refuse that,
    # not just our application code.
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="one_row_per_user_product"),
    )


# =========================
# Order Model
# =========================
#
# One row = one placed order.
#
# Notice we record the delivery details on the ORDER, not on the user.
# That is deliberate: a shopper may want one order delivered to their
# home and the next to their office. If we stored the address on the
# user, placing the second order would silently rewrite the first one's
# delivery address - a genuine bug in a lot of student projects.
#
# The status column drives the whole fulfilment flow:
#
#   Pending -> Confirmed -> Shipped -> Delivered
#                \\
#                 -> Cancelled

ORDER_STATUSES = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Who placed it. Every order belongs to exactly one user.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # --- Delivery details, copied at the moment of ordering ---
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(400), nullable=False)
    city = db.Column(db.String(100), nullable=False)

    # --- Payment. Cash on delivery only, per the project scope. ---
    payment_method = db.Column(db.String(40), nullable=False, default="Cash on Delivery")

    # --- Money ---
    #
    # total is a snapshot of what the shopper owed at checkout. We keep
    # it even though it is the sum of the items, because prices change
    # later - and an order is a record of what was agreed, not a live
    # calculation. If a seller raises a price tomorrow, yesterday's
    # order must still show yesterday's price.
    total = db.Column(db.Float, nullable=False, default=0)

    status = db.Column(db.String(20), nullable=False, default="Pending")

    # When the order was placed
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class OrderItem(db.Model):
    """One line of an order: "N of product X, at this price".

    This is the important table. It copies the product's NAME and PRICE
    at the time of the order. That way:
      - if the seller later edits or deletes the product, the order
        still shows what the shopper actually bought;
      - the order total never drifts.
    """

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
        nullable=False
    )

    # Kept so we can link back to the product page, but NOT relied on
    # for the display - the product might be gone.
    product_id = db.Column(db.Integer, nullable=True)

    # The values copied at purchase time
    product_name = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    @property
    def subtotal(self):
        return round(self.unit_price * self.quantity, 2)


# =========================
# Review Model
# =========================
#
# One row = one person's star rating and comment about one product.
#
# Two rules worth noting:
#
#   1. A UNIQUE constraint on (user_id, product_id) means you cannot
#      review the same product twice. Without it, one enthusiastic
#      shopper could post fifty 5-star reviews and drag the average up.
#
#   2. You may only review a product you have actually ORDERED. That
#      check happens in the route, not here, because it needs to look at
#      the order history.

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    # 1 to 5 stars
    rating = db.Column(db.Integer, nullable=False)

    comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="one_review_per_user_product"),
    )





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

def product_to_dict(product, rating=None):
    """Convert a Product to JSON.

    `rating` is worked out separately and passed in, because averaging
    ratings needs a database query and we do not want one query per
    product. The caller looks them all up in a single grouped query and
    hands each product its own summary.
    """
    body = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "image": product.image,
        "stock": product.stock,
        "seller_id": product.seller_id,
    }

    if rating is not None:
        body["rating_average"] = rating["average"]
        body["rating_count"] = rating["count"]

    return body


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

    # One grouped query for all the ratings, rather than one per product
    ratings = rating_summary_for([product.id for product in products])

    # Every product gets both rating fields, even when it has no reviews
    # at all. Missing keys would force the frontend to guard against
    # `undefined` on some products and a number on others - an easy
    # source of bugs. A consistent shape is worth the extra default.
    empty = {"average": 0.0, "count": 0}

    return [
        product_to_dict(product, ratings.get(product.id, empty))
        for product in products
    ]


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_single_product(product_id):
    """Return one product, or 404 if it does not exist."""

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    return product_to_dict(product, rating_for(product_id))


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
# CART (logged-in users)
# =========================
#
# The cart lives in the database, keyed by the logged-in user. That is
# what makes it survive a page refresh, a browser restart, or switching
# to a different device.
#
# Every route below is scoped to request.current_user, so there is no
# way to read or change somebody else's cart.

def cart_item_to_dict(item):
    """Turn a CartItem into JSON, joining in the product details.

    The frontend needs the name, price and image to draw the cart, and
    those live on the product - so we look it up here rather than making
    the browser fire one request per item.
    """
    product = db.session.get(Product, item.product_id)

    # Defensive: if a product was deleted while it sat in someone's
    # cart, skip it rather than crashing.
    if product is None:
        return None

    return {
        "product_id": product.id,
        "quantity": item.quantity,
        "name": product.name,
        "price": product.price,
        "image": product.image,
        "category": product.category,
        "stock": product.stock,
        "subtotal": round(product.price * item.quantity, 2),
    }


def read_cart():
    """Return the current user's cart as a list of dictionaries."""
    items = CartItem.query.filter_by(user_id=request.current_user.id).all()

    result = []

    for item in items:
        as_dict = cart_item_to_dict(item)

        if as_dict is not None:
            result.append(as_dict)

    return result


def cart_response(message=None, status=200):
    """Build a consistent cart reply for every cart route.

    Every route returns the same three things - a message plus the full
    recalculated cart - so the frontend can simply replace its state
    with whatever came back, instead of guessing what changed.
    """
    items = read_cart()

    body = {
        "items": items,
        "count": sum(item["quantity"] for item in items),
        "total": round(sum(item["subtotal"] for item in items), 2),
    }

    if message:
        body["message"] = message

    return body, status


@app.route("/api/cart", methods=["GET"])
@roles_required("buyer", "seller", "admin")
def get_cart():
    """Return the logged-in user's cart."""

    return cart_response()


@app.route("/api/cart", methods=["POST"])
@roles_required("buyer", "seller", "admin")
def add_to_cart():
    """Add a product to the cart, or increase its quantity.

    Body: { "product_id": 3, "quantity": 1 }
    """

    data = request.get_json(silent=True) or {}

    # --- 1. Which product? ---
    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return {"error": "A valid product_id is required."}, 400

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    # --- 2. How many? Defaults to 1 if not sent. ---
    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return {"error": "Quantity must be a whole number."}, 400

    if quantity < 1:
        return {"error": "Quantity must be at least 1."}, 400

    # --- 3. Already in the cart? Add to it instead of adding a row. ---
    existing = CartItem.query.filter_by(
        user_id=request.current_user.id,
        product_id=product_id
    ).first()

    if existing:
        existing.quantity += quantity

        # Never let the cart ask for more than the shop has
        if existing.quantity > product.stock:
            existing.quantity = product.stock

        message = f"'{product.name}' quantity updated."
    else:
        # A product with 0 stock cannot be added at all
        if product.stock < 1:
            return {"error": f"'{product.name}' is out of stock."}, 400

        existing = CartItem(
            user_id=request.current_user.id,
            product_id=product_id,
            quantity=min(quantity, product.stock)
        )

        db.session.add(existing)
        message = f"'{product.name}' added to your cart."

    db.session.commit()

    return cart_response(message, 201)


@app.route("/api/cart/<int:product_id>", methods=["PUT"])
@roles_required("buyer", "seller", "admin")
def update_cart_item(product_id):
    """Set the quantity of one cart item.

    Body: { "quantity": 4 }
    A quantity of 0 removes the item.
    """

    data = request.get_json(silent=True) or {}

    item = CartItem.query.filter_by(
        user_id=request.current_user.id,
        product_id=product_id
    ).first()

    if item is None:
        return {"error": "That product is not in your cart."}, 404

    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return {"error": "Quantity must be a whole number."}, 400

    if quantity < 0:
        return {"error": "Quantity cannot be negative."}, 400

    # --- Removing an item ---
    if quantity == 0:
        db.session.delete(item)
        db.session.commit()

        return cart_response("Item removed from your cart.")

    # --- Cap at available stock ---
    product = db.session.get(Product, product_id)
    message = "Cart updated."

    if product is not None and quantity > product.stock:
        quantity = product.stock
        message = (
            f"Only {quantity} left in stock, so your quantity was set to {quantity}."
        )

    item.quantity = quantity

    db.session.commit()

    return cart_response(message)


@app.route("/api/cart/<int:product_id>", methods=["DELETE"])
@roles_required("buyer", "seller", "admin")
def remove_cart_item(product_id):
    """Remove one product from the cart."""

    item = CartItem.query.filter_by(
        user_id=request.current_user.id,
        product_id=product_id
    ).first()

    if item is None:
        return {"error": "That product is not in your cart."}, 404

    db.session.delete(item)
    db.session.commit()

    return cart_response("Item removed from your cart.")


@app.route("/api/cart", methods=["DELETE"])
@roles_required("buyer", "seller", "admin")
def clear_cart():
    """Empty the cart completely."""

    CartItem.query.filter_by(user_id=request.current_user.id).delete()
    db.session.commit()

    return cart_response("Your cart is now empty.")


# =========================
# ORDERS
# =========================
#
# THE CHECKOUT FLOW, step by step:
#
#   1. Check the cart is not empty.
#   2. Check EVERY item is still in stock. If any is not, refuse the
#      whole order and say which item - we never half-place an order.
#   3. Create the Order row with the delivery details.
#   4. Copy each cart item into an OrderItem, recording the price paid.
#   5. Reduce the stock for each product.
#   6. Empty the cart.
#
# Steps 3-6 happen in ONE database transaction. If anything fails
# half-way, db.session.rollback() undoes the lot, so we can never end
# up with stock reduced but no order recorded.

# Which status a seller/admin may move an order to next.
# This is what stops an order jumping straight from Pending to Delivered.
ALLOWED_STATUS_TRANSITIONS = {
    "Pending": ["Confirmed", "Cancelled"],
    "Confirmed": ["Shipped", "Cancelled"],
    "Shipped": ["Delivered"],
    "Delivered": [],
    "Cancelled": [],
}


def order_to_dict(order, include_items=True):
    """Turn an Order into JSON."""

    body = {
        "id": order.id,
        "user_id": order.user_id,
        "full_name": order.full_name,
        "phone": order.phone,
        "address": order.address,
        "city": order.city,
        "payment_method": order.payment_method,
        "total": order.total,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }

    if include_items:
        items = OrderItem.query.filter_by(order_id=order.id).all()

        body["items"] = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "unit_price": item.unit_price,
                "quantity": item.quantity,
                "subtotal": item.subtotal,
            }
            for item in items
        ]

        body["item_count"] = sum(item.quantity for item in items)

    return body


@app.route("/api/orders", methods=["POST"])
@roles_required("buyer", "seller", "admin")
def place_order():
    """Turn the current user's cart into an order.

    Body:
        {
          "full_name": "...", "phone": "...",
          "address": "...",   "city": "..."
        }
    """

    user = request.current_user
    data = request.get_json(silent=True) or {}

    # --- 1. Delivery details ---
    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()
    city = (data.get("city") or "").strip()

    missing = [
        label
        for label, value in [
            ("Full name", full_name),
            ("Phone number", phone),
            ("Delivery address", address),
            ("City", city),
        ]
        if not value
    ]

    if missing:
        return {
            "error": f"Please fill in: {', '.join(missing)}."
        }, 400

    # --- 2. Is there anything to order? ---
    cart_items = CartItem.query.filter_by(user_id=user.id).all()

    if not cart_items:
        return {"error": "Your cart is empty, so there is nothing to order."}, 400

    # --- 3. Stock check, BEFORE we change anything ---
    #
    # We check all of them first so the shopper gets one clear message
    # listing every problem, rather than fixing one item only to be
    # told about the next.
    problems = []

    for cart_item in cart_items:
        product = db.session.get(Product, cart_item.product_id)

        if product is None:
            problems.append("One of the products in your cart no longer exists.")
            continue

        if product.stock < cart_item.quantity:
            if product.stock == 0:
                problems.append(f"'{product.name}' is out of stock.")
            else:
                problems.append(
                    f"'{product.name}' - only {product.stock} left, "
                    f"but your cart asks for {cart_item.quantity}."
                )

    if problems:
        return {"error": " ".join(problems)}, 400

    # --- 4. Everything is fine - build the order ---
    try:
        order = Order(
            user_id=user.id,
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
            payment_method="Cash on Delivery",
            status="Pending",
            total=0,
        )

        db.session.add(order)

        # flush() sends the INSERT so order.id is filled in, but does not
        # commit - the whole thing is still one transaction.
        db.session.flush()

        running_total = 0

        for cart_item in cart_items:
            product = db.session.get(Product, cart_item.product_id)

            # Copy the name and price as they are RIGHT NOW
            line = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=cart_item.quantity,
            )

            db.session.add(line)

            running_total += product.price * cart_item.quantity

            # Reduce the stock
            product.stock -= cart_item.quantity

            # Remove the cart row
            db.session.delete(cart_item)

        order.total = round(running_total, 2)

        db.session.commit()

        return {
            "message": f"Order #{order.id} placed. Pay cash on delivery.",
            "order": order_to_dict(order),
        }, 201

    except Exception:
        # Something went wrong part-way through. Undo everything so we
        # do not leave the database half-updated.
        db.session.rollback()
        return {"error": "Could not place the order. Please try again."}, 500


@app.route("/api/orders", methods=["GET"])
@roles_required("buyer", "seller", "admin")
def get_orders():
    """List orders.

    Buyers see only their own.
    Sellers see orders containing at least one of their products.
    Admins see everything.

    Optional ?status=Pending filters by status.
    """

    user = request.current_user
    status_filter = request.args.get("status")

    if user.role == "buyer":
        query = Order.query.filter_by(user_id=user.id)

    elif user.role == "seller":
        # Gather the ids of orders that contain one of this seller's
        # products, then fetch just those.
        own_product_ids = [
            row.id for row in Product.query.filter_by(seller_id=user.id).all()
        ]

        order_ids = [
            row.order_id
            for row in OrderItem.query.filter(
                OrderItem.product_id.in_(own_product_ids)
            ).all()
        ] if own_product_ids else []

        query = Order.query.filter(Order.id.in_(order_ids))

    else:
        query = Order.query

    if status_filter:
        query = query.filter(Order.status.ilike(status_filter.strip()))

    orders = query.order_by(Order.created_at.desc(), Order.id.desc()).all()

    return [order_to_dict(order) for order in orders]


def load_order_for_viewing(order_id):
    """Fetch an order, but only if this user is allowed to see it.

    Returns (order, error_message, status_code).
    """
    user = request.current_user
    order = db.session.get(Order, order_id)

    if order is None:
        return None, "Order not found.", 404

    if user.role == "admin":
        return order, None, None

    if order.user_id == user.id:
        return order, None, None

    if user.role == "seller":
        # A seller may see an order only if it contains one of their
        # products. They must not see the rest of somebody else's order
        # history.
        own_product_ids = [
            row.id for row in Product.query.filter_by(seller_id=user.id).all()
        ]

        if own_product_ids:
            contains_theirs = OrderItem.query.filter(
                OrderItem.order_id == order_id,
                OrderItem.product_id.in_(own_product_ids)
            ).first()

            if contains_theirs:
                return order, None, None

    return None, "You do not have permission to view this order.", 403


@app.route("/api/orders/<int:order_id>", methods=["GET"])
@roles_required("buyer", "seller", "admin")
def get_single_order(order_id):
    """Return one order, if the caller is allowed to see it."""

    order, error, status = load_order_for_viewing(order_id)

    if error:
        return {"error": error}, status

    return order_to_dict(order)


@app.route("/api/orders/<int:order_id>/status", methods=["PUT"])
@roles_required("seller", "admin")
def update_order_status(order_id):
    """Move an order to the next stage. Sellers and admins only.

    Body: { "status": "Shipped" }
    """

    order = db.session.get(Order, order_id)

    if order is None:
        return {"error": "Order not found."}, 404

    # A seller may only touch orders that contain their products.
    if request.current_user.role == "seller":
        own_product_ids = [
            row.id
            for row in Product.query.filter_by(seller_id=request.current_user.id).all()
        ]

        contains_theirs = OrderItem.query.filter(
            OrderItem.order_id == order_id,
            OrderItem.product_id.in_(own_product_ids)
        ).first() if own_product_ids else None

        if contains_theirs is None:
            return {
                "error": "This order does not contain any of your products."
            }, 403

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().title()

    if new_status not in ORDER_STATUSES:
        return {
            "error": f"Status must be one of: {', '.join(ORDER_STATUSES)}."
        }, 400

    if new_status == order.status:
        return {
            "error": f"This order is already '{order.status}'."
        }, 400

    allowed = ALLOWED_STATUS_TRANSITIONS.get(order.status, [])

    if new_status not in allowed:
        if not allowed:
            return {
                "error": (
                    f"An order that is '{order.status}' cannot be changed "
                    "any further."
                )
            }, 400

        return {
            "error": (
                f"An order that is '{order.status}' can only move to: "
                f"{', '.join(allowed)}."
            )
        }, 400

    order.status = new_status
    db.session.commit()

    return {
        "message": f"Order #{order.id} is now '{order.status}'.",
        "order": order_to_dict(order),
    }, 200


@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
@roles_required("buyer", "seller", "admin")
def cancel_order(order_id):
    """Cancel an order.

    A buyer may cancel their own order, but only while it is still
    Pending. A seller or admin may cancel at a later stage.
    """

    user = request.current_user
    order = db.session.get(Order, order_id)

    if order is None:
        return {"error": "Order not found."}, 404

    is_own_order = order.user_id == user.id

    if not is_own_order and user.role not in ("seller", "admin"):
        return {"error": "You cannot cancel this order."}, 403

    if order.status == "Cancelled":
        return {"error": "This order has already been cancelled."}, 400

    if order.status == "Delivered":
        return {
            "error": "This order was already delivered, so it cannot be cancelled."
        }, 400

    if is_own_order and user.role == "buyer" and order.status != "Pending":
        return {
            "error": (
                f"Your order is already '{order.status}', so it can no "
                "longer be cancelled. Please contact the seller."
            )
        }, 400

    # Put the stock back, since these items are no longer being bought
    for line in OrderItem.query.filter_by(order_id=order_id).all():
        product = db.session.get(Product, line.product_id)

        if product is not None:
            product.stock += line.quantity

    order.status = "Cancelled"
    db.session.commit()

    return {
        "message": f"Order #{order.id} was cancelled and the stock was returned.",
        "order": order_to_dict(order),
    }, 200


# =========================
# REVIEWS AND RATINGS
# =========================

def rating_summary_for(product_ids):
    """Work out the average rating for a list of products.

    Returns { product_id: {"average": 4.5, "count": 12} }.

    Why one query instead of one per product? Because a product listing
    page shows 30 products, and 30 separate lookups to draw 30 little
    star badges is wasteful. This does it in a single grouped query.

    SQLAlchemy's func.avg and func.count turn into SQL AVG() and
    COUNT(), so the database does the arithmetic, not Python.
    """
    if not product_ids:
        return {}

    rows = (
        db.session.query(
            Review.product_id,
            db.func.avg(Review.rating),
            db.func.count(Review.id),
        )
        .filter(Review.product_id.in_(product_ids))
        .group_by(Review.product_id)
        .all()
    )

    return {
        product_id: {
            "average": round(float(average), 1),
            "count": count,
        }
        for product_id, average, count in rows
    }


def rating_for(product_id):
    """The summary for a single product, with a safe empty default."""
    return rating_summary_for([product_id]).get(
        product_id, {"average": 0.0, "count": 0}
    )


def has_ordered(user_id, product_id):
    """Has this user ever had this product in a placed order?

    Used to make sure only real customers can review. Note we check the
    ORDER, not the cart - browsing is not buying.
    """
    return (
        db.session.query(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id, OrderItem.product_id == product_id)
        .first()
        is not None
    )


@app.route("/api/products/<int:product_id>/reviews", methods=["GET"])
def get_product_reviews(product_id):
    """List every review for a product, newest first. Open to everyone."""

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    reviews = (
        Review.query.filter_by(product_id=product_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .all()
    )

    # Look up the reviewer names in one go
    user_ids = [review.user_id for review in reviews]

    names = {}

    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
        names = {user.id: user.name for user in users}

    return {
        "product_id": product_id,
        "summary": rating_for(product_id),
        "reviews": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "reviewer_name": names.get(review.user_id, "SmartCart user"),
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at.isoformat()
                if review.created_at
                else None,
            }
            for review in reviews
        ],
    }


@app.route("/api/products/<int:product_id>/reviews", methods=["POST"])
@roles_required("buyer", "seller", "admin")
def create_review(product_id):
    """Add a review. You must have ordered the product first.

    Body: { "rating": 4, "comment": "..." }
    """

    user = request.current_user

    product = db.session.get(Product, product_id)

    if product is None:
        return {"error": "Product not found."}, 404

    data = request.get_json(silent=True) or {}

    # --- Rating must be 1 to 5 ---
    try:
        rating = int(data.get("rating"))
    except (TypeError, ValueError):
        return {"error": "Rating must be a whole number from 1 to 5."}, 400

    if rating < 1 or rating > 5:
        return {"error": "Rating must be between 1 and 5 stars."}, 400

    comment = (data.get("comment") or "").strip()

    if len(comment) > 1000:
        return {"error": "Comment is too long (1000 characters maximum)."}, 400

    # --- Only real customers may review ---
    if not has_ordered(user.id, product_id):
        return {
            "error": (
                "You can only review products you have ordered and "
                "received."
            )
        }, 403

    # --- One review per person per product ---
    existing = Review.query.filter_by(
        user_id=user.id, product_id=product_id
    ).first()

    if existing:
        return {
            "error": "You have already reviewed this product. "
                     "You can edit your review instead."
        }, 409

    review = Review(
        user_id=user.id,
        product_id=product_id,
        rating=rating,
        comment=comment or None,
    )

    db.session.add(review)
    db.session.commit()

    return {
        "message": "Thanks for your review!",
        "summary": rating_for(product_id),
        "review": {
            "id": review.id,
            "user_id": user.id,
            "reviewer_name": user.name,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat()
            if review.created_at
            else None,
        },
    }, 201


@app.route("/api/reviews/<int:review_id>", methods=["PUT"])
@roles_required("buyer", "seller", "admin")
def update_review(review_id):
    """Edit your own review. Admins may edit any review.

    Body: { "rating": 3, "comment": "..." }
    Both fields are optional - send only what you want to change.
    """

    user = request.current_user
    review = db.session.get(Review, review_id)

    if review is None:
        return {"error": "Review not found."}, 404

    if review.user_id != user.id and user.role != "admin":
        return {"error": "You can only edit your own review."}, 403

    data = request.get_json(silent=True) or {}

    if "rating" in data:
        try:
            rating = int(data["rating"])
        except (TypeError, ValueError):
            return {"error": "Rating must be a whole number from 1 to 5."}, 400

        if rating < 1 or rating > 5:
            return {"error": "Rating must be between 1 and 5 stars."}, 400

        review.rating = rating

    if "comment" in data:
        comment = (data["comment"] or "").strip()

        if len(comment) > 1000:
            return {"error": "Comment is too long (1000 characters maximum)."}, 400

        review.comment = comment or None

    db.session.commit()

    return {
        "message": "Your review was updated.",
        "summary": rating_for(review.product_id),
        "review": {
            "id": review.id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat()
            if review.created_at
            else None,
        },
    }, 200


@app.route("/api/reviews/<int:review_id>", methods=["DELETE"])
@roles_required("buyer", "seller", "admin")
def delete_review(review_id):
    """Delete your own review. Admins may delete any review."""

    user = request.current_user
    review = db.session.get(Review, review_id)

    if review is None:
        return {"error": "Review not found."}, 404

    if review.user_id != user.id and user.role != "admin":
        return {"error": "You can only delete your own review."}, 403

    product_id = review.product_id

    db.session.delete(review)
    db.session.commit()

    return {
        "message": "Your review was removed.",
        "summary": rating_for(product_id),
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