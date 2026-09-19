import { Link } from "react-router-dom";

import { useCart } from "../context/useCart";
import { useState } from "react";

import Stars from "./Stars";

/**
 * A horizontal row of recommended products.
 *
 * Used in two places with slightly different wording:
 *
 *   variant="similar"    - on a product page. "You might also like"
 *   variant="personal"   - on the recommendations page. "Picked for you"
 *
 * The component itself does not fetch anything. Whoever renders it
 * already has the list, which keeps the fetching rules (and the error
 * handling) in one place per page.
 */
function RecommendationStrip({
  title = "You might also like",
  subtitle = null,
  products = [],
  variant = "similar",
}) {
  const { addItem } = useCart();

  // Which card was just added to the cart, so we can flash "Added"
  // on that one button instead of all of them.
  const [justAddedId, setJustAddedId] = useState(null);

  const [error, setError] = useState(null);

  const handleAdd = async (product) => {
    setError(null);

    try {
      await addItem(product);
      setJustAddedId(product.id);

      window.setTimeout(() => setJustAddedId(null), 1500);
    } catch (err) {
      setError(err.message);
    }
  };

  // Nothing to show. Returning null (rather than an empty frame) keeps
  // the page tidy when a recommendation list is legitimately empty -
  // for example a brand new catalogue.
  if (products.length === 0) return null;

  return (
    <section className={`rec-strip rec-strip-${variant}`}>
      <div className="rec-strip-head">
        <div>
          <span className="section-label">
            {variant === "personal"
              ? "SMART RECOMMENDATIONS"
              : "RELATED PRODUCTS"}
          </span>

          <h3>{title}</h3>
        </div>

        {subtitle && <p className="rec-strip-subtitle">{subtitle}</p>}
      </div>

      {error && (
        <p className="rec-strip-error" role="alert">
          {error}
        </p>
      )}

      <div className="rec-strip-row">
        {products.map((product) => (
          <article className="rec-card" key={product.id}>
            <Link to={`/product/${product.id}`} className="rec-card-image-link">
              <img src={product.image} alt={product.name} />
            </Link>

            <div className="rec-card-body">
              <small>{product.category}</small>

              <Link to={`/product/${product.id}`} className="rec-card-name">
                {product.name}
              </Link>

              {/* Only shown when we actually know the rating. The
                  listing endpoints always send both keys, but the
                  recommender objects come through the same helper, so
                  this guard is just belt and braces. */}
              {product.rating_count > 0 ? (
                <div className="rec-card-rating">
                  <Stars value={product.rating_average} size="sm" />
                  <span>
                    {product.rating_average.toFixed(1)} ({product.rating_count})
                  </span>
                </div>
              ) : (
                <div className="rec-card-rating">
                  <span className="rec-card-no-rating">No reviews yet</span>
                </div>
              )}

              <div className="rec-card-foot">
                <strong>Rs. {product.price.toLocaleString()}</strong>

                <button
                  className="add-cart-btn rec-add-btn"
                  onClick={() => handleAdd(product)}
                  disabled={product.stock < 1}
                >
                  {product.stock < 1
                    ? "Out of Stock"
                    : justAddedId === product.id
                      ? "Added"
                      : "Add"}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default RecommendationStrip;
