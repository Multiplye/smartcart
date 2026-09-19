import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getProducts } from "../data/api";
import { useCart } from "../context/useCart";

function ProductList() {
  // The cart is shared app-wide, so this component reaches it directly
  // instead of being handed a prop from App.
  const { addItem } = useCart();

  const navigate = useNavigate();

  // The home page keeps its own simple search box that hands the term
  // to the products page. Deliberately a hand-off rather than a second
  // implementation: one search that works properly is better than two
  // that can drift apart.
  const [searchInput, setSearchInput] = useState("");

  const handleSearch = (event) => {
    event.preventDefault();

    const clean = searchInput.trim();

    navigate(clean ? `/products?search=${encodeURIComponent(clean)}` : "/products");
  };

  // Tracks which "Add to Cart" was clicked last, so we can show a short
  // confirmation on that one card instead of a message at the top of
  // the page that is easy to miss.
  const [justAdded, setJustAdded] = useState(null);
  const [addError, setAddError] = useState(null);

  const handleAdd = async (product) => {
    setAddError(null);

    try {
      await addItem(product);
      setJustAdded(product.id);

      // Put the button back to normal after a moment
      window.setTimeout(() => {
        setJustAdded((current) => (current === product.id ? null : current));
      }, 1500);
    } catch (err) {
      setAddError(err.message);
    }
  };

  // =========================
  // LOAD PRODUCTS FROM BACKEND
  // =========================
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      try {
        setLoading(true);
        setError(null);

        const data = await getProducts();

        if (!cancelled) {
          setProducts(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadProducts();

    return () => {
      cancelled = true;
    };
  }, []);

  // Show only 4 products on the home page
  const featuredProducts = products.slice(0, 4);

  return (
    <section className="products-section" id="products">
      <div className="products-header">
        <p>FEATURED PRODUCTS</p>

        <h2>Explore Our Products</h2>

        <span>
          A few of our popular picks for everyday shopping.
        </span>
      </div>

      {/* A quick way in. Submitting hands off to the products page,
          where the full search and category filters live. */}
      <form className="home-search" onSubmit={handleSearch} role="search">
        <input
          type="search"
          className="search-input"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Search for a product"
          aria-label="Search for a product"
        />

        <button type="submit" className="search-btn">
          Search
        </button>
      </form>

      {loading && (
        <p className="products-status">
          Loading products...
        </p>
      )}

      {error && (
        <div className="products-status products-error">
          <strong>Could not load products.</strong>

          <p>
            Make sure the Flask backend is running, then reload
            this page.
          </p>

          <small>{error}</small>
        </div>
      )}

      {addError && (
        <div className="products-status products-error">
          <strong>Could not add that to your cart.</strong>
          <p>{addError}</p>
        </div>
      )}

      {!loading && !error && (
        <div className="product-grid">
        {featuredProducts.map((product) => (
          <div className="product-card" key={product.id}>
            {/* The home cards link through to the product page too.
                Without this the featured products were the only ones
                in the whole app you could not click into. */}
            <Link to={`/product/${product.id}`} className="product-image">
              <img
                src={product.image}
                alt={product.name}
              />
            </Link>

            <div className="product-info">
              <small>{product.category}</small>

              <Link
                to={`/product/${product.id}`}
                className="product-name-link"
              >
                <h3>{product.name}</h3>
              </Link>

              <p className="product-price">
                Rs. {product.price.toLocaleString()}
              </p>

              <button
                className="add-cart-btn"
                onClick={() => handleAdd(product)}
                disabled={product.stock < 1}
              >
                {product.stock < 1
                  ? "Out of Stock"
                  : justAdded === product.id
                    ? "Added"
                    : "Add to Cart"}
              </button>
            </div>
          </div>
        ))}
        </div>
      )}

      <div className="products-more">
        <Link to="/products" className="learn-btn">
          View All Products
        </Link>
      </div>
    </section>
  );
}

export default ProductList;