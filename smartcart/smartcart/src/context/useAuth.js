// =========================
// useAuth hook
// =========================
//
// The way components read the auth state.
//
// Usage:
//
//   import { useAuth } from "../context/useAuth";
//
//   const { user, isLoggedIn, signIn, signOut } = useAuth();

import { useContext } from "react";
import AuthContext from "./authContextInstance";

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside an <AuthProvider>");
  }

  return context;
}

export default useAuth;
