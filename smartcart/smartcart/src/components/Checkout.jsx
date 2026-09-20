import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";
import { placeOrder } from "../data/api";

// The delivery form starts empty except for the name, which we can
// guess from the logged-in account.
const EMPTY = {
  full_name: "",
  phone: "",
  address: "",
  city: "",
};

function Checkout() {
  const navigate = useNavigate();
  const { user, isLoggedIn } = useAuth();
  const { items, cartCount, cartTotal, refreshCart } = useCart();

  const [form, setForm] = useState({
    ...EMPTY,
    full_name: user?.name || "",
  });

  const [error, setError] = useState(null);
  const [placing, setPlacing] = useState(false);

  const updateField = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setPlacing(true);

    try {
      const data = await placeOrder({
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        address: form.address.trim(),
        city: form.city.trim(),
      });

      // The backend emptied the cart as part of placing the order.
      // Pull the fresh (now empty) cart so the navbar count updates.
      await refreshCart();

      // Send the shopper to their order history so they can see it worked
      navigate("/orders", {
        state: { justPlaced: data.order.id, message: data.message },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setPlacing(false);
    }
  };

  // =========================
  // NOT LOGGED IN
  // =========================
  if (!isLoggedIn) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>CHECKOUT</p>
          <h1>Please Log In</h1>

          <div className="products-status products-error">
            <strong>You need an account to place an order.</strong>
            <p>
              Orders are saved to your account so you can track them
              later. Log in or register on the home page, then come
              back here to finish.
            </p>
          </div>

          {/* The auth card lives in the home page's `#auth` section.
              Sending people there directly saves them from landing on
              the top of the home page and having to work out where the
              login form is - which is exactly what this button used to
              do. The hash is handled by the home page's scroll logic,
              and by ScrollManager when arriving from another route. */}
          <Link to="/#auth" className="shop-btn">
            Log In or Register
          </Link>

          <Link to="/products" className="learn-btn">
            Keep Browsing
          </Link>
        </section>
      </main>
    );
  }

  // =========================
  // EMPTY CART
  // =========================
  if (items.length === 0) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>CHECKOUT</p>
          <h1>Your Cart Is Empty</h1>

          <span>Add something to your cart before checking out.</span>

          <Link to="/products" className="learn-btn">
            Browse Products
          </Link>
        </section>
      </main>
    );
  }

  // =========================
  // THE CHECKOUT FORM
  // =========================
  return (
    <main className="all-products-page">
      <section className="products-page-header">
        <p>CHECKOUT</p>

        <h1>Delivery Details</h1>

        <span>
          Pay cash when your order arrives. No card needed.
        </span>

        <Link to="/" className="learn-btn">
          Back to Home
        </Link>
      </section>

      <section className="collection-section">
        {error && (
          <div className="products-status products-error">
            <strong>We could not place your order.</strong>
            <p>{error}</p>
          </div>
        )}

        <div className="checkout-wrapper">

          {/* ============ LEFT: the form ============ */}
          <div className="manage-form-wrapper checkout-form-wrapper">
            <h2>Where should we deliver it?</h2>

            <form className="manage-form" onSubmit={handleSubmit}>

              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Ashim Sharma"
                  value={form.full_name}
                  onChange={updateField("full_name")}
                  required
                />
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input
                  type="tel"
                  placeholder="e.g. 9800000000"
                  value={form.phone}
                  onChange={updateField("phone")}
                  required
                />
                <small className="form-hint">
                  The delivery rider will call this number.
                </small>
              </div>

              <div className="form-group">
                <label>Delivery Address</label>
                <textarea
                  rows="3"
                  placeholder="House number, street, area"
                  value={form.address}
                  onChange={updateField("address")}
                  required
                />
              </div>

              <div className="form-group">
                <label>City</label>
                <input
                  type="text"
                  placeholder="e.g. Kathmandu"
                  value={form.city}
                  onChange={updateField("city")}
                  required
                />
              </div>

              <div className="payment-note">
                <strong>Cash on Delivery</strong>
                <p>
                  You pay the delivery rider in cash when your order
                  arrives. This project does not handle online payments.
                </p>
              </div>

              <div className="manage-form-actions">
                <button type="submit" className="auth-btn" disabled={placing}>
                  {placing
                    ? "Placing your order..."
                    : `Place Order · Rs. ${cartTotal.toLocaleString()}`}
                </button>
              </div>

            </form>
          </div>

          {/* ============ RIGHT: what is being ordered ============ */}
          <div className="cart-summary checkout-summary">
            <h3>Your Order</h3>

            {items.map((item) => (
              <div className="checkout-line" key={item.product_id}>
                <span>
                  {item.name}
                  <small> x{item.quantity}</small>
                </span>

                <span>
                  Rs. {(item.price * item.quantity).toLocaleString()}
                </span>
              </div>
            ))}

            <div className="summary-row">
              <span>Items</span>
              <span>{cartCount}</span>
            </div>

            <div className="summary-row total-row">
              <strong>Total</strong>
              <strong>Rs. {cartTotal.toLocaleString()}</strong>
            </div>
          </div>

        </div>
      </section>
    </main>
  );
}

export default Checkout;
