# SmartCart — Roles and Product Management (Step 2)

Sellers can add, edit and delete products. Buyers cannot.

---

## Who can do what

| Action | Logged out | Buyer | Seller | Admin |
|---|---|---|---|---|
| Browse products | ✅ | ✅ | ✅ | ✅ |
| Search / filter products | ✅ | ✅ | ✅ | ✅ |
| Add a product | ❌ 401 | ❌ 403 | ✅ | ✅ |
| Edit a product | ❌ 401 | ❌ 403 | ✅ | ✅ |
| Delete a product | ❌ 401 | ❌ 403 | ✅ | ✅ |

`401` means "you are not logged in".
`403` means "logged in, but your role is not allowed".

---

## Where the seller tools are

Log in with a **seller** account, then:

- Click **Manage** in the navbar (only sellers and admins see this link), or
- Go directly to <http://localhost:5173/manage>

From there you can:

1. **Add a product** — fill in the form at the top and press *Add Product*
2. **Edit a product** — press *Edit* on any row; the form fills in and the
   button changes to *Save Changes*
3. **Delete a product** — press *Delete*; you will be asked to confirm first

If you visit `/manage` as a buyer you get a friendly "this area is for
sellers" message rather than a blank page.

---

## API reference

| Method | Path | Who | Success | Failures |
|---|---|---|---|---|
| GET | `/api/products` | anyone | 200 | — |
| GET | `/api/products/<id>` | anyone | 200 | 404 |
| POST | `/api/products` | seller, admin | 201 | 400, 401, 403 |
| PUT | `/api/products/<id>` | seller, admin | 200 | 400, 401, 403, 404 |
| DELETE | `/api/products/<id>` | seller, admin | 200 | 401, 403, 404 |

### Handy query options

```
GET /api/products?category=Electronics   # only electronics
GET /api/products?search=watch           # name or description contains "watch"
```

### Partial updates

`PUT` accepts just the fields you want to change. Sending only `price` leaves
the name, description and everything else as they were:

```json
{ "price": 1499 }
```

---

## How the role check works

```
React app                                    Flask
   |                                            |
   |  remembers the logged-in user              |
   |                                            |
   |-- POST /api/products --------------------> |
   |   header: X-User-Id: 5                     |
   |                                            |
   |                          looks up user 5 in the database
   |                          reads their role
   |                          buyer? -> 403 Forbidden
   |                          seller? -> allowed
   |                                            |
   |<-- 201 Created ----------------------------|
```

The header carries **only the user's id, never the role**. The backend looks the
role up in the database every time. So editing `X-User-Id` in the browser could
at most impersonate a different *existing* user — it cannot invent permissions,
because whatever id you send, the role still comes from the database.

---

## Testing

```powershell
cd C:\Users\ashim\Downloads\smartcart\backend
.\venv\Scripts\Activate.ps1
python test_products.py
```

**45 checks**, covering all of the above. It also verifies the 30 real products
are never damaged, and deletes its own test data afterwards.

The earlier auth suite still runs too — `python test_auth.py` (24 checks).

Run both after any change to routes or permissions.

---

## Answers you might need for your viva

**"How do you stop a buyer from adding products?"**
Every write route is wrapped in a `@roles_required("seller", "admin")`
decorator. It reads the `X-User-Id` header, loads that user, and checks the
role before the route body runs at all.

**"What is the difference between 401 and 403?"**
401 = not authenticated (we do not know who you are).
403 = authenticated but not authorised (we know who you are, you are just not
allowed). Using the right one makes the API easier to debug.

**"Could someone fake the header?"**
They could send a different id, but the role is read from the database — so
they cannot give themselves seller rights they do not have. A production system
would use a signed token so even the identity could not be guessed, and that
limit is worth stating in the report.

**"Why does PUT allow partial updates?"**
So the edit form can send only what changed. Without it, every save would have
to include all six fields, and a missing one would silently wipe that column.

---

## Known limitations (worth a line in your report)

1. **Any product can be edited by any seller.** There is no "owner" on a
   product yet, so seller A can edit seller B's listing. Fixing this needs a
   `seller_id` column on Product — a natural next step.
2. **Identity is a plain id in a header**, not a signed token. Fine for
   coursework; noted above.
3. **No product images upload.** The form takes an image URL. File upload would
   need storage on the server and is outside the synopsis.

---

## What changed

### Backend
- `requirements.txt` added (pinned versions)
- `@roles_required(...)` decorator and `get_current_user()` helper
- `read_product_payload()` — one validation function shared by create and update
- New routes: `GET /api/products/<id>`, `PUT`, `DELETE`
- `GET /api/products` now supports `?category=` and `?search=`
- `test_products.py` — 45 checks

### Frontend
- `api.js` — a single `requestJson()` helper; every call now sends `X-User-Id`
- `components/ManageProducts.jsx` — the seller page
- `App.jsx` — `/manage` route, and a **Manage** nav link for sellers/admins
- `App.css` — styles for the form and product list

---

## Next

The natural follow-on is giving products an **owner** (`seller_id`), so each
seller manages only their own listings. After that: cart saved per user.
