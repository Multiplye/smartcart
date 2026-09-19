// =========================
// Backend API helper
// =========================
//
// All communication with the Flask backend lives here, so components
// never have to know the URL or the fetch details.
//
// Start the backend first:
//   cd backend
//   .\venv\Scripts\Activate.ps1
//   python app.py
// Then it is available at http://127.0.0.1:5000

const API_BASE_URL = "http://127.0.0.1:5000";

// =========================
// Who is making the request?
// =========================
//
// Protected routes (adding, editing and deleting products) need to know
// which user is asking, so the backend can check their role.
//
// The logged-in user is kept in localStorage by AuthProvider. Rather
// than pass the user into every single call, this module reads it when
// building the request.
//
// We only ever send the user's ID. The backend looks the user up and
// reads the role from the database, so editing this value in the browser
// cannot grant extra permissions.

const STORAGE_KEY = "smartcart_user";

function currentUserId() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return null;

    const user = JSON.parse(saved);
    return user?.id ?? null;
  } catch {
    return null;
  }
}

/** Headers for every request, including the user id when logged in. */
function buildHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };

  const userId = currentUserId();
  if (userId !== null) {
    headers["X-User-Id"] = String(userId);
  }

  return headers;
}

/**
 * Shared request helper.
 *
 * The backend reports problems as { "error": "message" } with a non-OK
 * status code. This turns that into a normal JavaScript Error, so the
 * calling component can just catch it and show err.message.
 */
async function requestJson(path, { method = "GET", body } = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: buildHeaders(),
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // fetch() itself failed - the server is probably not running
    throw new Error(
      "Could not reach the server. Is the Flask backend running?"
    );
  }

  // A 204 has no body to parse
  if (response.status === 204) {
    return null;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server sent an unexpected response.");
  }

  if (!response.ok) {
    // Use the backend's own message when it gave us one.
    throw new Error(
      data.error || `Server responded with status ${response.status}`
    );
  }

  return data;
}

// =========================
// Products
// =========================

/**
 * Fetch products.
 * Optional filters: { category: "Electronics", search: "watch" }
 * Returns an array of product objects.
 */
export async function getProducts(filters = {}) {
  const params = new URLSearchParams();

  if (filters.category) params.set("category", filters.category);
  if (filters.search) params.set("search", filters.search);

  const query = params.toString();
  const path = query ? `/api/products?${query}` : "/api/products";

  return requestJson(path);
}

/** Fetch one product by id. */
export async function getProduct(productId) {
  return requestJson(`/api/products/${productId}`);
}

/** Add a product. Needs a seller or admin account. */
export async function createProduct(product) {
  return requestJson("/api/products", { method: "POST", body: product });
}

/** Edit a product. Needs a seller or admin account. */
export async function updateProduct(productId, changes) {
  return requestJson(`/api/products/${productId}`, {
    method: "PUT",
    body: changes,
  });
}

/** Delete a product. Needs a seller or admin account. */
export async function deleteProduct(productId) {
  return requestJson(`/api/products/${productId}`, { method: "DELETE" });
}

// =========================
// Recommendations (the AI)
// =========================
//
// Two flavours, and the difference matters:
//
//   getProductRecommendations(id)  - "people looking at this also like..."
//                                    Pure text similarity. Works for
//                                    visitors who are not logged in.
//                                    Answer: { product_id, based_on:
//                                    "product similarity", fallback,
//                                    recommendations: [...] }
//
//   getRecommendations()           - personalised. Reads your order
//                                    history and builds a taste profile
//                                    from it. Falls back to the most
//                                    popular products if you are new.
//                                    Answer: { based_on, reason,
//                                    personalised, based_on_products?,
//                                    recommendations: [...] }
//
// Each item carries match_score (0..1), match_percent (an integer,
// friendlier to show a person) and text_similarity (the raw cosine
// score before ratings are blended in).

/** "You might also like" for one product. Public - no login needed. */
export async function getProductRecommendations(productId, limit) {
  const params = new URLSearchParams();

  if (limit) params.set("limit", limit);

  const query = params.toString();
  const path = `/api/products/${productId}/recommendations`;

  return requestJson(query ? `${path}?${query}` : path);
}

/** Personalised picks for the logged-in user, or popular ones for a guest. */
export async function getRecommendations(limit) {
  const params = new URLSearchParams();

  if (limit) params.set("limit", limit);

  const query = params.toString();
  const path = "/api/recommendations";

  return requestJson(query ? `${path}?${query}` : path);
}

// =========================
// Admin
// =========================
//
// Every one of these needs an admin account. The backend checks the
// role in the database on each request, so hiding these buttons in the
// UI is a convenience, not the security boundary.

/** Every account, newest first, with an order count each. */
export async function getAdminUsers() {
  return requestJson("/api/admin/users");
}

/** Promote or demote somebody. role is "buyer" | "seller" | "admin". */
export async function setUserRole(userId, role) {
  return requestJson(`/api/admin/users/${userId}/role`, {
    method: "PUT",
    body: { role },
  });
}

/** Delete an account along with their cart, orders and reviews. */
export async function deleteUser(userId) {
  return requestJson(`/api/admin/users/${userId}`, { method: "DELETE" });
}

/** Counts for the top of the dashboard. */
export async function getAdminStats() {
  return requestJson("/api/admin/stats");
}

/** The whole catalogue, including who owns each listing. */
export async function getAdminProducts() {
  return requestJson("/api/admin/products");
}

// =========================
// Cart
// =========================
//
// The cart lives on the server, tied to the logged-in user. Every one
// of these returns the same shape:
//
//   { message?, items: [...], count: 3, total: 5000 }
//
// so the caller can just drop the new values straight into state.

/** Fetch the logged-in user's cart. */
export async function getCart() {
  return requestJson("/api/cart");
}

/** Add a product to the cart (or bump its quantity). */
export async function addCartItem(productId, quantity = 1) {
  return requestJson("/api/cart", {
    method: "POST",
    body: { product_id: productId, quantity },
  });
}

/** Set an item's quantity. Passing 0 removes it. */
export async function setCartItemQuantity(productId, quantity) {
  return requestJson(`/api/cart/${productId}`, {
    method: "PUT",
    body: { quantity },
  });
}

/** Remove one product from the cart. */
export async function removeCartItem(productId) {
  return requestJson(`/api/cart/${productId}`, { method: "DELETE" });
}

/** Empty the whole cart. */
export async function clearCart() {
  return requestJson("/api/cart", { method: "DELETE" });
}

// =========================
// Orders
// =========================

/**
 * Turn the current cart into an order.
 * Needs the delivery details:
 *   { full_name, phone, address, city }
 */
export async function placeOrder(deliveryDetails) {
  return requestJson("/api/orders", {
    method: "POST",
    body: deliveryDetails,
  });
}

/**
 * List orders.
 *
 * What you get back depends on your role:
 *   buyer  -> only your own orders
 *   seller -> orders containing your products
 *   admin  -> every order
 *
 * Optional filter: { status: "Pending" }
 */
export async function getOrders(filters = {}) {
  const params = new URLSearchParams();

  if (filters.status) params.set("status", filters.status);

  const query = params.toString();
  const path = query ? `/api/orders?${query}` : "/api/orders";

  return requestJson(path);
}

/** Fetch one order. 403 if it is not yours. */
export async function getOrder(orderId) {
  return requestJson(`/api/orders/${orderId}`);
}

/** Move an order to the next stage. Sellers and admins only. */
export async function updateOrderStatus(orderId, status) {
  return requestJson(`/api/orders/${orderId}/status`, {
    method: "PUT",
    body: { status },
  });
}

/** Cancel an order and return the stock. */
export async function cancelOrder(orderId) {
  return requestJson(`/api/orders/${orderId}`, { method: "DELETE" });
}

// =========================
// Reviews
// =========================

/**
 * Read a product's reviews. Open to everyone, no login needed.
 * Returns { product_id, summary: { average, count }, reviews: [...] }
 */
export async function getProductReviews(productId) {
  return requestJson(`/api/products/${productId}/reviews`);
}

/** Add a review. You must have ordered the product. */
export async function createReview(productId, { rating, comment }) {
  return requestJson(`/api/products/${productId}/reviews`, {
    method: "POST",
    body: { rating, comment },
  });
}

/** Edit your own review. Send only the fields you want to change. */
export async function updateReview(reviewId, { rating, comment }) {
  const body = {};

  if (rating !== undefined) body.rating = rating;
  if (comment !== undefined) body.comment = comment;

  return requestJson(`/api/reviews/${reviewId}`, {
    method: "PUT",
    body,
  });
}

/** Delete your own review. */
export async function deleteReview(reviewId) {
  return requestJson(`/api/reviews/${reviewId}`, { method: "DELETE" });
}

// =========================
// Accounts
// =========================

/**
 * Create a new account.
 * Returns { message, user } where user = { id, name, email, role }.
 */
export async function register({ name, email, password, role }) {
  return requestJson("/api/register", {
    method: "POST",
    body: { name, email, password, role },
  });
}

/**
 * Log in with an existing account.
 * Returns { message, user } where user = { id, name, email, role }.
 */
export async function login({ email, password }) {
  return requestJson("/api/login", {
    method: "POST",
    body: { email, password },
  });
}

export { API_BASE_URL };
