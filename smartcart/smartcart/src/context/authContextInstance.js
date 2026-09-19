// =========================
// Auth context object
// =========================
//
// Just the shared context object. Kept in its own file so that
// AuthProvider.jsx only exports a component, which keeps React's
// Fast Refresh working properly during development.

import { createContext } from "react";

const AuthContext = createContext(null);

export default AuthContext;
