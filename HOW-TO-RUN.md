# SmartCart — How To Run

SmartCart is an online marketplace (BIT academic project) with a React frontend
and a Flask + SQLite backend.

Run **two terminals** — the backend and the frontend each need their own.

---

## Terminal 1 — Backend (Flask)

```powershell
cd C:\Users\ashim\Downloads\smartcart\backend
.\venv\Scripts\Activate.ps1
python app.py
```

You should see:

```
* Running on http://127.0.0.1:5000
```

Test it in a browser: <http://127.0.0.1:5000/api/products>
That should return a JSON list of **30 products**.

> If PowerShell blocks the activate script, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

---

## Terminal 2 — Frontend (React + Vite)

```powershell
cd C:\Users\ashim\Downloads\smartcart\smartcart\smartcart
npm run dev
```

You should see:

```
  VITE v8.3.0  ready in ~1000 ms

  ➜  Local:   http://localhost:5173/
```

Open <http://localhost:5173>

---

## ⚠️ The folder trap — read this if you get `Missing script` or `ENOENT`

There are **two folders named `smartcart`, nested inside each other**, plus a
`backend` folder. That means **four** places you might be standing, and only one
of them runs the React app with `npm`.

```
smartcart/                     <- project root   ❌ npm says ENOENT
├── HOW-TO-RUN.md
├── backend/                   <- Flask API       ❌ npm = wrong tool, use python
└── smartcart/                 <- ❌ WRONG         npm says Missing script
    └── smartcart/             <- ✅ RIGHT         npm run dev works here
        ├── src/
        ├── package.json       <- the real "dev" script
        └── vite.config.js
```

### Quick rule

**The correct folder contains `vite.config.js`.** Run `dir` and check.
If it's not there, you're in the wrong place.

### Every wrong folder now tells you what to do

A small guard-rail `package.json` was added to each wrong folder, so you get a
clear message instead of a cryptic npm error:

| You are in | Running `npm run dev` prints |
|---|---|
| `smartcart\` | "WRONG FOLDER" + the correct `cd` |
| `smartcart\backend\` | "WRONG FOLDER AND WRONG TOOL" + `python app.py` |
| `smartcart\smartcart\` | "WRONG FOLDER" + `cd smartcart` |
| `smartcart\smartcart\smartcart\` | ✅ Vite starts normally |

> Note: npm searches **up** the folder tree for a `package.json`. That's why
> running npm inside `backend\` reports the root's message — it found the root
> file by walking upward.

### The one command that always works

```powershell
cd C:\Users\ashim\Downloads\smartcart\smartcart\smartcart
npm run dev
```

---

## Common errors and what they mean

| What you see | Cause | Fix |
|---|---|---|
| `npm error code ENOENT` + `path ...\smartcart\package.json` | Running npm in the **project root** | `cd smartcart\smartcart\smartcart` |
| `npm error Missing script: "dev"` | Running npm in `smartcart\smartcart` | `cd smartcart` then retry |
| `WRONG FOLDER AND WRONG TOOL` | Running npm inside **`backend\`** (a Python project) | Use `python app.py` there. npm belongs in the frontend folder |
| Page says **"Could not load products"** | Flask backend not running | Start Terminal 1 |
| `'npm' is not recognized` | Node.js not installed | Install from nodejs.org |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | See note in Terminal 1 |
| `Port 5173 is in use, trying another one...` | A dev server is already running | Fine — it uses 5174. Close the old terminal to reuse 5173 |
| Port 5000 already in use | Old Flask process alive | Close the old terminal; Flask's debug reloader spawns a child process, so the parent PID may not be the real listener |

---

## Useful extras

**Re-seed the database** (restores all 30 demo products, safe to re-run):

```powershell
cd C:\Users\ashim\Downloads\smartcart\backend
.\venv\Scripts\Activate.ps1
python import_products.py
```

**Check the database directly:**

```powershell
cd C:\Users\ashim\Downloads\smartcart\backend
.\venv\Scripts\Activate.ps1
python -c "from app import app, Product; app.app_context().push(); print(Product.query.count())"
```

**Production build of the frontend:**

```powershell
cd C:\Users\ashim\Downloads\smartcart\smartcart\smartcart
npm run build
```
