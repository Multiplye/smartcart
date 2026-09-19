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
