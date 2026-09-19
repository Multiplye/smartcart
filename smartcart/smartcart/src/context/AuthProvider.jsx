// =========================
// Auth provider
// =========================
//
// Holds "who is logged in" for the whole app.
//
// The logged-in user is also saved to localStorage, so a page refresh
// does not log you out.
//
// To READ the auth state, use the hook from useAuth.js:
//
//   import { useAuth } from "../context/useAuth";
//   const { user, isLoggedIn, signIn, signOut } = useAuth();

import { useState } from "react";
import AuthContext from "./authContextInstance";

// The key we store the user under in the browser's localStorage
const STORAGE_KEY = "smartcart_user";

/** Read the saved user from localStorage, or return null. */
function readSavedUser() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch {
    // If the saved value is corrupt, start logged out
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  // Reading localStorage straight into useState means we get the saved
  // user on the very first render - no second render, no flicker.
  const [user, setUser] = useState(readSavedUser);

  /** Call this after a successful login or register. */
  const signIn = (userData) => {
    setUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
  };

  /** Call this to log out. */
  const signOut = () => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value = {
    user,
    isLoggedIn: Boolean(user),
    // Convenience booleans for showing/hiding features
    isBuyer: user?.role === "buyer",
    isSeller: user?.role === "seller",
    isAdmin: user?.role === "admin",
    signIn,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthProvider;
