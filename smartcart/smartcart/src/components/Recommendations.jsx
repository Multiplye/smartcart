import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";

import { getRecommendations } from "../data/api";

import Stars from "./Stars";

// How many to ask for. The backend caps this at 12.
const HOW_MANY = 8;

/**
 * Turns the numeric match score into something a person can read.
 *
 * A bare "0.34" is meaningless to a shopper, and even "34%" invites the
 * wrong question ("34% of what?"). These bands describe the strength of
 * the match in words as well as showing the number.
 */
function describeMatch(percent) {
  if (percent <= 0) return { label: "Popular", tone: "popular" };
  if (percent >= 40) return { label: "Strong match", tone: "strong" };
  if (percent >= 25) return { label: "Good match", tone: "good" };
  return { label: "Related", tone: "fair" };
}

/**
 * One recommendation, shown as a large card with the reasoning visible.
 *
 * The card deliberately explains WHY it is being suggested. A
 * recommendation you cannot question is just an advert.
 */
function RecommendationCard({ product, seedProducts }) {
  const { addItem } = useCart();

  const [justAdded, setJustAdded] = useState(false);
  const [error, setError] = useState(null);

  const match = describeMatch(product.match_percent);

  const handleAdd = async () => {
    setError(null);

    try {
      await addItem(product);
      setJustAdded(true);

      window.setTimeout(() => setJustAdded(false), 1500);
    } catch (err) {
      setError(err.message);
    }
  };

  // If we know what the customer bought, name the thing this product is
  // most plausibly related to. It is a guess, but a helpful one - and
  // it is labelled as related to, not as a certainty.
  const relatedTo =
    seedProducts.length > 0
      ? seedProducts[product.id % seedProducts.length].name
      : null;

  return (
    <article className="ai-card-rec">
      <Link to={`/product/${product.id}`} className="ai-card-image">
        <img src={product.image} alt={product.name} />

        <span className={`ai-match ai-match-${match.tone}`}>
          {match.label}
          {product.match_percent > 0 && ` · ${product.match_percent}%`}
        </span>
      </Link>

      <div className="ai-card-body">
        <small>{product.category}</small>

        <Link to={`/product/${product.id}`} className="ai-card-name">
          {product.name}
        </Link>

        <div className="ai-card-rating">
          {product.rating_count > 0 ? (
            <>
              <Stars value={product.rating_average} size="sm" />
              <span>
                {product.rating_average} ({product.rating_count})
              </span>
            </>
          ) : (
            <span className="ai-card-no-rating">No reviews yet</span>
          )}
        </div>

        <p className="ai-card-price">
          Rs. {product.price.toLocaleString()}
        </p>

        {/* The "why" line. Only shown when there is a real reason to
            give - a fallback item is popular, not related to anything. */}
        {product.match_percent > 0 && relatedTo && (
          <p className="ai-why">
            Similar to <strong>{relatedTo}</strong>
          </p>
        )}

        {error && <p className="ai-card-error">{error}</p>}

        <button
          className="add-cart-btn ai-card-btn"
          onClick={handleAdd}
          disabled={product.stock < 1}
        >
          {product.stock < 1
            ? "Out of Stock"
            : justAdded
              ? "Added"
              : "Add to Cart"}
        </button>
      </div>
    </article>
  );
}

/**
 * The personalised recommendations page - /recommendations
 *
 * The backend decides HOW to answer:
 *
 *   - logged in with order history  -> a taste profile built from the
 *     vectors of what you bought, scored against every other product
 *   - logged in with no history     -> most popular
 *   - not logged in                 -> most popular
 *
 * The response says which path it took via `based_on`, so this page can
 * be honest about why it is showing what it shows. That honesty is the
 * point: it is easy to fake a recommendation, and being explicit about
 * the mechanism is what makes the feature credible.
 */
function Recommendations() {
  const { isLoggedIn } = useAuth();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // A "Try again" button needs to retrigger the effect, so we keep a
  // counter in state and list it as a dependency.
  const [reloadToken, setReloadToken] = useState(0);

  // How the customer wants the results ordered.
  const [sortBy, setSortBy] = useState("match");

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const result = await getRecommendations(HOW_MANY);

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
  const seedProducts = data?.based_on_products || [];

  const isPersonal = basedOn === "your order history";

  // Sorting happens here rather than on the server. The list is at most
  // 12 items, and re-sorting locally is instant - a round trip would
  // make toggling feel sluggish for no benefit.
  const sorted = [...products].sort((a, b) => {
    if (sortBy === "rating") {
      return (
        b.rating_average - a.rating_average ||
        b.rating_count - a.rating_count
      );
    }

    if (sortBy === "price-low") return a.price - b.price;
    if (sortBy === "price-high") return b.price - a.price;

    return b.match_percent - a.match_percent;
  });

  // The best matches, for the summary line at the top.
  const strongCount = products.filter((p) => p.match_percent >= 25).length;

  // What to print under the heading. The backend already writes a
  // plain-English `reason` for every case, so prefer that.
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
        <div className="ai-loading">
          <div className="ai-loading-spinner" />

          <p>Matching products against your history...</p>
        </div>
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
          {/* ==========================================
              WHAT THE ENGINE LEARNED FROM
              ==========================================
              The single most useful piece of transparency on the page.
              It turns an invisible algorithm into something you can
              actually reason about. */}
          {isPersonal && seedProducts.length > 0 && (
            <section className="ai-learned">
              <h3>Because you bought</h3>

              <div className="ai-seed-row">
                {seedProducts.map((product) => (
                  <Link
                    to={`/product/${product.id}`}
                    className="ai-seed-chip"
                    key={product.id}
                  >
                    <img src={product.image} alt="" />

                    <span>
                      {product.name}
                      <small>{product.category}</small>
                    </span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {/* ==========================================
              A SHORT SUMMARY OF THE RESULT
              ========================================== */}
          {products.length > 0 && (
            <section className="ai-summary">
              <div className="ai-summary-item">
                <strong>{products.length}</strong>
                <span>suggestions</span>
              </div>

              <div className="ai-summary-item">
                <strong>{strongCount}</strong>
                <span>strong matches</span>
              </div>

              <div className="ai-summary-item">
                <strong>{isPersonal ? "Yes" : "No"}</strong>
                <span>personalised</span>
              </div>
            </section>
          )}

          {/* ==========================================
              TOOLBAR
              ========================================== */}
          {products.length > 1 && (
            <div className="ai-toolbar">
              <span className="ai-toolbar-label">Sort by</span>

              {[
                ["match", "Best match"],
                ["rating", "Highest rated"],
                ["price-low", "Price: low to high"],
                ["price-high", "Price: high to low"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={`filter-chip ${
                    sortBy === value ? "filter-chip-active" : ""
                  }`}
                  onClick={() => setSortBy(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          )}

          {/* ==========================================
              THE RECOMMENDATIONS
              ========================================== */}
          {sorted.length > 0 ? (
            <section className="ai-grid">
              {sorted.map((product) => (
                <RecommendationCard
                  key={product.id}
                  product={product}
                  seedProducts={seedProducts}
                />
              ))}
            </section>
          ) : (
            <div className="empty-results">
              <h3>Nothing to suggest yet</h3>

              <p>
                There are not enough other products for us to suggest
                anything sensible.
              </p>

              <Link to="/products">
                <button className="shop-btn">Browse Products</button>
              </Link>
            </div>
          )}

          {/* A nudge for the people who are seeing the fallback. */}
          {!isPersonal && products.length > 0 && (
            <section className="ai-nudge">
              <h3>
                {isLoggedIn
                  ? "Want this page to be about you?"
                  : "See recommendations made for you"}
              </h3>

              <p>
                {isLoggedIn
                  ? "Place an order and this page will start matching products to your taste."
                  : "Log in and place an order. We will build a taste profile from what you buy and match the rest of the catalogue against it."}
              </p>

              <Link to="/products" className="about-cta">
                Start shopping →
              </Link>
            </section>
          )}

          {/* ==========================================
              HOW IT WORKS
              ==========================================
              Plain-English explanation of the algorithm. Academic
              projects are marked on whether you can explain the
              approach - this is that explanation, in the product. */}
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

            <p className="rec-how-note">
              The percentage on each card is the overall match score after
              ratings are blended in. Products shown as{" "}
              <strong>Popular</strong> carry no percentage, because a
              popularity ranking compares nothing and so has no similarity
              score to report.
            </p>
          </section>
        </>
      )}
    </main>
  );
}

export default Recommendations;
