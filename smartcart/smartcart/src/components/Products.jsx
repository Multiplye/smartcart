import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getProducts } from "../data/api";
import { useCart } from "../context/useCart";

function Products() {
  const [searchParams] = useSearchParams();

  const category = searchParams.get("category");

  // Reach the shared cart directly rather than taking a prop
  const { addItem } = useCart();

  const [justAdded, setJustAdded] = useState(null);
  const [addError, setAddError] = useState(null);

  const handleAdd = async (product) => {
    setAddError(null);

    try {
      await addItem(product);
      setJustAdded(product.id);

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

    // Cleanup: stop updating state if the user leaves this page early
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredProducts = category
    ? products.filter(
        (product) =>
          product.category.toLowerCase() ===
          category.toLowerCase()
      )
    : products;

  const pageTitle = category
    ? category === "Home"
      ? "Home & Living"
      : category
    : "All Products";

  return (
    <main className="all-products-page">
      {/* ================= HEADER ================= */}
      <section className="products-page-header">
        <p>SMARTCART COLLECTION</p>

        <h1>{pageTitle}</h1>

        <span>
          {category
            ? `Explore our ${pageTitle.toLowerCase()} collection.`
            : "Discover products for your everyday needs."}
        </span>

        <Link to="/" className="learn-btn">
          Back to Home
        </Link>
      </section>

      {/* ================= PRODUCTS ================= */}
      <section className="collection-section">

        {loading && (
          <p className="products-status">
            Loading products...
          </p>
        )}

        {error && (
          <div className="products-status products-error">
            <strong>Could not load products.</strong>

            <p>
              Make sure the Flask backend is running on{" "}
              http://127.0.0.1:5000
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

        {!loading && !error && filteredProducts.length === 0 && (
          <p className="products-status">
            No products found in this category.
          </p>
        )}

        {!loading && !error && (
          <div className="product-grid">
          {filteredProducts.map((product) => (
            <div
              className="product-card"
              key={product.id}
            >
              <div className="product-image">
                <img
                  src={product.image}
                  alt={product.name}
                />
              </div>

              <div className="product-info">
                <small>
                  {product.category}
                </small>

                <h3>
                  {product.name}
                </h3>

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
      </section>
    </main>
  );
}

export default Products;