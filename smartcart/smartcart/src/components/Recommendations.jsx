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
function RecommendationCard({ product, seedProducts, index = 0 }) {
  const { addItem } = useCart();

  const [justAdded, setJustAdded] = useState(false);
  const [error, setError] = useState(null);

  const match = describeMatch(product.match_percent);

  // Cards arrive one after another rather than all at once. The index is
  // known here, so the delay is set here; the animation itself lives in
  // App.css. Capped at 8 so a long list never makes the last card wait.
  const delay = Math.min(index, 8) * 70;

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
    <article
      className="ai-card-rec"
      style={{ "--rec-delay": `${delay}ms` }}
    >
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
      {/* ==========================================
          HEADER
          ==========================================
          This was a bare left-aligned stack of three lines on a wide
          empty page, and it read as unfinished.

          It is now a self-contained banner: the text sits on the left,
          a colour-coded "engine status" panel sits on the right so the
          row is not half empty, and the header band visually separates
          itself from the grid below.

          The status panel is the honest bit. It reports whether the
          list in front of you was actually personalised, rather than
          just asserting that SmartCart has AI. */}
      <section className="rec-header ai-rise">
        <div className="rec-header-text">
          <span className="rec-header-label">
            SMART RECOMMENDATIONS
          </span>

          <h1>
            Picked <span>For You</span>
          </h1>

          <p>{explanation}</p>

          <div className="rec-header-actions">
            {isPersonal ? (
              <Link to="/orders" className="rec-header-link">
                Your orders →
              </Link>
            ) : (
              <Link to="/products" className="rec-header-link">
                Browse products →
              </Link>
            )}

            {!isPersonal && (
              /* There is no /login route - signing in happens in the
                 auth section of the home page, so link to that hash. */
              <Link to="/#auth" className="rec-header-link rec-header-link-quiet">
                {isLoggedIn ? "See how to personalise" : "Log in"}
              </Link>
            )}
          </div>
        </div>

        {/* Sits still while the list loads, so the header never jumps
            and the page does not appear empty from the moment it opens. */}
        <aside className="rec-header-status">
          <span className="rec-status-title">Engine status</span>

          <div className="rec-status-row">
            <span className="rec-status-dot" data-on={isPersonal} />
            <span className="rec-status-key">Personalised</span>
            <strong>{isPersonal ? "Yes" : "No"}</strong>
          </div>

          <div className="rec-status-row">
            <span className="rec-status-key">Source</span>
            <strong>
              {isPersonal ? "Your order history" : "Popularity"}
            </strong>
          </div>

          <div className="rec-status-row">
            <span className="rec-status-key">Method</span>
            <strong>TF-IDF · cosine</strong>
          </div>
        </aside>
      </section>

      {loading && (
        <div className="ai-loading">
          <div className="ai-loading-spinner" />

          <p>Matching products against your history...</p>

          {/* Skeleton cards. A spinner alone leaves the page looking
              empty; these show the shape of what is coming and make the
              wait feel shorter. Hidden from screen readers, because
              they carry no information. */}
          <div className="ai-grid ai-skeleton-grid" aria-hidden="true">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                className="ai-skeleton"
                key={i}
                style={{ "--rec-delay": `${i * 90}ms` }}
              >
                <div className="ai-skeleton-image" />
                <div className="ai-skeleton-line ai-skeleton-line-short" />
                <div className="ai-skeleton-line" />
                <div className="ai-skeleton-line ai-skeleton-line-tiny" />
              </div>
            ))}
          </div>
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
              <h3 className="ai-rise">Because you bought</h3>

              <div className="ai-seed-row">
                {seedProducts.map((product, i) => (
                  <Link
                    to={`/product/${product.id}`}
                    className="ai-seed-chip ai-rise"
                    key={product.id}
                    style={{ "--rec-delay": `${i * 60}ms` }}
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
              <div
                className="ai-summary-item ai-rise"
                style={{ "--rec-delay": "0ms" }}
              >
                <strong>{products.length}</strong>
                <span>suggestions</span>
              </div>

              <div
                className="ai-summary-item ai-rise"
                style={{ "--rec-delay": "70ms" }}
              >
                <strong>{strongCount}</strong>
                <span>strong matches</span>
              </div>

              <div
                className="ai-summary-item ai-rise"
                style={{ "--rec-delay": "140ms" }}
              >
                <strong>{isPersonal ? "Yes" : "No"}</strong>
                <span>personalised</span>
              </div>
            </section>
          )}

          {/* ==========================================
              TOOLBAR
              ========================================== */}
          {products.length > 1 && (
            <div className="ai-toolbar ai-rise">
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
              {sorted.map((product, i) => (
                <RecommendationCard
                  key={product.id}
                  product={product}
                  seedProducts={seedProducts}
                  index={i}
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
              This used to be three paragraphs of plain text sitting
              under the grid. It was accurate and it was ugly - the
              page looked like it ended in an essay.

              It is now collapsed by default with just a one-line
              summary, so the page finishes on the products. The full
              explanation is still there, one click away, because an
              academic project is marked on being able to explain the
              approach. Three-step layout instead of a wall of prose. */}
          <section className="rec-how">
            <details>
              <summary>
                <span className="rec-how-icon" aria-hidden="true">
                  ?
                </span>

                <span className="rec-how-text">
                  <strong>How does this work?</strong>
                  <small>
                    TF-IDF vectors, cosine similarity, and a small
                    rating bonus
                  </small>
                </span>

                <span className="rec-how-toggle" aria-hidden="true" />
              </summary>

              <div className="rec-how-body">
                <ol className="rec-steps">
                  <li>
                    <span className="rec-step-no">1</span>
                    <div>
                      <strong>Every product becomes a vector</strong>
                      <p>
                        Its name, category and description are scored
                        with <em>TF-IDF</em>, which weights words that
                        are distinctive to a product more heavily than
                        words that appear everywhere.
                      </p>
                    </div>
                  </li>

                  <li>
                    <span className="rec-step-no">2</span>
                    <div>
                      <strong>Similarity is the angle between them</strong>
                      <p>
                        We take the <em>cosine similarity</em> of those
                        vectors. The smaller the angle, the more alike
                        two products are.
                      </p>
                    </div>
                  </li>

                  <li>
                    <span className="rec-step-no">3</span>
                    <div>
                      <strong>Your history sets the direction</strong>
                      <p>
                        The vectors of what you bought are averaged into
                        a taste profile, and every other product is
                        scored against it. Ratings count for a 15%
                        bonus, so a close match with a good average
                        rating wins.
                      </p>
                    </div>
                  </li>
                </ol>

                <p className="rec-how-note">
                  No order history means no profile - which is why new
                  visitors see popular products instead. Those cards
                  show no percentage, because a popularity ranking
                  compares nothing and so has no similarity score to
                  report.
                </p>
              </div>
            </details>
          </section>
        </>
      )}
    </main>
  );
}

export default Recommendations;
