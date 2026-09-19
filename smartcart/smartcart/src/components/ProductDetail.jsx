import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { useCart } from "../context/useCart";

import {
  getProduct,
  getProductRecommendations,
  getProductReviews,
  createReview,
  updateReview,
  deleteReview,
} from "../data/api";

import Stars from "./Stars";
import RecommendationStrip from "./RecommendationStrip";

function ProductDetail() {
  const { productId } = useParams();

  const { user, isLoggedIn, isAdmin } = useAuth();
  const { addItem } = useCart();

  // The product itself
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // The reviews
  const [reviews, setReviews] = useState([]);
  const [summary, setSummary] = useState({ average: 0, count: 0 });

  // "You might also like" - filled in by the second effect below
  const [suggestions, setSuggestions] = useState([]);

  // The review form
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [notice, setNotice] = useState(null);

  // Which review (if any) is being edited
  const [editingReviewId, setEditingReviewId] = useState(null);

  // A short confirmation on the Add to Cart button
  const [justAdded, setJustAdded] = useState(false);

  // =========================
  // LOAD PRODUCT AND REVIEWS
  // =========================
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const [productData, reviewData] = await Promise.all([
          getProduct(productId),
          getProductReviews(productId),
        ]);

        if (cancelled) return;

        setProduct(productData);
        setReviews(reviewData.reviews);
        setSummary(reviewData.summary);
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
  }, [productId]);

  // =========================
  // LOAD "YOU MIGHT ALSO LIKE"
  // =========================
  //
  // Separate from the product fetch above on purpose. If the
  // recommender is ever slow or fails, the product page must still
  // work - the suggestions are a bonus, not a requirement. So this
  // effect swallows its own errors and just leaves the list empty.
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await getProductRecommendations(productId, 4);

        // The endpoint always answers, but the recommender list can be
        // empty (a one-product catalogue has nothing to compare with),
        // so guard rather than assume.
        if (!cancelled) setSuggestions(data.recommendations || []);
      } catch {
        if (!cancelled) setSuggestions([]);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [productId]);

  // My own review, if I have written one
  const myReview = isLoggedIn
    ? reviews.find((review) => review.user_id === user?.id)
    : null;

  // =========================
  // ADD TO CART
  // =========================
  const handleAddToCart = async () => {
    try {
      await addItem(product);
      setJustAdded(true);

      window.setTimeout(() => setJustAdded(false), 1500);
    } catch (err) {
      setFormError(err.message);
    }
  };

  // =========================
  // SUBMIT A REVIEW
  // =========================
  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setNotice(null);

    if (rating < 1) {
      setFormError("Please choose a star rating first.");
      return;
    }

    setSaving(true);

    try {
      const data = editingReviewId
        ? await updateReview(editingReviewId, { rating, comment })
        : await createReview(productId, { rating, comment });

      // Refresh the list and the summary from the server's answer
      const fresh = await getProductReviews(productId);

      setReviews(fresh.reviews);
      setSummary(fresh.summary);
      setNotice(data.message);

      // Reset the form
      setRating(0);
      setComment("");
      setEditingReviewId(null);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // =========================
  // EDIT / DELETE
  // =========================
  const startEditing = (review) => {
    setEditingReviewId(review.id);
    setRating(review.rating);
    setComment(review.comment || "");
    setFormError(null);
    setNotice(null);

    document
      .getElementById("review-form")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  const cancelEditing = () => {
    setEditingReviewId(null);
    setRating(0);
    setComment("");
    setFormError(null);
  };

  const handleDeleteReview = async (review) => {
    const sure = window.confirm("Delete your review? This cannot be undone.");
    if (!sure) return;

    setFormError(null);
    setNotice(null);

    try {
      const data = await deleteReview(review.id);

      const fresh = await getProductReviews(productId);

      setReviews(fresh.reviews);
      setSummary(fresh.summary);
      setNotice(data.message);

      if (editingReviewId === review.id) cancelEditing();
    } catch (err) {
      setFormError(err.message);
    }
  };

  // =========================
  // LOADING / ERROR
  // =========================
  if (loading) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>PRODUCT</p>
          <h1>Loading...</h1>
        </section>
      </main>
    );
  }

  if (error || !product) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>PRODUCT</p>
          <h1>Not Found</h1>

          <div className="products-status products-error">
            <strong>We could not load that product.</strong>
            <p>{error || "It may have been removed."}</p>
          </div>

          <Link to="/products" className="learn-btn">
            Back to Products
          </Link>
        </section>
      </main>
    );
  }

  // Can this user review? They must have ordered it - which we cannot
  // know from here, so we let them try and show the server's answer.
  const canWriteReview = isLoggedIn && !myReview;

  // =========================
  // THE PAGE
  // =========================
  return (
    <main className="all-products-page">
      <section className="products-page-header">
        <p>{product.category.toUpperCase()}</p>
        <h1>{product.name}</h1>

        <Link to="/products" className="learn-btn">
          Back to Products
        </Link>
      </section>

      <section className="collection-section">
        <div className="detail-wrapper">

          {/* ============ LEFT: the image ============ */}
          <div className="detail-image">
            <img src={product.image} alt={product.name} />
          </div>

          {/* ============ RIGHT: the facts ============ */}
          <div className="detail-info">
            <div className="detail-rating-row">
              <Stars value={summary.average} />

              <span>
                {summary.count > 0
                  ? `${summary.average} out of 5 (${summary.count} review${
                      summary.count === 1 ? "" : "s"
                    })`
                  : "No reviews yet"}
              </span>
            </div>

            <p className="detail-price">
              Rs. {product.price.toLocaleString()}
            </p>

            <p className="detail-description">{product.description}</p>

            <div className="detail-stock">
              {product.stock > 0 ? (
                <span className="in-stock">
                  In stock — {product.stock} available
                </span>
              ) : (
                <span className="out-of-stock">Out of stock</span>
              )}
            </div>

            {formError && (
              <div className="products-status products-error">
                <p>{formError}</p>
              </div>
            )}

            <button
              className="add-cart-btn detail-add-btn"
              onClick={handleAddToCart}
              disabled={product.stock < 1}
            >
              {product.stock < 1
                ? "Out of Stock"
                : justAdded
                  ? "Added to Cart"
                  : "Add to Cart"}
            </button>
          </div>
        </div>

        {/* ============ REVIEWS ============ */}
        <div className="reviews-section">
          <h2 className="reviews-heading">
            Customer Reviews
            {summary.count > 0 && (
              <span className="reviews-heading-count">
                {summary.count}
              </span>
            )}
          </h2>

          {notice && (
            <div className="products-status products-success">{notice}</div>
          )}

          {/* ---------- the review form ---------- */}
          {canWriteReview && (
            <div className="review-form-wrapper" id="review-form">
              <h3>Write a review</h3>

              <p className="review-hint">
                You can review this product because you have ordered it.
              </p>

              <form className="review-form" onSubmit={handleReviewSubmit}>
                <div className="review-rating-input">
                  <label>Your rating</label>

                  <Stars
                    value={rating}
                    interactive
                    onSelect={setRating}
                  />
                </div>

                <div className="form-group">
                  <label>Your comment (optional)</label>
                  <textarea
                    rows="3"
                    placeholder="What did you think of it?"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                </div>

                <div className="manage-form-actions">
                  <button type="submit" className="auth-btn" disabled={saving}>
                    {saving ? "Saving..." : "Submit Review"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ---------- your existing review ---------- */}
          {myReview && editingReviewId !== myReview.id && (
            <div className="review-card review-mine">
              <div className="review-head">
                <div>
                  <strong>Your review</strong>
                  <Stars value={myReview.rating} size="sm" />
                </div>

                <div className="review-actions">
                  <button
                    type="button"
                    className="manage-edit-btn"
                    onClick={() => startEditing(myReview)}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="manage-delete-btn"
                    onClick={() => handleDeleteReview(myReview)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              {myReview.comment && <p>{myReview.comment}</p>}
            </div>
          )}

          {/* ---------- an editing form ---------- */}
          {editingReviewId && (
            <div className="review-form-wrapper" id="review-form">
              <h3>Edit your review</h3>

              <form className="review-form" onSubmit={handleReviewSubmit}>
                <div className="review-rating-input">
                  <label>Your rating</label>
                  <Stars value={rating} interactive onSelect={setRating} />
                </div>

                <div className="form-group">
                  <label>Your comment (optional)</label>
                  <textarea
                    rows="3"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                </div>

                <div className="manage-form-actions">
                  <button type="submit" className="auth-btn" disabled={saving}>
                    {saving ? "Saving..." : "Save Changes"}
                  </button>

                  <button
                    type="button"
                    className="manage-cancel-btn"
                    onClick={cancelEditing}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ---------- logged out nudge ---------- */}
          {!isLoggedIn && (
            <p className="review-hint">
              Log in to leave a review. You can review products you have
              ordered.
            </p>
          )}

          {/* ---------- the list ---------- */}
          {reviews.filter((review) => review.id !== myReview?.id).length === 0 &&
            !myReview && (
              <p className="products-status">
                There are no reviews for this product yet.
              </p>
            )}

          <div className="review-list">
            {reviews
              .filter((review) => review.id !== myReview?.id)
              .map((review) => (
                <div className="review-card" key={review.id}>
                  <div className="review-head">
                    <div>
                      <strong>{review.reviewer_name}</strong>
                      <Stars value={review.rating} size="sm" />
                    </div>

                    {isAdmin && (
                      <button
                        type="button"
                        className="manage-delete-btn"
                        onClick={() => handleDeleteReview(review)}
                      >
                        Delete
                      </button>
                    )}
                  </div>

                  {review.comment && <p>{review.comment}</p>}
                </div>
              ))}
          </div>
        </div>

        {/* ==========================================
            AI RECOMMENDATIONS
            ==========================================
            The backend scores every other product against this one
            using TF-IDF vectors and cosine similarity. We re-render by
            key so React throws the strip away and rebuilds it when you
            move from one product page to another. */}
        <RecommendationStrip
          key={productId}
          products={suggestions}
          variant="similar"
          title="You might also like"
          subtitle="Chosen by comparing this product's description with the rest of the catalogue."
        />
      </section>
    </main>
  );
}

export default ProductDetail;
