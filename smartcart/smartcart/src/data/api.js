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

/**
 * Shared helper for POST requests.
 *
 * The backend reports problems as { "error": "message" } with a non-OK
 * status code. This turns that into a normal JavaScript Error, so the
 * calling component can just catch it and show err.message.
 */
async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server sent an unexpected response.");
  }

  if (!response.ok) {
    // Use the backend's own message when it gave us one.
    throw new Error(data.error || `Server responded with status ${response.status}`);
  }

  return data;
}

/**
 * Fetch every product from the Flask backend.
 * Returns an array of product objects.
 * Throws an Error if the server is not reachable.
 */
export async function getProducts() {
  const response = await fetch(`${API_BASE_URL}/api/products`);

  if (!response.ok) {
    throw new Error(`Server responded with status ${response.status}`);
  }

  return response.json();
}

/**
 * Create a new account.
 * Returns { message, user } where user = { id, name, email, role }.
 */
export async function register({ name, email, password, role }) {
  return postJson("/api/register", { name, email, password, role });
}

/**
 * Log in with an existing account.
 * Returns { message, user } where user = { id, name, email, role }.
 */
export async function login({ email, password }) {
  return postJson("/api/login", { email, password });
}

export { API_BASE_URL };
