import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";

/**
 * The shared navbar.
 *
 * This used to live inside App.jsx, which caused a subtle bug: the
 * section links ("Categories", "About") were plain anchors like
 * `href="#categories"`. Those sections only exist on the HOME page, so
 * clicking them from /admin or /recommendations did nothing at all -
 * the browser looked for an element with that id, found none, and
 * stayed put.
 *
 * The fix is to remember that those are home-page sections:
 *
 *   - on the home page  -> a plain anchor, so the browser scrolls
 *   - anywhere else     -> a link to "/#categories", which navigates
 *                          home AND then scrolls
 *
 * `location.pathname` is what lets us tell the two cases apart.
 */
function Navbar() {
  const { user, isLoggedIn, isSeller, isAdmin } = useAuth();
  const { cartCount } = useCart();

  /*
    The cart badge gives a small pop whenever the count changes, so
    adding something to the basket is acknowledged even when the
    navbar is off to the side of what you were looking at.

    This has to be driven by the PREVIOUS value: the count alone
    cannot tell us whether it changed or the page simply re-rendered.
    Comparing against a ref, and only popping when they differ, means
    the badge is still on first load and every unrelated render is
    still - it only moves when the number actually moves.

    The class is removed on a timer so the animation can run again
    next time. React would not re-trigger a CSS animation that is
    already applied, so the class has to come off in between.
  */
  const previousCount = useRef(cartCount);
  const [popping, setPopping] = useState(false);

  useEffect(() => {
    const changed = previousCount.current !== cartCount;
    previousCount.current = cartCount;

    if (!changed) return undefined;

    setPopping(true);
    const timer = window.setTimeout(() => setPopping(false), 420);

    return () => window.clearTimeout(timer);
  }, [cartCount]);

  const location = useLocation();
  const navigate = useNavigate();

  const onHomePage = location.pathname === "/";

  // Build a section link that works from any page.
  const sectionLink = (hash) =>
    onHomePage ? `#${hash}` : `/#${hash}`;

  // On the home page we want a real anchor so the browser's native
  // smooth scroll and the back button both behave normally. On other
  // pages we push the route and let the home page scroll itself.
  const handleSectionClick = (event, hash) => {
    if (onHomePage) return;

    event.preventDefault();
    navigate(`/#${hash}`);
  };

  const firstName = user?.name ? user.name.split(" ")[0] : "";

  return (
    <header className="navbar">
      <Link to="/" className="logo">
        Smart<span>Cart</span>
      </Link>

      <nav>
        <Link to="/">Home</Link>
        <Link to="/products">Products</Link>
        <Link to="/recommendations">For You</Link>

        {isLoggedIn && <Link to="/orders">Orders</Link>}

        {/* Sellers and admins both manage listings. */}
        {(isSeller || isAdmin) && <Link to="/manage">Manage</Link>}

        {/* Only admins see this one. Note the backend enforces it too -
            hiding a link is convenience, never security. */}
        {isAdmin && <Link to="/admin">Admin</Link>}

        <a
          href={sectionLink("categories")}
          onClick={(e) => handleSectionClick(e, "categories")}
        >
          Categories
        </a>

        <a
          href={sectionLink("about")}
          onClick={(e) => handleSectionClick(e, "about")}
        >
          About
        </a>

        <a
          href={sectionLink("auth")}
          onClick={(e) => handleSectionClick(e, "auth")}
        >
          {isLoggedIn ? `Hi, ${firstName}` : "Login"}
        </a>
      </nav>

      <Link to="/checkout" className="cart-btn">
        Cart (
        <span className={`cart-count-badge ${popping ? "cart-count-pop" : ""}`}>
          {cartCount}
        </span>
        )
      </Link>
    </header>
  );
}

export default Navbar;
