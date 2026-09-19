// =========================
// useCart hook
// =========================
//
// How any component reaches the cart:
//
//   import { useCart } from "../context/useCart";
//
//   const { items, cartCount, cartTotal, addItem } = useCart();
//
// Throwing when there is no provider turns a confusing "cannot read
// property of null" into a message that says exactly what is wrong.

import { useContext } from "react";
import CartContext from "./cartContextInstance";

export function useCart() {
  const context = useContext(CartContext);

  if (context === null) {
    throw new Error(
      "useCart() was called outside a <CartProvider>. " +
        "Wrap your component in <CartProvider> in main.jsx."
    );
  }

  return context;
}

export default useCart;
