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
        "stock": product.stock
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


@app.route("/api/products", methods=["GET"])
def get_products():
    products = Product.query.all()

    return [product_to_dict(product) for product in products]


# =========================
# CREATE PRODUCT
# =========================

@app.route("/api/products", methods=["POST"])
def create_product():

    data = request.get_json()

    product = Product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        category=data["category"],
        image=data.get("image"),
        stock=data.get("stock", 0)
    )

    db.session.add(product)
    db.session.commit()

    return {
        "message": "Product created successfully!",
        "product": product_to_dict(product)
    }, 201


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