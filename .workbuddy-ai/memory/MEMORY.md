# SmartCart — Project Notes

BIT academic project. Online marketplace with AI recommendations.
Full run instructions: `HOW-TO-RUN.md`. Auth details: `AUTH-GUIDE.md`.

## Stack
- React 19 + Tailwind, Vite 8, react-router-dom v7
- Flask + Flask-CORS + Flask-SQLAlchemy, SQLite (`backend/instance/smartcart.db`)
- **SQLite is deliberate**: one synopsis section says MySQL, but the methodology
  says SQLite and that is what is built. Change only if the supervisor insists.
- AI (pending): Scikit-learn, content-based, TF-IDF + cosine similarity
- Excluded by synopsis: payments, delivery tracking, mobile app, analytics.
  Ordering is Cash-on-Delivery.

## Folder layout — ONLY the innermost folder runs the app
```
smartcart/                    <- root
├── backend/                  <- Flask API  (python app.py)
└── smartcart/                <- Tailwind deps only
    └── smartcart/            <- ✅ React app (npm run dev)
```
**Rule for the user: the correct folder contains `vite.config.js`.**
Guard-rail `package.json` files sit in the three wrong folders; **do not delete
them**. npm walks UP the tree for `package.json`. Do not restructure the nesting
unless the user asks.

## Gotchas
- Vite 8 binds IPv6-only (`[::1]:5173`) — use `localhost`, not `127.0.0.1`.
- Flask `debug=True` spawns a reloader CHILD process that does the real serving,
  so killing the netstat PID may leave the port answering. Test with
  `socket.bind()`, not netstat.
## Conventions
- All backend calls go through `src/data/api.js`; components never hardcode the
  URL. Its `postJson()` helper converts the backend's `{error}` responses into
  thrown JS Errors.
- Backend uses `product_to_dict()` / `user_to_dict()`, not repeated dict literals.
- SQLite tables are the source of truth; `src/data/products.js` is only a
  historical reference.
- `Product`: `id, name, description, price, category, image, stock`. Categories:
  Electronics, Fashion, Home (10 each, 30 total). `description` is
  `nullable=False`, so the import script builds a placeholder per category.
- `User`: `id, name, email(unique), password_hash, role` (buyer|seller|admin).
  Emails lowercased, so login is case-insensitive.

## API
`GET /` · `GET|POST /api/products` · `POST /api/register` (201|400|409) ·
`POST /api/login` (200|400|401)

## Auth decisions (built)
- Session-style, NOT JWT (user's choice). Passwords hashed with werkzeug
  `generate_password_hash` (scrypt) — Flask bundles it.
- `password_hash` must NEVER appear in a response; `user_to_dict()` omits it.
- Login returns the SAME error for bad password and unknown email (prevents user
  enumeration). Keep that behaviour.
- Frontend auth is `src/context/` across 3 files: `AuthProvider.jsx` (component),
  `authContextInstance.js` (context object), `useAuth.js` (hook). The split is
  REQUIRED by eslint react-refresh rules — do not merge them.
- Read via `useAuth()`; provided in `src/main.jsx`.
- Intentional limitation: role comes from the signup dropdown, so anyone can pick
  "seller". Lock down with the admin panel.

## Roadmap
Done: Flask/SQLite setup, Product model + GET/POST, 30 products migrated,
products page on the API, **authentication** (User table, register, login,
hashed passwords, React form wired, session in localStorage).

Pending: role enforcement, product CRUD (PUT/DELETE), per-user cart, orders,
reviews/ratings, AI recommendations, admin panel, frontend wiring, docs.

Build one module at a time and test before moving on — the user is a beginner.
