import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getProducts } from "../data/api";
import { useCart } from "../context/useCart";
import Stars from "./Stars";
import Reveal from "./Reveal";

// The categories that exist in the catalogue. Hard-coded rather than
// derived from the fetched products so the filter row does not jump
// around while the list is loading.
const CATEGORIES = ["Electronics", "Fashion", "Home"];

function Products() {
  const [searchParams, setSearchParams] = useSearchParams();

  const category = searchParams.get("category") || "";
  const searchFromUrl = searchParams.get("search") || "";

  // Reach the shared cart directly rather than taking a prop
  const { addItem } = useCart();

  const [justAdded, setJustAdded] = useState(null);
  const [addError, setAddError] = useState(null);

  // =========================
  // SEARCH
  // =========================
  //
  // Two pieces of state on purpose:
  //
  //   `searchInput` is what you are typing right now.
  //   `query` is what has actually been searched.
  //
  // They must be separate, or the list would reload on every single
  // keystroke. `searchInput` follows the URL so that arriving from a
  // link like /products?search=watch shows the term in the box.
  //
  // `searchInput` is stored alongside the URL value it was typed
  // against. When the URL changes underneath us - a link from the home
  // page, or the back button - the stored key no longer matches and the
  // box re-reads the URL on the spot during render. That keeps the two
  // in step without an effect, which matters because setting state
  // directly inside an effect causes an extra cascading render on every
  // URL change.
  const [searchInput, setSearchInput] = useState({
    key: searchFromUrl,
    value: searchFromUrl,
  });

  if (searchInput.key !== searchFromUrl) {
    setSearchInput({ key: searchFromUrl, value: searchFromUrl });
  }

  const typedSearch = searchInput.value;

  // `query` is what has actually been searched. The same keyed trick
  // applies: a URL that changes to a different term should re-run the
  // fetch, without needing an effect to notice.
  const [queryState, setQueryState] = useState({
    key: searchFromUrl,
    value: searchFromUrl,
  });

  if (queryState.key !== searchFromUrl) {
    setQueryState({ key: searchFromUrl, value: searchFromUrl });
  }

  const query = queryState.value;

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
  //
  // We send the search term to the server rather than filtering in the
  // browser. The backend already searches across both the name and the
  // description, which a client-side filter on the name alone could
  // never match. It also means this keeps working when the catalogue
  // grows beyond what is sensible to download.
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProducts() {
      try {
        setLoading(true);
        setError(null);

        const filters = {};

        if (query) filters.search = query;

        const data = await getProducts(filters);

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
  }, [query]);

  // The category filter stays in the browser. It is an exact match on
  // a field we already have, so a round trip would only add latency.
  const filteredProducts = category
    ? products.filter(
        (product) =>
          product.category.toLowerCase() === category.toLowerCase()
      )
    : products;

  // Searching fetches the whole category-agnostic set, so if a
  // category is also active we still want the heading to say so.
  const pageTitle = category
    ? category === "Home"
      ? "Home & Living"
      : category
    : "All Products";

  // =========================
  // CHANGE THE FILTERS
  // =========================
  const applySearch = (term) => {
    const clean = term.trim();

    // Update both at once: the applied query, and the box (which needs
    // its key set too, or the guard above would immediately undo the
    // typing by re-reading the old URL).
    setQueryState({ key: clean, value: clean });
    setSearchInput({ key: clean, value: clean });

    // Keep the URL honest, so the search can be linked and shared and
    // the back button behaves sensibly.
    const next = new URLSearchParams(searchParams);

    if (clean) {
      next.set("search", clean);
    } else {
      next.delete("search");
    }

    setSearchParams(next, { replace: true });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    applySearch(typedSearch);
  };

  const handleClearSearch = () => {
    applySearch("");
  };

  const handleCategory = (name) => {
    const next = new URLSearchParams(searchParams);

    if (name) {
      next.set("category", name);
    } else {
      next.delete("category");
    }

    setSearchParams(next, { replace: true });
  };

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

      {/* ================= SEARCH AND FILTERS ================= */}
      <section className="filter-bar">
        <form className="search-form" onSubmit={handleSubmit} role="search">
          <input
            className="search-input"
            type="search"
            value={typedSearch}
            onChange={(event) =>
              setSearchInput({
                key: searchInput.key,
                value: event.target.value,
              })
            }
            /* Kept short on purpose. The previous wording, "Search
               products by name or description", was long enough to
               be cut off mid-word on a phone, where the Search
               button takes most of the row. "Search products" fits
               at every width, and the aria-label below still
               announces the full explanation to screen readers. */
            placeholder="Search products"
            aria-label="Search products by name or description"
          />

          <button type="submit" className="search-btn">
            Search
          </button>

          {/* Only offered once there is something to clear, so the bar
              stays quiet when it has nothing to do. */}
          {(typedSearch || query) && (
            <button
              type="button"
              className="search-clear"
              onClick={handleClearSearch}
            >
              Clear
            </button>
          )}
        </form>

        <div className="filter-row">
          <div className="category-filter">
            <button
              type="button"
              className={`filter-chip ${category === "" ? "filter-chip-active" : ""}`}
              onClick={() => handleCategory("")}
            >
              All
            </button>

            {CATEGORIES.map((name) => (
              <button
                key={name}
                type="button"
                className={`filter-chip ${
                  category.toLowerCase() === name.toLowerCase()
                    ? "filter-chip-active"
                    : ""
                }`}
                onClick={() => handleCategory(name)}
              >
                {name === "Home" ? "Home & Living" : name}
              </button>
            ))}
          </div>

          {/* Say what is currently being shown. A searched list with
              no explanation is confusing. It sits at the end of the
              same row as the chips so it reads as a count of what the
              filters produced, not as another control. */}
          {!loading && !error && (
            <p className="filter-summary">
              {query
                ? `${filteredProducts.length} result${
                    filteredProducts.length === 1 ? "" : "s"
                  } for "${query}"`
                : `Showing ${filteredProducts.length} product${
                    filteredProducts.length === 1 ? "" : "s"
                  }`}
              {category && ` in ${category === "Home" ? "Home & Living" : category}`}
            </p>
          )}
        </div>
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

        {/* An empty result has two different causes, and they need
            different advice - so they get different messages. */}
        {!loading && !error && filteredProducts.length === 0 && (
          <div className="empty-results">
            <h3>No products found</h3>
            {query ? (
              <>
                <p>
                  Nothing matches &ldquo;{query}&rdquo;
                  {category
                    ? ` in ${category === "Home" ? "Home & Living" : category}`
                    : ""}
                  .
                </p>

                <button
                  type="button"
                  className="shop-btn"
                  onClick={handleClearSearch}
                >
                  Clear Search
                </button>
              </>
            ) : (
              <>
                <p>There are no products in this category yet.</p>

                <button
                  type="button"
                  className="shop-btn"
                  onClick={() => handleCategory("")}
                >
                  Show All Products
                </button>
              </>
            )}
          </div>
        )}

        {!loading && !error && (
          <div className="product-grid">
          {filteredProducts.map((product, index) => (
            /* Capped at 8 steps. A 36-item list with an uncapped
               stagger would leave the last card waiting four seconds,
               which reads as broken rather than as a flourish. Past
               the eighth the delay stops growing, so the tail of a
               long list arrives together. */
            <Reveal
              className="product-card"
              key={product.id}
              delay={Math.min(index, 8) * 70}
            >
              {/* Clicking the image or the name opens the full product
                  page, where the reviews live. */}
              <Link
                to={`/product/${product.id}`}
                className="product-image"
              >
                <img
                  src={product.image}
                  alt={product.name}
                />
              </Link>

              <div className="product-info">
                <small>
                  {product.category}
                </small>

                <Link
                  to={`/product/${product.id}`}
                  className="product-name-link"
                >
                  <h3>
                    {product.name}
                  </h3>
                </Link>

                <div className="card-rating">
                  <Stars value={product.rating_average || 0} size="sm" />

                  <span>
                    {product.rating_count > 0
                      ? `${product.rating_average} (${product.rating_count})`
                      : "No reviews"}
                  </span>
                </div>

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
            </Reveal>
          ))}
          </div>
        )}
      </section>
    </main>
  );
}

export default Products;
