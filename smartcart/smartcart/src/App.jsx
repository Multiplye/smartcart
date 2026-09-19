import "./App.css";

import ProductList from "./components/ProductList";
import Auth from "./components/Auth";
import Products from "./components/Products";
import ManageProducts from "./components/ManageProducts";
import Checkout from "./components/Checkout";
import Orders from "./components/Orders";
import ProductDetail from "./components/ProductDetail";
import Recommendations from "./components/Recommendations";
import Admin from "./components/Admin";
import Navbar from "./components/Navbar";
import HeroArt from "./components/HeroArt";
import PageLayout from "./components/PageLayout";
import ScrollManager from "./components/ScrollManager";

import { useAuth } from "./context/useAuth";
import { useCart } from "./context/useCart";

import { Routes, Route, Link } from "react-router-dom";

function Home() {
  // The cart now comes from context, so it is shared by every page and
  // survives a refresh. No props to thread through any more.
  const {
    items: cart,
    cartCount,
    cartTotal,
    loading: cartLoading,
    error: cartError,
    setQuantity,
    removeItem,
  } = useCart();

  const { isLoggedIn } = useAuth();

  const increaseQuantity = (productId) =>
    setQuantity(productId, (cart.find((i) => i.product_id === productId)?.quantity ?? 0) + 1);

  const decreaseQuantity = (productId) =>
    setQuantity(productId, Math.max(0, (cart.find((i) => i.product_id === productId)?.quantity ?? 1) - 1));

  return (
    <div className="app">
      {/* ================= NAVBAR ================= */}
      <Navbar />


      {/* ================= HERO ================= */}
      <section className="hero" id="home">
        <div className="hero-content">
          <p className="hero-label">
            SMART SHOPPING IN NEPAL
          </p>

          {/*
            The two lines used to be identical in weight and only differed
            in colour, which made the heading read as one loud block. The
            second line now switches to Playfair Display, so the serif
            carries the emphasis instead of the colour having to do all of
            it. This is the same pairing used on the "For You" page, so the
            site keeps one voice across both.
          */}
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

        {/*
          The illustration used to be an <img> pointing at
          src/assets/home.png. That file carried a visible "Google"
          watermark and went soft on large screens, so it has been
          replaced with an animated inline SVG component. See
          components/HeroArt.jsx for why it is drawn rather than
          loaded from a file.
        */}
        <div className="hero-image">
          <div className="hero-image-bg"></div>

          <HeroArt />
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
      <ProductList />

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

          <Link to="/recommendations">
            <button className="ai-btn">
              Try AI Recommendations →
            </button>
          </Link>
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

        {cartLoading && (
          <p className="products-status">Loading your cart...</p>
        )}

        {cartError && (
          <div className="products-status products-error">
            <strong>Could not load your cart.</strong>
            <p>{cartError}</p>
          </div>
        )}

        {!cartLoading && cart.length === 0 ? (
          <div className="empty-cart">
            <div className="empty-cart-icon">
              00
            </div>

            <h3>
              Your cart is empty
            </h3>

            <p>
              {isLoggedIn
                ? "Add products to your cart to get started."
                : "Log in and your cart will be saved to your account."}
            </p>

            <Link to="/products">
              <button className="shop-btn">
                Browse Products
              </button>
            </Link>
          </div>
        ) : (
          !cartLoading && (
          <div className="cart-container">

            <div className="cart-items">
              {cart.map((item) => (
                <div
                  className="cart-item"
                  key={item.product_id}
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
                        decreaseQuantity(item.product_id)
                      }
                    >
                      −
                    </button>

                    <span>
                      {item.quantity}
                    </span>

                    <button
                      onClick={() =>
                        increaseQuantity(item.product_id)
                      }
                    >
                      +
                    </button>
                  </div>

                  <div className="item-total">
                    <strong>
                      Rs.{" "}
                      {(item.price * item.quantity).toLocaleString()}
                    </strong>

                    <button
                      className="remove-btn"
                      onClick={() =>
                        removeItem(item.product_id)
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

              <Link to="/checkout" className="checkout-btn-link">
                <button className="checkout-btn">
                  Proceed to Checkout
                </button>
              </Link>
            </div>

          </div>
          )
        )}
      </section>

      {/* ================= ABOUT =================
          This used to be a bare "features" strip that happened to
          carry id="about". Two things were wrong:

            1. There was no actual About section, so clicking "About"
               in the navbar landed on three feature cards with no
               explanation of what SmartCart is.

            2. The navbar's "Login" link pointed at "#auth" and no
               element had that id at all - so it silently did
               nothing. The auth card is a few lines below and now
               carries the id it always should have had.
      ========================================= */}
      <section className="about-section" id="about">
        <div className="section-heading">
          <span className="section-label">ABOUT SMARTCART</span>

          <h2>A Smarter Way to Shop</h2>

          <p>
            SmartCart is an online marketplace built for Nepal. It
            pairs a simple shopping experience with a recommendation
            engine that learns what you like from what you buy.
          </p>
        </div>

        <div className="features">
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
        </div>

        {/* A short, honest description of how the AI actually works.
            Worth having on the page: it is the project's headline
            feature, and a visitor should be able to understand it. */}
        <div className="about-how">
          <h3>How the recommendations work</h3>

          <p>
            Every product&apos;s name, category and description is
            turned into a mathematical vector using TF-IDF, which
            gives more weight to words that are distinctive to a
            product. SmartCart then measures the angle between those
            vectors with cosine similarity to find products that are
            genuinely alike.
          </p>

          <p>
            Once you have placed an order, the vectors of what you
            bought are averaged into a taste profile, and every other
            product is scored against it. Ratings are blended in as a
            small bonus, so a strong match with a good average rating
            comes out on top.
          </p>

          <Link to="/recommendations" className="about-cta">
            See your recommendations →
          </Link>
        </div>
      </section>

      {/* ================= AUTH =================
          id="auth" is what the navbar's Login link targets. Without
          it that link had nothing to scroll to. */}
      <div id="auth">
        <Auth />
      </div>

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
  // The cart lives in CartProvider now (see src/context/CartProvider.jsx),
  // so this component no longer needs to hold any cart state.
  // ProductList and Products reach the cart themselves via useCart().

  /* =========================
     NAVBAR
     =========================
     Shared by every page, so it can show the cart count and the right
     links no matter where you are.

     It would be cleaner still to pull this into its own component -
     that is a good refactor for later, once the pages settle down.
  ========================= */
  /* =========================
     ROUTES
     =========================
     Home renders its own navbar (the hero sits directly under it).
     Every other page is wrapped in PageLayout, which supplies the
     navbar. Wrapping at the route level means a new page cannot
     forget to include it.
  ========================= */
  const wrap = (page) => <PageLayout>{page}</PageLayout>;

  return (
    <>
      {/* Runs on every navigation. Not visible - it just fixes
          scrolling, which React Router leaves to you. */}
      <ScrollManager />

      <Routes>

        {/* HOME PAGE - renders its own Navbar */}
        <Route path="/" element={<Home />} />

        {/* ALL PRODUCTS PAGE */}
        <Route path="/products" element={wrap(<Products />)} />

        {/* ONE PRODUCT - with its reviews and related products */}
        <Route path="/product/:productId" element={wrap(<ProductDetail />)} />

        {/* AI RECOMMENDATIONS - personalised, or popular for a visitor */}
        <Route path="/recommendations" element={wrap(<Recommendations />)} />

        {/* CHECKOUT - cart to order */}
        <Route path="/checkout" element={wrap(<Checkout />)} />

        {/* ORDER HISTORY - all three roles, different views */}
        <Route path="/orders" element={wrap(<Orders />)} />

        {/* SELLER / ADMIN PRODUCT MANAGEMENT */}
        <Route path="/manage" element={wrap(<ManageProducts />)} />

        {/* ADMIN PANEL - the backend rejects anyone who is not an admin */}
        <Route path="/admin" element={wrap(<Admin />)} />

      </Routes>
    </>
  );
}

export default App;