# SmartCart — Authentication (Step 1)

How login and registration work, and how to test them.

---

## What was added

### Backend (`backend/app.py`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/register` | POST | Create an account |
| `/api/login` | POST | Log in |

### New User table

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(150) | Full name |
| `email` | String(200) | **Unique** — no two accounts can share an email |
| `password_hash` | String(300) | The scrambled password. Never the real one |
| `role` | String(20) | `buyer`, `seller` or `admin`. Defaults to `buyer` |

### Frontend

| File | Change |
|---|---|
| `src/data/api.js` | Added `register()` and `login()` |
| `src/context/AuthProvider.jsx` | Remembers who is logged in |
| `src/context/authContextInstance.js` | The shared context object |
| `src/context/useAuth.js` | The hook components use to read auth state |
| `src/components/Auth.jsx` | Your form is now wired to the real API |
| `src/main.jsx` | Wraps the app in `<AuthProvider>` |
| `src/App.jsx` | Navbar greets you by name when logged in |
| `src/App.css` | Styles for the dropdown and feedback messages |

---

## How to use it

1. Make sure the backend is running (Terminal 1)
2. Make sure the frontend is running (Terminal 2)
3. Open <http://localhost:5173> and scroll to the **Login** section
4. Click **Register**, fill in the form, choose Buyer or Seller
5. You are logged in immediately — the navbar will show your name
6. Refresh the page — you stay logged in (saved in browser storage)

---

## Testing

Two ways, pick either:

### A. Automated tests (no server needed)

```powershell
cd C:\Users\ashim\Downloads\smartcart\backend
.\venv\Scripts\Activate.ps1
python test_auth.py
```

24 checks covering registration, login, duplicates, validation, wrong
passwords, and password hashing. It deletes its own test accounts.

### B. By hand, in the browser

Open <http://127.0.0.1:5000/api/products> to confirm the backend is up,
then use the form at <http://localhost:5173>.

---

## Why passwords are safe

Passwords are never stored as text. We store a **hash**:

```
You type:        mypassword123
Stored in DB:    scrypt:32768:8:1$cXU2fpxBZHJQhmhZ$3be089a4d9...
```

A hash is one-way — you cannot turn it back into the password. When you log
in, the backend hashes what you typed and compares the two hashes.

Even if someone copied your `smartcart.db` file, they could not read anyone's
password.

---

## Answers you might need for your viva

**"Why is the password not stored directly?"**
Because if the database leaked, every user's password would be exposed. A hash
makes that useless — and because people reuse passwords, it also protects their
other accounts.

**"What does `role` do?"**
It splits users into buyer, seller and admin. Buyers shop, sellers list
products, admins manage the whole site. The column is in place now; the
permissions that enforce it come in Step 2.

**"Why the same error for a wrong password and an unknown email?"**
So an attacker cannot use the login form to discover which emails have accounts.
That technique is called *user enumeration*.

**"Is this production-ready?"**
No — and that is expected for this project. It uses a simple session approach
rather than signed tokens, and the Flask development server. Both are normal
for an academic project; the report should note them as known limitations.

---

## Known limitations (worth a line in your report)

1. **Role is self-selected at signup.** Anyone can choose "seller" from the
   dropdown. Locking this down belongs with the admin panel.
2. **The browser stores the user object in localStorage.** Fine for a project,
   but a determined user could edit it. Real systems use signed server-side
   tokens (JWT) so this cannot happen.
3. **No password reset.** Out of scope for the synopsis.

---

## Next: Step 2

Enforce the roles — sellers can add products, buyers cannot. The `role` column
already exists, so this is about checking it on the backend routes.
