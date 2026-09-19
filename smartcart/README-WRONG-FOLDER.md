# ⚠️ This is NOT the React app folder

You are in `smartcart/smartcart/`. This folder only holds the **Tailwind CSS**
packages that the real React app depends on.

If you run `npm run dev` here you will get:

```
npm error Missing script: "dev"
```

That is expected — there is no `dev` script in this folder.

## Run the app from here instead

```
cd smartcart        # the NEXT folder in, not this one
npm run dev
```

Or in one line from this folder:

```
cd smartcart && npm run dev
```

## The folder layout explained

```
smartcart/                 <- project root
├── backend/               <- Flask API (run: python app.py)
└── smartcart/             <- YOU ARE HERE (Tailwind deps only, no scripts)
    └── smartcart/         <- ✅ the React app (run: npm run dev)
        ├── src/
        ├── package.json
        └── vite.config.js
```

Yes, there are two folders both called `smartcart` nested inside each other.
The React app is the **innermost** one.
