// =========================
// Cart context instance
// =========================
//
// Just the created context object, on its own.
//
// Why a separate file? Because of the eslint rule
// "react-refresh/only-export-components": a file that exports a
// component must not also export anything that is not a component, or
// hot reloading cannot work out what to refresh.
//
// So the three pieces live apart:
//
//   cartContextInstance.js  <- this file: the context object
//   CartProvider.jsx        <- the component that fills it in
//   useCart.js              <- the hook components call

import { createContext } from "react";

const CartContext = createContext(null);

export default CartContext;
