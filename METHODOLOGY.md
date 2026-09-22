# SmartCart — Proposed Methodology / System Approach

**Project:** SmartCart — an online marketplace with AI-based product recommendations
**Technology:** Python (Flask), React, SQLite, Scikit-learn

---

## 1. Overview of the approach

SmartCart was built using an **incremental, test-driven development
methodology**. Rather than designing the whole system on paper and then
implementing it in one pass, the project was divided into small,
independently verifiable milestones. Each milestone was implemented,
tested in isolation, and only then connected to the rest of the system.

This approach was chosen for three practical reasons:

1. **Fault localisation.** When something breaks in a system built in
   one pass, the cause could be anywhere. When functionality is added
   one slice at a time, a failure is almost always in the slice just
   added.

2. **Continuous verification.** Every layer has an executable check
   attached to it — 430 automated backend assertions, plus a browser
   walkthrough that drives the real user journey. A regression is
   caught at the moment it is introduced, not at final testing.

3. **Honest handling of the AI component.** Machine-learning behaviour
   is difficult to predict from reading code. Building the recommender
   early and testing its *output quality* — not merely that it returned
   a result — allowed the algorithm and the underlying data to be
   corrected while changes were still cheap.

The methodology follows a **four-phase Software Development Life Cycle**:
requirements analysis, system design, implementation with continuous
testing, and evaluation.

---

## 2. Phase 1 — Requirements analysis

The functional requirements were derived from what an online marketplace
actually has to do, and were grouped into five areas:

| Area | Requirement |
|---|---|
| **Accounts** | Register, log in, and operate in one of three roles — buyer, seller, admin |
| **Catalogue** | Browse, search, and filter products by category |
| **Transactions** | Maintain a cart, check out, and track order status |
| **Reviews** | Rate and review products, but only those actually purchased |
| **Recommendation** | Suggest relevant products to each user |

Two non-functional requirements shaped the design significantly:

- **The shop must work with no purchase history.** A new marketplace has
  no "other people bought this" data, so a recommendation strategy that
  depends on it would return nothing on day one.
- **Every user must only be able to reach their own data.** A cart,
  an order, and a seller's product listings are all private.

Both of these later became direct influences on the algorithm choice
(Section 4) and on the testing strategy (Section 7).

---

## 3. Phase 2 — System design

### 3.1 Three-tier architecture

The system is designed as three separated tiers:

```
        ┌─────────────────────────────┐
        │  PRESENTATION TIER          │
        │  React + Vite (port 5173)   │
        │  Components, routing, state │
        └──────────────┬──────────────┘
                       │  HTTP + JSON
                       │  (fetch, X-User-Id header)
        ┌──────────────▼──────────────┐
        │  APPLICATION TIER           │
        │  Flask REST API (port 5000) │
        │  30 routes, 3 role guards   │
        └──────────────┬──────────────┘
                       │  SQLAlchemy ORM
        ┌──────────────▼──────────────┐
        │  DATA TIER                  │
        │  SQLite (smartcart.db)      │
        │  6 tables                   │
        └─────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  RECOMMENDATION ENGINE      │
        │  Scikit-learn TF-IDF +      │
        │  cosine similarity          │
        └─────────────────────────────┘
```

**Why this separation matters.** The frontend never touches the database,
and the backend never renders HTML. This means the recommendation engine
can be tested without a browser, the API can be tested without a UI, and
the two tiers can be deployed independently. It also means a fault is
attributable to a specific tier.

### 3.2 Data model

Six entities were identified, with relationships chosen to preserve
historical accuracy:

```
User ──1:N──> Product        (a seller owns listings)
User ──1:N──> CartItem ──N:1──> Product
User ──1:N──> Order ──1:N──> OrderItem
User ──1:N──> Review  ──N:1──> Product
```

| Table | Purpose | Notable design decision |
|---|---|---|
| `user` | Accounts | Stores `password_hash`, never a password. `role` is validated against a fixed list. |
| `product` | Listings | `seller_id` attributes ownership, enforced on every write. |
| `cart_item` | Basket | Scoped by `user_id` so carts cannot leak. |
| `order` | Placed orders | Stores delivery details and a computed `total` at purchase time. |
| `order_item` | Order lines | **Copies** `product_name` and `unit_price` rather than referencing the product. |
| `review` | Ratings | One per user per product, gated on a matching purchase. |

The `order_item` decision is worth explaining, because it looks like
duplication. It is deliberate: if a seller later edits a price or
renames a product, a historical order must still show what the customer
actually paid for. Referencing the live product would silently rewrite
past invoices.

### 3.3 Interface design

The tiers communicate over a **REST API using JSON**. The API was
designed resource-first:

| Resource | Endpoints | Purpose |
|---|---|---|
| `/api/products` | GET, POST | List and create |
| `/api/products/<id>` | GET, PUT, DELETE | Read, update, delete one |
| `/api/cart` | GET, POST, PUT, DELETE | Manage the basket |
| `/api/orders` | GET, POST, DELETE | Place, list, cancel |
| `/api/reviews` | GET, POST, PUT, DELETE | Manage reviews |
| `/api/recommendations` | GET | AI suggestions |
| `/api/admin/*` | — | Role management |

Identity travels in an **`X-User-Id` request header**, and the server
re-reads the user's role from the database on every request. The role is
never trusted from the client, so a buyer cannot promote themselves by
editing a request.

---

## 4. Phase 3 — Algorithm selection (the AI component)

This is the core technical decision of the project.

### 4.1 The problem

The system must answer: *given this product (or this customer), what
should be suggested next?*

Two standard strategies exist:

| Strategy | How it works | Why it was **not** chosen |
|---|---|---|
| **Collaborative filtering** | "People who bought X also bought Y" | Needs substantial purchase history. On a new shop it returns nothing — the *cold-start problem*. |
| **Content-based filtering** | Compare what the products themselves say | — **Chosen.** Works from day one; requires only product text. |

**Selected approach: content-based recommendation using TF-IDF
vectorisation with cosine similarity.**

### 4.2 How the algorithm works

**Step 1 — Build a text representation of each product.** The product
name, category, and description are combined into one block of text. The
name is included twice, because it is the most informative field, and
the category is prefixed (`category_electronics`) so products in the
same category share a token even when their wording differs.

**Step 2 — Vectorise with TF-IDF.** Each product becomes a numerical
vector across the full vocabulary:

- **TF (term frequency)** — a word frequent in *this* product matters
  more for it.
- **IDF (inverse document frequency)** — but a word appearing in *every*
  product carries no distinguishing information and is pushed towards
  zero.

So "headphones" acquires a high weight, while "product" acquires almost
none. The vectoriser is configured with `stop_words="english"`,
`min_df=2` (ignore words unique to one product — they cannot link
anything), `ngram_range=(1,2)` (capture two-word phrases such as
"wireless headphones"), and `sublinear_tf=True`.

**Step 3 — Score with cosine similarity.** Each product is now a
direction in high-dimensional space. Cosine similarity measures the
**angle** between two vectors, not the distance between their endpoints.
This matters: a short description and a long one can still be about the
same thing, and cosine ignores the difference in length. The result
runs from 0 (unrelated) to 1 (identical).

**Step 4 — Blend in the rating.** Pure text similarity cannot tell that
one product is more popular than an equally-worded one, so the final
score combines both signals:

```
final_score = 0.85 × text_similarity + 0.15 × normalised_rating
```

The rating is **normalised across the candidate set** before blending,
otherwise its raw scale (1–5) would dominate a similarity value that
typically sits between 0 and 1.

**Step 5 — Personalise.** For a returning customer, a "taste profile" is
built by averaging the TF-IDF vectors of everything they have bought.
Recommendations are the products closest to that combined vector, with
already-purchased items excluded.

### 4.3 Handling the cold start

A new user has no history, so the personalised engine has nothing to
work from. Rather than returning an empty list, the system **falls back
to popular products**, ranked by rating and review count. This is
implemented as an explicit, documented fallback rather than an error
state — the user always sees something useful.

### 4.4 Why the model is rebuilt rather than saved

The TF-IDF matrix is rebuilt on each request instead of being persisted.
At 30 products this takes a few milliseconds. Caching it would
introduce an invalidation problem — *when exactly does the matrix become
stale?* — for no measurable benefit at this scale. This is a conscious
trade-off that would be revisited for a large catalogue.

---

## 5. Phase 3 — Implementation strategy

Implementation proceeded in vertical slices. Each slice cut through all
three tiers, so every milestone produced something demonstrable:

| Slice | Delivered | Verified by |
|---|---|---|
| 1 | Database models and schema | Model relationships and constraints |
| 2 | Account registration and login | Password hashing, role validation |
| 3 | Product CRUD with ownership rules | Sellers cannot edit others' listings |
| 4 | Cart operations | Stock limits, cart privacy |
| 5 | Checkout and order lifecycle | Stock deduction, price snapshots |
| 6 | Reviews with the purchase gate | Only buyers who ordered can review |
| 7 | Recommendation engine | Output *quality*, not just output presence |
| 8 | Admin panel | Refusals — what an admin must **not** do |
| 9 | Frontend integration | Real user journey in a browser |

This ordering was intentional: each slice depends only on the ones
before it, so the system was never in a half-built state where nothing
could be tested.

---

## 6. Security approach

Three principles were applied throughout:

**1. Passwords are hashed, never stored.** `generate_password_hash` and
`check_password_hash` (Werkzeug) are used on registration and login. The
plaintext password exists only inside the request handler and is never
written to the database.

**2. Roles are enforced on the server, per request.** A `@roles_required`
decorator reads the user's role from the database on every call. The
frontend hides buttons a user should not see, but that is presentation
only — the API refuses the request regardless of what the client sends.

**3. Ownership is checked, not assumed.** A seller may edit a product
only if `seller_id` matches their own id. This rule is applied
consistently across update and delete, and is directly tested — including
attempts to spoof another seller's identity in the request body.

**4. Errors never leak internals.** Custom error handlers for 400, 404,
405 and 500 return JSON. The 500 handler deliberately returns no
exception detail, because a stack trace in an HTTP response exposes
internal file paths and query text.

---

## 7. Testing methodology

Testing was treated as part of implementation, not a separate phase
afterwards.

### 7.1 Layer 1 — Automated backend assertions

**Seven suites, 430 assertions, all passing.**

| Suite | Assertions | Focus |
|---|---|---|
| `test_auth.py` | 24 | Registration, login, hashing, role validation |
| `test_products.py` | 65 | CRUD, role guards, ownership fencing, spoofing |
| `test_cart.py` | 62 | Add, update, stock cap, cart privacy |
| `test_orders.py` | 79 | Checkout, stock refusal, snapshots, status chain |
| `test_reviews.py` | 63 | Purchase gate, one-per-person, averages |
| `test_recommendations.py` | 59 | Matrix shape, determinism, no self-recommendation |
| `test_admin.py` | 78 | Everything an admin is **not** permitted to do |

Two design choices in this layer are worth highlighting:

- **The AI is tested on quality, not just function.** It is easy to
  write an endpoint that returns *something* and call it working. These
  tests assert that a laptop stand recommends a keyboard rather than a
  random item, that purchased products are never re-suggested, and that
  identical input produces identical output.

- **The admin suite mostly tests refusals.** Because these routes can
  delete accounts and alter roles, the majority of the assertions
  attempt operations that must be forbidden — a buyer and seller
  refused on all five admin routes, an admin unable to change their own
  role, the last remaining admin protected from removal.

- **Suites are self-cleaning and were run twice in succession.** Running
  them a second time exposed a genuine data-isolation defect that a
  single green run had hidden. This is documented as a finding in its
  own right, because it demonstrates why a passing result should be
  questioned rather than trusted.

### 7.2 Layer 2 — Browser-based journey verification

Backend tests prove the API works; they cannot prove the React
application can *drive* it. A wrong prop name, an unsent header, or a
route that renders nothing are all invisible to a Flask test client.

An automated browser walkthrough was therefore written that drives the
**real user journey** — loading the catalogue, searching, filtering by
category, opening a product, adding to cart, viewing recommendations,
and reaching checkout — while collecting console errors and failed
network requests.

This layer found three defects that all the backend tests had passed
over:

1. **An unknown URL rendered a completely blank page.** No catch-all
   route existed, so a mistyped address produced a white screen with no
   navigation and no way back.
2. **A deep link scrolled to the login form and stopped 580 pixels
   short**, because the page was still loading images when the scroll
   ran; the content moved after the scroll had finished.
3. **The API returned an HTML error page for errors it had not
   anticipated** — a non-numeric product id produced HTML where JSON
   was expected. The frontend masked this, since a failed JSON parse
   lands in the same error handler as any other failure.

This is the clearest justification for the layered approach: a green
result in one layer is not evidence of correctness in another.

### 7.3 Layer 3 — Layout verification

Responsive behaviour was verified programmatically at multiple viewport
widths, checking for horizontal overflow and confirming that no element
extends beyond the document width. Verification was done through the
browser's device-metrics override rather than by cropping screenshots,
since a cropped image and a genuine layout overflow are visually
identical but have entirely different causes.

---

## 8. Phase 4 — Evaluation

The system was evaluated against the five functional requirements
(Section 2) as follows:

| Requirement | Evaluated by |
|---|---|
| Accounts and roles | Auth suite (24 assertions) plus role-refusal tests |
| Catalogue browsing | Journey walkthrough — search, filter, deep links |
| Cart and orders | Order suite (79 assertions), including stock refusal |
| Reviews | Review suite (63), confirming the purchase gate holds |
| Recommendation quality | Recommendation suite (59) asserting output *relevance* |

The recommendation engine was additionally validated on **output
quality** rather than response correctness: recommendations were checked
to fall in plausible categories relative to the source product, and the
personalised engine was checked to reflect the categories a customer had
previously bought from.

---

## 9. Summary of the methodology

| Phase | Activity | Output |
|---|---|---|
| **1. Requirements** | Identify functional and non-functional needs | Five functional areas, two binding constraints |
| **2. Design** | Three-tier architecture, six-entity schema, REST interface | Architecture, data model, API contract |
| **3. Implementation** | Nine vertical slices, each tested before the next | Working system, 430 passing assertions |
| **4. Evaluation** | Layered verification — API, browser journey, layout | Three defects found and corrected |

The defining characteristic of this methodology is that **every claim
about the system is backed by an executable check**, and that the checks
are layered so that a pass in one layer is never mistaken for a pass in
another.
