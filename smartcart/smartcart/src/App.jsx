import { useState } from "react";
import "./App.css";

import ProductList from "./components/ProductList";
import Auth from "./components/Auth";
import Products from "./components/Products";

import { useAuth } from "./context/useAuth";

import { Routes, Route, Link } from "react-router-dom";

function Home({
  cart,
  addToCart,
  increaseQuantity,
  decreaseQuantity,
  removeFromCart,
  cartCount,
  cartTotal,
}) {
  const { user, isLoggedIn } = useAuth();

  return (
    <div className="app">
      {/* ================= NAVBAR ================= */}
      <header className="navbar">
        <Link to="/" className="logo">
          Smart<span>Cart</span>
        </Link>

        <nav>
          <Link to="/">Home</Link>
          <Link to="/products">Products</Link>
          <a href="#categories">Categories</a>
          <a href="#about">About</a>
          <a href="#auth">
            {isLoggedIn ? `Hi, ${user.name.split(" ")[0]}` : "Login"}
          </a>
        </nav>

        <a href="#cart" className="cart-btn">
          Cart ({cartCount})
        </a>
      </header>

      {/* ================= HERO ================= */}
      <section className="hero" id="home">
        <div className="hero-content">
          <p className="hero-label">
            SMART SHOPPING IN NEPAL
          </p>

          <h1>
            Smart Shopping.
            <br />
            <span>Simple Living.</span>
          </h1>

          <p className="hero-description">
            Discover products you love, explore personalized
            recommendations, and enjoy a simple shopping
            experience designed around you.
          </p>

          <div className="hero-buttons">
            <Link to="/products">
              <button className="shop-btn">
                Explore Products
              </button>
            </Link>

            <a href="#about" className="learn-btn">
              Learn More
            </a>
          </div>
        </div>

        <div className="hero-image">
          <div className="hero-image-bg"></div>

          <img
            src="/src/assets/home.png"
            alt="SmartCart shopping"
          />
        </div>
      </section>

      {/* ================= TRUST BAR ================= */}
      <section className="trust-bar">
        <div>
          <strong>01</strong>
          <span>Nepal Focused</span>
        </div>

        <div>
          <strong>02</strong>
          <span>Easy Shopping</span>
        </div>

        <div>
          <strong>03</strong>
          <span>Secure Experience</span>
        </div>

        <div>
          <strong>04</strong>
          <span>Smart Recommendations</span>
        </div>
      </section>

      {/* ================= PRODUCTS ================= */}
      <ProductList addToCart={addToCart} />

      {/* ================= CATEGORIES ================= */}
      <section
        className="category-section"
        id="categories"
      >
        <div className="section-heading">
          <span className="section-label">
            SHOP BY CATEGORY
          </span>

          <h2>
            Explore Our Collections
          </h2>

          <p>
            Find products selected for your everyday needs.
          </p>
        </div>

        <div className="category-grid">

          {/* ELECTRONICS */}
<div className="category-card">
  <div className="category-number">
    01
  </div>

  <h3>
    Electronics
  </h3>

  <p>
    Smart gadgets and useful technology
    for modern living.
  </p>

  <Link to="/products?category=Electronics">
    Explore Collection →
  </Link>
</div>


{/* FASHION */}
<div className="category-card">
  <div className="category-number">
    02
  </div>

  <h3>
    Fashion
  </h3>

  <p>
    Comfortable and stylish products
    for everyday life.
  </p>

  <Link to="/products?category=Fashion">
    Explore Collection →
  </Link>
</div>


{/* HOME */}
<div className="category-card">
  <div className="category-number">
    03
  </div>

  <h3>
    Home & Living
  </h3>

  <p>
    Simple products that make your
    space feel better.
  </p>

  <Link to="/products?category=Home">
    Explore Collection →
  </Link>
</div>
</div>
      </section>

      {/* ================= AI SECTION ================= */}
      <section className="ai-section">
        <div className="ai-content">
          <span className="section-label">
            SMART RECOMMENDATIONS
          </span>

          <h2>
            Find Products
            <br />
            <span>Made for You.</span>
          </h2>

          <p>
            SmartCart uses your preferences to help
            you discover products that match your
            interests and shopping needs.
          </p>

          <button className="ai-btn">
            Try AI Recommendations →
          </button>
        </div>

        <div className="ai-visual">
          <div className="ai-circle">
            AI
          </div>

          <div className="ai-card">
            Personalized
            <br />
            Recommendations
          </div>
        </div>
      </section>

      {/* ================= CART ================= */}
      <section className="cart-section" id="cart">
        <div className="cart-header">
          <span className="section-label">
            YOUR SHOPPING CART
          </span>

          <h2>
            Shopping Cart
          </h2>
        </div>

        {cart.length === 0 ? (
          <div className="empty-cart">
            <div className="empty-cart-icon">
              00
            </div>

            <h3>
              Your cart is empty
            </h3>

            <p>
              Add products to your cart to get started.
            </p>

            <Link to="/products">
              <button className="shop-btn">
                Browse Products
              </button>
            </Link>
          </div>
        ) : (
          <div className="cart-container">

            <div className="cart-items">
              {cart.map((item) => (
                <div
                  className="cart-item"
                  key={item.id}
                >
                  <img
                    src={item.image}
                    alt={item.name}
                  />

                  <div className="cart-item-info">
                    <small>
                      {item.category}
                    </small>

                    <h3>
                      {item.name}
                    </h3>

                    <p>
                      Rs. {item.price.toLocaleString()}
                    </p>
                  </div>

                  <div className="quantity-controls">
                    <button
                      onClick={() =>
                        decreaseQuantity(item.id)
                      }
                    >
                      −
                    </button>

                    <span>
                      {item.quantity}
                    </span>

                    <button
                      onClick={() =>
                        increaseQuantity(item.id)
                      }
                    >
                      +
                    </button>
                  </div>

                  <div className="item-total">
                    <strong>
                      Rs.{" "}
                      {(
                        item.price * item.quantity
                      ).toLocaleString()}
                    </strong>

                    <button
                      className="remove-btn"
                      onClick={() =>
                        removeFromCart(item.id)
                      }
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="cart-summary">
              <h3>
                Order Summary
              </h3>

              <div className="summary-row">
                <span>
                  Items
                </span>

                <span>
                  {cartCount}
                </span>
              </div>

              <div className="summary-row total-row">
                <strong>
                  Total
                </strong>

                <strong>
                  Rs. {cartTotal.toLocaleString()}
                </strong>
              </div>

              <button className="checkout-btn">
                Proceed to Checkout
              </button>
            </div>

          </div>
        )}
      </section>

      {/* ================= FEATURES ================= */}
      <section
        className="features"
        id="about"
      >
        <div className="feature-card">
          <span className="feature-number">
            01
          </span>

          <h3>
            Easy Shopping
          </h3>

          <p>
            Browse and discover products through
            a simple and user-friendly interface.
          </p>
        </div>

        <div className="feature-card">
          <span className="feature-number">
            02
          </span>

          <h3>
            AI Recommendations
          </h3>

          <p>
            Discover products based on your
            preferences and interests.
          </p>
        </div>

        <div className="feature-card">
          <span className="feature-number">
            03
          </span>

          <h3>
            Trusted Shopping
          </h3>

          <p>
            View product information and reviews
            before making a purchase.
          </p>
        </div>
      </section>

      {/* ================= AUTH ================= */}
      <Auth />

      {/* ================= CONTACT ================= */}
      <section
        className="contact-section"
        id="contact"
      >
        <span className="section-label">
          GET IN TOUCH
        </span>

        <h2>
          Shopping Made Simple.
        </h2>

        <p>
          SmartCart — a smarter shopping experience
          designed for Nepal.
        </p>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="footer">
  <div className="footer-content">

    {/* Brand */}
    <div className="footer-brand">
      <div className="footer-logo">
        Smart<span>Cart</span>
      </div>

      <p>
        A simple and smart shopping experience for your everyday needs.
        Discover quality products at affordable prices.
      </p>
    </div>

    {/* Quick Links */}
    <div className="footer-column">
      <h4>Quick Links</h4>

      <a href="/">Home</a>
      <a href="/products">Products</a>
      <a href="#categories">Categories</a>
      <a href="#about">About Us</a>
    </div>

    {/* Contact */}
    <div className="footer-column">
      <h4>Contact Us</h4>

      <a href="mailto:hello@smartcart.com">
        hello@smartcart.com
      </a>

      <a href="tel:+9779800000000">
        +977 9860406288
      </a>

      <span>Kathmandu, Nepal</span>
    </div>

    {/* Social Media */}
    <div className="footer-column">
      <h4>Follow Us</h4>

      <div className="social-links">
        <a href="#" aria-label="Facebook">
          Facebook
        </a>

        <a href="#" aria-label="Instagram">
          Instagram
        </a>

        <a href="#" aria-label="TikTok">
          TikTok
        </a>

        <a href="#" aria-label="LinkedIn">
          LinkedIn
        </a>
      </div>
    </div>

  </div>

  {/* Bottom Footer */}
  <div className="footer-bottom">

    <p>
      © 2026 SmartCart. All rights reserved.
    </p>

    <div className="footer-legal">
      <a href="#">Privacy Policy</a>
      <a href="#">Terms & Conditions</a>
    </div>

  </div>
</footer>
    </div>
  );
}


function App() {
  const [cart, setCart] = useState([]);

  /* =========================
     CART FUNCTIONS
  ========================= */

  const addToCart = (product) => {
    setCart((currentCart) => {
      const existingProduct = currentCart.find(
        (item) => item.id === product.id
      );

      if (existingProduct) {
        return currentCart.map((item) =>
          item.id === product.id
            ? {
                ...item,
                quantity: item.quantity + 1,
              }
            : item
        );
      }

      return [
        ...currentCart,
        {
          ...product,
          quantity: 1,
        },
      ];
    });
  };

  const increaseQuantity = (id) => {
    setCart((currentCart) =>
      currentCart.map((item) =>
        item.id === id
          ? {
              ...item,
              quantity: item.quantity + 1,
            }
          : item
      )
    );
  };

  const decreaseQuantity = (id) => {
    setCart((currentCart) =>
      currentCart
        .map((item) =>
          item.id === id
            ? {
                ...item,
                quantity: item.quantity - 1,
              }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  };

  const removeFromCart = (id) => {
    setCart((currentCart) =>
      currentCart.filter(
        (item) => item.id !== id
      )
    );
  };

  const cartCount = cart.reduce(
    (total, item) => total + item.quantity,
    0
  );

  const cartTotal = cart.reduce(
    (total, item) =>
      total + item.price * item.quantity,
    0
  );

  return (
    <Routes>

      {/* HOME PAGE */}
      <Route
        path="/"
        element={
          <Home
            cart={cart}
            addToCart={addToCart}
            increaseQuantity={increaseQuantity}
            decreaseQuantity={decreaseQuantity}
            removeFromCart={removeFromCart}
            cartCount={cartCount}
            cartTotal={cartTotal}
          />
        }
      />

      {/* ALL PRODUCTS PAGE */}
      <Route
        path="/products"
        element={
          <Products
            addToCart={addToCart}
          />
        }
      />

    </Routes>
  );
}

export default App;