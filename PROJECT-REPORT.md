# SmartCart — Project Report

An online marketplace with AI-based product recommendations.

**Module:** Bachelor of Information Technology — Final Project
**Stack:** React 19 + Vite · Flask · SQLite · Scikit-learn

---

## 1. What the project is

SmartCart is a working online shop where customers browse products, add
them to a cart, place Cash-on-Delivery orders and leave star ratings.
Its distinguishing feature is a recommendation engine that suggests
products based on what a customer has previously bought.

The shop is built around three user roles:

| Role | Can do |
|---|---|
| **Buyer** | Browse, shop, place orders, review what they have bought |
| **Seller** | Everything a buyer can, plus create and manage their own listings |
| **Admin** | Everything, plus manage accounts and see the whole catalogue |

---

## 2. Why these choices were made

### 2.1 Why content-based recommendation, not collaborative filtering

There are two common approaches to building a recommender.

**Collaborative filtering** ("people similar to you also bought…")
needs a large volume of interaction data. With a handful of users and
30 products, a co-occurrence matrix is almost entirely empty, and the
algorithm would produce nonsense or nothing.

**Content-based filtering** compares the *text describing a product*
against text describing what a customer has bought. It works from the
first customer onwards, because it only needs product descriptions —
not a crowd.

For a project of this size, content-based is the honest choice.

### 2.2 Why TF-IDF and cosine similarity

Every product's name, category and description is converted into a
numeric vector using **TF-IDF** (Term Frequency — Inverse Document
Frequency):

- **Term frequency** counts how often a word appears in one product.
- **Inverse document frequency** divides that by how common the word is
  across *all* products.

The effect: a distinctive word like *"mechanical"* carries a lot of
weight, while a word appearing in almost every description (*"product"*,
*"quality"*) is pushed towards zero. `stop_words="english"` removes
filler words outright, and `min_df=2` discards any term appearing in
only one product.

Similarity is then measured with **cosine similarity** — the cosine of
the angle between two vectors. This is preferred over Euclidean
distance because it measures *direction* rather than magnitude, so a
short description and a long one about the same topic still score as
similar.

The parameters used:

```python
TfidfVectorizer(
    stop_words="english",
    min_df=2,
    lowercase=True,
    ngram_range=(1, 2),
    sublinear_tf=True,
)
```

`ngram_range=(1, 2)` captures two-word phrases such as *"power bank"*,
which a single-word model would treat as unrelated terms. `sublinear_tf`
applies `1 + log(tf)`, stopping one term repeated many times from
dominating.

### 2.3 The rating blend

Text similarity alone ignores quality. The final score is therefore:

```
final = 0.85 × text_similarity + 0.15 × normalised_rating
```

Ratings are normalised to 0–1 with `(average − 1) / 4`, so 1 star → 0.0
and 5 stars → 1.0. A product with no reviews is treated as a neutral
0.5 rather than 0, so a new listing is not unfairly buried. Text
dominates deliberately: the blend should nudge good products up, not
let a popular irrelevance win.

### 2.4 The cold-start fallback

A brand-new visitor has no purchase history, so there is nothing to
build a taste profile from. Rather than showing an empty box, the
engine falls back to the highest-rated products, breaking ties on the
number of votes. The API reports which path it took, so the interface
can explain itself honestly.

---

## 3. System architecture

```
┌─────────────────────────────┐
│  React (Vite) :5173         │
│  • Routes (react-router)    │
│  • AuthContext / CartContext│
│  • fetch wrapper → api.js   │
└──────────────┬──────────────┘
               │ HTTP + X-User-Id header
┌──────────────▼──────────────┐
│  Flask :5000                │
│  • @roles_required decorator│
│  • Route groups by feature  │
│  • recommender.py           │
└──────┬───────────────┬──────┘
       │               │
┌──────▼──────┐  ┌─────▼──────────┐
│ SQLite      │  │ scikit-learn   │
│ 6 tables    │  │ TfidfVectorizer│
└─────────────┘  └────────────────┘
```

The backend is deliberately a **single `app.py`**. For a project this
size, splitting into blueprints would spread related logic across files
and make it harder to follow. The AI engine is the one exception — it
lives in `recommender.py`, because it is pure logic with no database or
HTTP concerns, and keeping it separate makes it independently testable.

---

## 4. Database design

Six tables.

### `user`
```
id, name, email, password_hash, role
```
Passwords are hashed with Werkzeug's `generate_password_hash`
(scrypt-based). The plain password is never stored, and `password_hash`
is never included in any API response — `user_to_dict()` deliberately
omits it.

### `product`
```
id, name, description, price, category, image, stock, seller_id → user.id
```
`seller_id` is **nullable on purpose**. The 30 seeded products have no
owner and behave as shop-owned stock that only an admin may edit. This
also matters practically: adding a `NOT NULL` column to a populated
table is impossible without a default.

### `cart_item`
```
id, user_id → user.id, product_id → product.id, quantity
UNIQUE (user_id, product_id)
```
The unique constraint means one row per user per product, enforced by
the database rather than by application code. Quantity is bumped
instead of a second row being inserted.

**No price is stored here.** The cart holds a reference to a product,
not a copy of its price. Storing the price would let a customer hold an
old price in their cart and check out at that price later.

### `order`
```
id, user_id → user.id, full_name, phone, address, city,
payment_method, total, status, created_at
```
Delivery details live on the **order**, not on the user, because an
address is a property of a delivery rather than of a person — the same
account may ship to different places.

### `order_item`
```
id, order_id → order.id, product_id, product_name, unit_price, quantity
```
This is the **snapshot pattern**. The product name and the price paid
are copied at the moment of purchase. If a seller later raises the
price or deletes the listing, existing order history is unaffected.

`product_id` is stored but is deliberately **not** a foreign key — the
order line must survive the product being deleted.

### `review`
```
id, user_id → user.id, product_id → product.id, rating, comment, created_at
UNIQUE (user_id, product_id)
```
One review per person per product, enforced by the database.

### Entity relationships

```
user ──< cart_item >── product
  │                       │
  │                       │
  ├──< order ──< order_item
  │                       │
  └──< review >───────────┘
```

---

## 5. Authentication and authorisation

### 5.1 How identity travels

The React app remembers the logged-in user and sends their id in an
`X-User-Id` request header on every protected call. The server then
loads the user **from the database** and reads their role.

This design has a deliberate consequence worth stating plainly: the
header alone grants nothing. A client sending `X-User-Id: 1` is not
trusted — the server looks up user 1 and uses whatever role the
database holds. Roles are therefore read fresh on every request, so a
role change takes effect immediately without requiring a re-login.

**Trade-off:** this is a session-style scheme suitable for a teaching
project. It is not JWT-based and would need to be replaced with signed
tokens before any real deployment, because a header can be forged by
anyone who can make an HTTP request.

### 5.2 The `@roles_required` decorator

```python
def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return {"error": "You must be logged in to do that."}, 401
            if user.role not in allowed_roles:
                return {"error": f"Your account is a '{user.role}' account. "
                                 f"This action needs one of: "
                                 f"{', '.join(allowed_roles)}."}, 403
            request.current_user = user
            return view(*args, **kwargs)
        return wrapped
    return decorator
```

The distinction between **401** (nobody is logged in) and **403** (you
are logged in, but not allowed) is maintained everywhere, and a test
asserts the two carry different messages so a frontend can tell the
user whether to log in or give up.

### 5.3 Three rules that protect the admin panel

Admin routes can demote accounts and delete them. Three guards prevent
an operator from locking everyone out of their own site:

1. An admin **cannot change their own role**.
2. An admin **cannot delete their own account**.
3. The **last remaining admin cannot be removed**.

Without these, one careless click could leave a system with no
administrator and no way back in through the interface.

### 5.4 Account deletion cleans up after itself

Deleting a user row naively would leave orphaned `order_item`,
`cart_item` and `review` rows pointing at an id that no longer exists,
breaking every subsequent join. The delete therefore runs inside one
transaction, in dependency order:

1. Delete their reviews
2. Delete their cart rows
3. Delete order lines, then the orders themselves
4. Set `seller_id = NULL` on their products — **not** delete them
5. Delete the user

Step 4 is the significant one. A seller's listings are handed back to
the shop rather than destroyed, so no customer's order history loses
its products. If any step fails, `rollback()` leaves the database
untouched.

---

## 6. API reference

### Products

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/products` | Public | List, with `?category=` and `?search=` |
| GET | `/api/products/<id>` | Public | One product |
| POST | `/api/products` | Seller, Admin | Create (owner taken from the session) |
| PUT | `/api/products/<id>` | Owner, Admin | Update |
| DELETE | `/api/products/<id>` | Owner, Admin | Delete |

### Reviews

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/products/<id>/reviews` | Public | Reviews + average |
| POST | `/api/products/<id>/reviews` | Logged in | Write one |
| PUT | `/api/reviews/<id>` | Author, Admin | Edit |
| DELETE | `/api/reviews/<id>` | Author, Admin | Delete |

Writing a review requires having **ordered** the product. Browsing is
not buying, so having it in the cart does not count.

### Cart

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/cart` | Logged in | Current cart with totals |
| POST | `/api/cart` | Logged in | Add or bump quantity |
| PUT | `/api/cart/<product_id>` | Logged in | Set quantity |
| DELETE | `/api/cart/<product_id>` | Logged in | Remove one |
| DELETE | `/api/cart` | Logged in | Empty the cart |

Every cart route returns the same shape — `{ items, count, total }` —
so the client can drop the response straight into state.

### Orders

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/orders` | Logged in | Check out |
| GET | `/api/orders` | Logged in | Own orders (`?status=`); sellers/admins see more |
| GET | `/api/orders/<id>` | Owner, Seller, Admin | One order |
| PUT | `/api/orders/<id>/status` | Seller, Admin | Advance status |
| DELETE | `/api/orders/<id>` | Owner, Seller, Admin | Cancel |

### Recommendations

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/products/<id>/recommendations` | Public | Similar products (`?limit=1..12`) |
| GET | `/api/recommendations` | Public | Personalised, or popular fallback |

### Admin

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/admin/users` | Admin | All accounts with order counts |
| PUT | `/api/admin/users/<id>/role` | Admin | Promote or demote |
| DELETE | `/api/admin/users/<id>` | Admin | Delete with full cleanup |
| GET | `/api/admin/stats` | Admin | Counts, revenue, orders by status |
| GET | `/api/admin/products` | Admin | Whole catalogue with owner names |

### Accounts

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/register` | Public | Create an account |
| POST | `/api/login` | Public | Log in |

---

## 7. Order status transitions

Statuses may not be skipped. The allowed moves are declared in one
place so the rule cannot drift between the API and the interface:

```
Pending ──▶ Confirmed ──▶ Shipped ──▶ Delivered
   │            │
   └────────────┴──────▶ Cancelled
```

Attempting an illegal move (for example `Delivered → Pending`) returns
a 400. The React order page mirrors this same table in a local
`NEXT_STATUS` constant, so it only ever offers valid buttons.

Cancelling an order **returns the stock** to each product, inside the
same transaction as the status change.

---

## 8. The recommendation engine in detail

### 8.1 Building the text

```python
def build_text(product):
    name = product.name or ""
    category = product.category or ""
    description = product.description or ""
    return " ".join([
        name,
        name,                                     # repeated on purpose
        f"category_{category.lower().replace(' ', '_')}",
        description,
    ])
```

Three deliberate decisions:

- **The name appears twice.** It is the most informative part of a
  listing, so repeating it raises its term weight.
- **The category is prefixed** with `category_`, so the word
  "Electronics" as a category cannot be confused with the same word
  appearing inside a description.
- **Empty fields are coerced to `""`** rather than `None`, because
  `TfidfVectorizer` would raise on a `None` value.

### 8.2 Two ways to query the engine

**Similar products** — compare one product against all others:

```python
similarities = cosine_similarity(target_vector, matrix).flatten()
```

**Personalised** — build a taste profile from purchase history:

```python
profile = matrix[purchased_rows].mean(axis=0)
profile = np.asarray(profile)
similarities = cosine_similarity(profile, matrix).flatten()
```

Averaging the vectors of everything a customer bought produces a single
point in the same space, representing their combined taste. Products
closest to that point are recommended. Items already purchased are
excluded, because recommending something the customer already owns is
useless.

### 8.3 The model is rebuilt on every request

Instead of caching the fitted vectorizer, it is refitted per request.
The catalogue holds 30 products, so fitting takes a few milliseconds.
Caching would introduce a stale-data problem — a product added by a
seller would not be recommendable until the cache expired — for no
measurable gain. This is a deliberate simplicity trade-off, and it is
the first thing that would need to change at a larger scale.

---

## 9. Testing

The backend has **seven test suites totalling 430 assertions, all
passing**:

| Suite | Checks | Covers |
|---|---|---|
| `test_auth.py` | 24 | Registration, login, hashing, role validation |
| `test_products.py` | 65 | CRUD, role guard, **ownership fencing**, spoofing |
| `test_cart.py` | 62 | Add, update, cap at stock, **cart privacy**, clearing |
| `test_orders.py` | 79 | Checkout, stock refusal, snapshots, status chain, cancellation |
| `test_reviews.py` | 63 | The "must have ordered" gate, one-per-person, averages |
| `test_recommendations.py` | 59 | Matrix shape, no self-recommendation, determinism, fallback |
| `test_admin.py` | 78 | **Everything an admin is NOT allowed to do** |

**430 assertions, 0 failures — verified by running the full set twice
in succession.**

### 9.1 Testing the AI, not just the plumbing

It is easy to write an endpoint that returns *something* and call it
working. The recommendation tests deliberately check whether the
*something* is sensible:

- A laptop stand must recommend a **mechanical keyboard**, not a random
  product.
- Suggestions must lean towards the categories a customer bought from.
- Products already purchased must never be suggested.
- The engine must exclude everything when the customer owns the whole
  catalogue, rather than falling over.
- The same input must give the same output twice (determinism).

### 9.2 The admin suite mostly tests refusals

Because these routes can delete accounts and change roles, most of
`test_admin.py` is spent trying to do things that should be forbidden:

- A buyer and a seller are refused on **all five** admin routes.
- A logged-out request gets 401, not 403 — and the two carry different
  messages.
- An admin cannot change their own role.
- An admin cannot delete themselves.
- The last admin cannot be removed.
- An invented role name returns 400.
- After deleting a user: no orphaned order lines remain anywhere in the
  database, and the deleted user's old credentials stop working
  entirely.

### 9.3 Test isolation — a bug found by running the suites twice

Running the suites once looked fine. Running them a second time
exposed a genuine problem worth documenting, because finding it
required questioning a green result.

Two suites were **permanently mutating the demo catalogue**:

- `test_admin.py` put real product #1 in a cart, placed an order for
  two of it, and never restored the stock. Each run silently reduced it
  by two.
- `test_recommendations.py` bought a real product to build a purchase
  history and also never restored it.

Eventually product #1 reached **stock 0**. That then made a *different*
suite fail — `test_recommendations.py` could not place its test order
at all — and the failure looked like a bug in the recommender, when the
real cause was a side effect from a test that had run earlier.

Two fixes:

1. Both suites now create their **own throwaway product** to order, so
   the real catalogue is never touched.
2. Both remember the stock they consume and **restore it during
   cleanup**, and `test_admin.py` now asserts that no catalogue product
   moved at all:

```python
moved = [
    (p.id, p.name, p.stock)
    for p in Product.query.filter(Product.id <= 30).all()
    if p.stock != 10
]
check("no catalogue product had its stock changed", len(moved) == 0, moved)
```

A test is allowed to create and destroy its own fixtures. It must never
quietly damage the data it is supposed to be checking.

### 9.4 Live HTTP walkthroughs

Five scripts exercise the real server over a socket rather than through
Flask's test client, so they prove the whole stack rather than one
layer:

- `live_demo_checkout.py` — stock falls 6 → 4, cart empties, status chain
- `live_demo_reviews.py` — the 403 for a non-buyer, the 409 duplicate
- `live_demo_admin.py` — every admin guard, over HTTP
- `demo_recommendations.py` — **the personalisation proof in section 11**
- `seed_demo_data.py` — builds the demo shop

`live_demo_admin.py` also verifies at the end that no catalogue product's
stock moved, so this class of bug cannot return unnoticed.

---

## 10. A finding worth reporting: descriptions determine results

This is the most useful thing learned during the project.

The 30 seeded products initially shared three filler sentences
(*"a reliable electronic product for everyday use"*). Running the engine
produced a clear failure: Wireless Headphones, Wireless Mouse and
Wireless Earbuds all scored a text similarity of **exactly 1.0000**.

**Why:** after `min_df=2` removed every word that did not appear in at
least two documents, those three products had *no distinctive terms
left*. Their feature vectors were identical.

**The fix:** `improve_descriptions.py` replaced the filler with 30
genuine, individually-written descriptions. The number of distinct
features in the matrix rose from **33 to 88**, ties disappeared, and
recommendations became meaningfully better — notably reaching across
categories (Laptop Stand → Desk Lamp is a sensible pairing that the
old data could never have produced).

**The lesson:** a content-based recommender is only ever as good as the
text you feed it. The algorithm was not wrong; the data was. This is a
realistic and instructive outcome, and it is exactly the kind of
finding a project report should contain.

---

## 11. Evidence that personalisation works

After running `seed_demo_data.py`, three customers with different
tastes received genuinely different recommendations:

**Aarav** — bought Wireless Headphones, Mechanical Keyboard, Power Bank:

| Match | Product | Category |
|---|---|---|
| 34% | USB-C Charger | Electronics |
| 30% | Wireless Earbuds | Electronics |
| 30% | Running Shoes | Fashion |
| 29% | Laptop Stand | Electronics |
| 26% | Wireless Mouse | Electronics |

**Priya** — bought Scented Candle, Kitchen Organizer, Desk Lamp:

| Match | Product | Category |
|---|---|---|
| 36% | Coffee Maker | Home |
| 27% | Decorative Plant | Home |
| 21% | Mechanical Keyboard | Electronics |
| 20% | Storage Basket | Home |
| 15% | Laptop Stand | Electronics |

**Bikash** — bought Running Shoes, Classic Backpack, Sunglasses:

| Match | Product | Category |
|---|---|---|
| 28% | Mechanical Keyboard | Electronics |
| 27% | Classic Sneakers | Fashion |
| 16% | Wrist Watch | Fashion |
| 15% | Scented Candle | Home |
| 15% | Wireless Headphones | Electronics |

Aarav's list is four-fifths electronics. Priya's is four-fifths home,
led by a coffee maker — a strong match for someone who bought a kitchen
organizer. Bikash's is led by footwear and accessories.

**The control:** a logged-out visitor and an account with no orders
both received the *identical* popularity list. Same input, same
output — confirming the personalised results above are caused by
purchase history rather than by randomness.

Note that the fallback list reports **0%** for every item. That is
honest rather than a bug: a popularity ranking makes no similarity
comparison, so it has no score to report.

---

## 12. Known limitations

Stated plainly, because a report that claims no weaknesses is not a
credible one.

1. **Authentication is not production-grade.** An `X-User-Id` header
   can be forged. Real deployment needs signed tokens (JWT) or server
   sessions with secure cookies.

2. **No payment processing.** Cash on Delivery only, as scoped.

3. **The model is refitted per request.** Correct and fast at 30
   products; it would need caching and possibly a narrower candidate
   set at thousands.

4. **No stemming or lemmatisation.** "Chargers" and "charger" are
   treated as different terms. Adding a stemmer would improve matching
   on sparse descriptions.

5. **Recommendations ignore browsing behaviour.** Only purchased
   products inform the profile. Someone who browses twenty keyboards
   but buys nothing gets no benefit from it.

6. **No pagination.** `GET /api/products` returns the whole catalogue.

7. **The admin panel has no audit log.** Role changes and deletions
   happen with no record of who did what.

8. **Cart stock is checked at two moments.** The cart caps quantity at
   available stock, and checkout re-checks every item before committing.
   Stock can still fall between those two points under concurrency, so
   a small race remains.

---

## 13. What would come next

In priority order:

1. Replace header auth with JWT, including token expiry.
2. Add browsing history to the taste profile as a second signal.
3. Cache the fitted vectorizer, invalidated when a product changes.
4. Add an audit log for admin actions.
5. Paginate the product listing.
6. Evaluate the recommender properly — precision@k against a held-out
   set of purchases — rather than the spot checks used here.

---

## 14. How to run it

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/pip install flask flask-cors flask-sqlalchemy scikit-learn numpy

./venv/Scripts/python import_products.py     # load the 30 products
./venv/Scripts/python app.py                 # serve on :5000
```

### Frontend

```bash
cd smartcart/smartcart        # note: nested - this is the inner folder
npm install
npm run dev                   # serve on :5173
```

### Demo data and tests

```bash
cd backend
./venv/Scripts/python seed_demo_data.py          # realistic demo shop
./venv/Scripts/python demo_recommendations.py    # prove personalisation
./venv/Scripts/python test_products.py           # and the five others
```

### Demo accounts

All use the password `demo1234`.

| Email | Role | Notes |
|---|---|---|
| `aarav@demo.smartcart` | buyer | Electronics buyer — personal list |
| `priya@demo.smartcart` | buyer | Home buyer — different list |
| `bikash@demo.smartcart` | buyer | Fashion buyer — third list |
| `sunita@demo.smartcart` | seller | Can list products |
| `admin@demo.smartcart` | admin | Full admin panel access |

---

## 15. Summary

SmartCart implements a complete marketplace — authentication with
three roles, product management with ownership enforcement, a
persistent cart, transactional Cash-on-Delivery checkout, order status
workflow, and verified-customer reviews — plus a content-based
recommendation engine built on TF-IDF and cosine similarity.

The parts worth highlighting:

- **Recommendations demonstrably differ per customer**, with a control
  case proving the difference comes from purchase history.
- **A real data-quality failure was found and fixed**, and the cause
  understood — not merely patched.
- **A test-isolation bug was found by running the suites twice**, which
  is the difference between a green result and a trustworthy one.
- **430 automated assertions pass, twice in succession**, and the admin
  suite is mostly spent proving what is *forbidden*.
- **Correctness is enforced at the database level** where possible —
  unique constraints on cart rows and reviews, snapshotting of order
  prices — rather than relying on application code to behave.
- **The test suites leave the database exactly as they found it**,
  verified by an explicit assertion on the catalogue.
