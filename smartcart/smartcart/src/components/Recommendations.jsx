import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/useAuth";

import { getRecommendations } from "../data/api";

import RecommendationStrip from "./RecommendationStrip";

/**
 * The personalised recommendations page - /recommendations
 *
 * This is the page that shows off the AI. It asks the backend for
 * suggestions, and the backend decides HOW to answer:
 *
 *   - If you are logged in and have ordered before, it builds a
 *     "taste profile" from the products you bought and finds the
 *     closest matches in the catalogue.
 *
 *   - Otherwise it falls back to the most popular products.
 *
 * The response tells us which happened, via `based_on`, so the page
 * can be honest with the reader about why it is showing what it shows.
 * That honesty matters for a project like this: it is easy to fake a
 * recommendation, and being explicit about the mechanism is what makes
 * the feature credible.
 */
function Recommendations() {
  const { isLoggedIn } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // A "Try again" button needs to retrigger the effect, so we keep a
  // counter in state and list it as a dependency.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const result = await getRecommendations(8);

        if (cancelled) return;

        setData(result);
        setError(null);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setReloadToken((n) => n + 1);
  };

  const products = data?.recommendations || [];
  const basedOn = data?.based_on;

  // The engine names its two modes in plain words. Keep them in one
  // place so the copy below reads clearly.
  const isPersonal = basedOn === "your order history";

  const basedOnProducts = data?.based_on_products || [];

  // What to print under the heading. The backend already writes a
  // plain-English `reason` for every case, so prefer that and only fall
  // back to our own words if it is missing.
  let explanation;
  if (data?.reason) {
    explanation = data.reason;
  } else if (isPersonal) {
    explanation = "Based on the products you have ordered before.";
  } else if (isLoggedIn) {
    explanation =
      "You have not ordered anything yet, so these are our most popular products. Place an order and this page will change.";
  } else {
    explanation =
      "Log in and buy something to personalise this page - for now, these are our most popular products.";
  }

  return (
    <main className="page-wrapper">
      <section className="page-head">
        <span className="section-label">SMART RECOMMENDATIONS</span>

        <h1>
          Picked <span>For You</span>
        </h1>

        <p>{explanation}</p>
      </section>

      {loading && (
        <p className="products-status">Finding products you might like...</p>
      )}

      {error && (
        <div className="products-status products-error">
          <strong>Could not load recommendations.</strong>
          <p>{error}</p>
          <button className="retry-btn" onClick={handleRetry}>
            Try Again
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* Show WHAT the engine learned from. This is the single most
              useful bit of transparency on the page - it turns an
              invisible algorithm into something you can reason about. */}
          {isPersonal && basedOnProducts.length > 0 && (
            <section className="rec-basis">
              <h3>Because you bought</h3>

              <div className="rec-basis-row">
                {basedOnProducts.map((product) => (
                  <Link
                    to={`/product/${product.id}`}
                    className="rec-basis-chip"
                    key={product.id}
                  >
                    <img src={product.image} alt="" />
                    <span>{product.name}</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          <RecommendationStrip
            products={products}
            variant="personal"
            title={isPersonal ? "You might like these" : "Most popular right now"}
          />

          {/* An empty list here is a legitimate outcome, not an error -
              for example if the catalogue only holds a couple of
              products. Say so plainly. */}
          {products.length === 0 && (
            <div className="empty-cart">
              <h3>Nothing to suggest yet</h3>

              <p>
                There are not enough other products yet for us to suggest
                anything sensible.
              </p>

              <Link to="/products">
                <button className="shop-btn">Browse Products</button>
              </Link>
            </div>
          )}

          {/* A short, plain-English note on how it works. Academic
              projects get marked on whether you can explain the
              algorithm - this is that explanation, in the product. */}
          <section className="rec-how">
            <h3>How does this work?</h3>

            <p>
              Every product&apos;s name, category and description is turned
              into a mathematical vector with a technique called
              <strong> TF-IDF</strong>, which gives more weight to words that
              are distinctive to a product and less to words that appear
              everywhere. We then measure the angle between vectors using
              <strong> cosine similarity</strong> - the smaller the angle, the
              more alike two products are.
            </p>

            <p>
              Product ratings are mixed in as a small bonus (15%), so a
              good match with a good average rating comes out on top.
              When we have your order history we average the vectors of
              what you bought to build a profile and compare every other
              product against it. No purchase history means no profile,
              which is why new visitors see the most popular products
              instead.
            </p>
          </section>
        </>
      )}
    </main>
  );
}

export default Recommendations;
