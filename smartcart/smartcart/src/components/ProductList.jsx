import { useEffect, useState } from "react";
import { getProducts } from "../data/api";

function ProductList({ addToCart }) {
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

      {loading && (
        <p className="products-status">
          Loading products...
        </p>
      )}

      {error && (
        <div className="products-status products-error">
          <strong>Could not load products.</strong>

          <p>
            Make sure the Flask backend is running on
            http://127.0.0.1:5000
          </p>

          <small>{error}</small>
        </div>
      )}

      {!loading && !error && (
        <div className="product-grid">
        {featuredProducts.map((product) => (
          <div className="product-card" key={product.id}>
            <div className="product-image">
              <img
                src={product.image}
                alt={product.name}
              />
            </div>

            <div className="product-info">
              <small>{product.category}</small>

              <h3>{product.name}</h3>

              <p className="product-price">
                Rs. {product.price.toLocaleString()}
              </p>

              <button
                className="add-cart-btn"
                onClick={() => addToCart(product)}
              >
                Add to Cart
              </button>
            </div>
          </div>
        ))}
        </div>
      )}
    </section>
  );
}

export default ProductList;