import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getProducts,
  createProduct,
  updateProduct,
  deleteProduct,
} from "../data/api";

import { useAuth } from "../context/useAuth";

// An empty form, used when adding a new product
const EMPTY_FORM = {
  name: "",
  description: "",
  price: "",
  category: "",
  image: "",
  stock: "",
};

const CATEGORIES = ["Electronics", "Fashion", "Home"];

function ManageProducts() {
  const { user, isLoggedIn, isSeller, isAdmin } = useAuth();

  const canManage = isSeller || isAdmin;

  // The product list
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  // The form
  const [form, setForm] = useState(EMPTY_FORM);

  // When set, the form is editing this product instead of adding a new one
  const [editingId, setEditingId] = useState(null);

  // Feedback for the user
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [saving, setSaving] = useState(false);

  // An admin manages everything; a seller only manages their own listings.
  const ownsThis = (product) => {
    if (isAdmin) return true;
    return product.seller_id === user?.id;
  };

  // A seller sees their own listings; an admin sees the whole catalogue.
  const visibleProducts = isAdmin
    ? products
    : products.filter((product) => product.seller_id === user?.id);

  const shopOwnedCount = products.filter(
    (product) => product.seller_id === null
  ).length;

  // =========================
  // LOAD PRODUCTS
  // =========================
  async function loadProducts() {
    try {
      setLoadError(null);
      const data = await getProducts();
      setProducts(data);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!canManage) {
      // Nothing to fetch. No state to update either - see `showLoading`.
      return;
    }

    // Anything that calls setState has to happen asynchronously, so React
    // is not asked to re-render in the middle of this effect.
    let cancelled = false;

    (async () => {
      try {
        const data = await getProducts();
        if (!cancelled) {
          setProducts(data);
          setLoadError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [canManage]);

  // Only show the loading message when we are actually allowed to load
  const showLoading = canManage && loading;

  // =========================
  // FORM HELPERS
  // =========================
  const updateField = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setError(null);
  };

  /** Load a product into the form for editing. */
  const startEditing = (product) => {
    // The buttons are already disabled for products this user does not
    // own, but the backend would refuse anyway - this is just a clear
    // message instead of a confusing 403.
    if (!ownsThis(product)) {
      setError(
        product.seller_id === null
          ? "That product belongs to the shop, so only an admin can edit it."
          : "That product belongs to a different seller."
      );
      return;
    }

    setForm({
      name: product.name,
      description: product.description,
      price: String(product.price),
      category: product.category,
      image: product.image || "",
      stock: String(product.stock),
    });

    setEditingId(product.id);
    setError(null);
    setSuccess(null);

    // Scroll the form into view so the user sees what happened
    document
      .getElementById("product-form")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  // =========================
  // SUBMIT (add or edit)
  // =========================
  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setSuccess(null);
    setSaving(true);

    // Send numbers as numbers, so the backend does not have to guess
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      price: Number(form.price),
      category: form.category.trim(),
      image: form.image.trim() || null,
      stock: Number(form.stock || 0),
    };

    try {
      if (editingId) {
        const data = await updateProduct(editingId, payload);
        setSuccess(data.message);
      } else {
        const data = await createProduct(payload);
        setSuccess(data.message);
      }

      resetForm();
      await loadProducts();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // =========================
  // DELETE
  // =========================
  const handleDelete = async (product) => {
    if (!ownsThis(product)) {
      setSuccess(null);
      setError(
        product.seller_id === null
          ? "That product belongs to the shop, so only an admin can delete it."
          : "That product belongs to a different seller."
      );
      return;
    }

    const sure = window.confirm(
      `Delete "${product.name}"? This cannot be undone.`
    );

    if (!sure) return;

    setError(null);
    setSuccess(null);

    try {
      const data = await deleteProduct(product.id);
      setSuccess(data.message);

      // If we were editing this product, clear the form
      if (editingId === product.id) {
        resetForm();
      }

      await loadProducts();
    } catch (err) {
      setError(err.message);
    }
  };

  // =========================
  // NOT ALLOWED HERE
  // =========================
  if (!canManage) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>SELLER TOOLS</p>
          <h1>Manage Products</h1>

          <div className="products-status products-error">
            {isLoggedIn ? (
              <>
                <strong>This area is for sellers.</strong>
                <p>
                  Your account is a buyer account, so it cannot add or edit
                  products. Create a seller account to list products.
                </p>
              </>
            ) : (
              <>
                <strong>Please log in.</strong>
                <p>
                  You need a seller account to manage products. Log in or
                  register below.
                </p>
              </>
            )}
          </div>

          <Link to="/" className="learn-btn">
            Back to Home
          </Link>
        </section>
      </main>
    );
  }

  // =========================
  // THE SELLER PAGE
  // =========================
  return (
    <main className="all-products-page">
      <section className="products-page-header">
        <p>SELLER TOOLS</p>

        <h1>Manage Products</h1>

        <span>
          Add new products, edit the ones you have, or remove them.
        </span>

        <Link to="/products" className="learn-btn">
          View Shop
        </Link>
      </section>

      <section className="collection-section">

        {/* ================= MESSAGES ================= */}
        {error && (
          <div className="products-status products-error">
            <strong>Something went wrong.</strong>
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="products-status products-success">
            {success}
          </div>
        )}

        {/* ================= FORM ================= */}
        <div className="manage-form-wrapper" id="product-form">
          <h2>
            {editingId
              ? `Editing: ${form.name || "product"}`
              : "Add a new product"}
          </h2>

          <form className="manage-form" onSubmit={handleSubmit}>

            <div className="form-group">
              <label>Product Name</label>
              <input
                type="text"
                placeholder="e.g. Wireless Headphones"
                value={form.name}
                onChange={updateField("name")}
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                rows="3"
                placeholder="Describe the product"
                value={form.description}
                onChange={updateField("description")}
                required
              />
            </div>

            <div className="manage-form-row">
              <div className="form-group">
                <label>Price (Rs.)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="2500"
                  value={form.price}
                  onChange={updateField("price")}
                  required
                />
              </div>

              <div className="form-group">
                <label>Stock</label>
                <input
                  type="number"
                  min="0"
                  placeholder="10"
                  value={form.stock}
                  onChange={updateField("stock")}
                  required
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <select
                  value={form.category}
                  onChange={updateField("category")}
                  required
                >
                  <option value="">Choose one</option>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Image URL (optional)</label>
              <input
                type="url"
                placeholder="https://example.com/photo.jpg"
                value={form.image}
                onChange={updateField("image")}
              />
            </div>

            <div className="manage-form-actions">
              <button
                type="submit"
                className="auth-btn"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editingId
                    ? "Save Changes"
                    : "Add Product"}
              </button>

              {editingId && (
                <button
                  type="button"
                  className="manage-cancel-btn"
                  onClick={resetForm}
                >
                  Cancel
                </button>
              )}
            </div>

          </form>
        </div>

        {/* ================= EXISTING PRODUCTS ================= */}
        <h2 className="manage-list-heading">
          {isAdmin
            ? `All products (${products.length})`
            : `Your products (${visibleProducts.length})`}
        </h2>

        {isAdmin && shopOwnedCount > 0 && (
          <p className="manage-note">
            {shopOwnedCount} of these belong to the shop rather than to a
            seller account. Only an admin can edit those.
          </p>
        )}

        {showLoading && <p className="products-status">Loading products...</p>}

        {loadError && (
          <div className="products-status products-error">
            <strong>Could not load products.</strong>
            <p>{loadError}</p>
          </div>
        )}

        {!showLoading && !loadError && visibleProducts.length === 0 && (
          <div className="products-status">
            {isAdmin ? (
              "There are no products in the shop yet."
            ) : (
              <>
                <strong>You have not listed anything yet.</strong>
                <p>Use the form above to add your first product.</p>
              </>
            )}
          </div>
        )}

        {!showLoading && !loadError && visibleProducts.length > 0 && (
          <div className="manage-list">
            {visibleProducts.map((product) => (
              <div className="manage-row" key={product.id}>
                <img
                  src={product.image}
                  alt={product.name}
                  className="manage-thumb"
                />

                <div className="manage-row-info">
                  <strong>{product.name}</strong>
                  <small>
                    {product.category} · Rs.{" "}
                    {product.price.toLocaleString()} · {product.stock} in stock
                  </small>

                  {isAdmin && (
                    <small className="manage-owner-tag">
                      {product.seller_id === null
                        ? "Owned by: the shop"
                        : `Owned by: seller #${product.seller_id}`}
                    </small>
                  )}
                </div>

                <div className="manage-row-actions">
                  <button
                    type="button"
                    className="manage-edit-btn"
                    onClick={() => startEditing(product)}
                    disabled={!ownsThis(product)}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="manage-delete-btn"
                    onClick={() => handleDelete(product)}
                    disabled={!ownsThis(product)}
                  >
                    Delete
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

export default ManageProducts;
