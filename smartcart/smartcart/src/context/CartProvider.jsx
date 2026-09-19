// =========================
// Cart provider
// =========================
//
// Holds the shopping cart for the whole app.
//
// TWO MODES, ONE INTERFACE
// ------------------------
// The rest of the app never needs to know which mode we are in - it
// just calls addItem(5) and reads cartCount.
//
//   LOGGED IN  -> the cart lives in the database, tied to the user's
//                 account. Refresh the page, switch devices, and it is
//                 still there.
//
//   LOGGED OUT -> the cart lives in localStorage under "smartcart_guest_cart".
//                 We cannot save it to a user account because there is no
//                 user yet.
//
// WHEN YOU LOG IN
// ---------------
// If a guest had items in their localStorage cart, we push them into
// the real cart on login. So "browse as a guest, then log in to buy"
// does not silently lose the basket.

import { useCallback, useEffect, useRef, useState } from "react";

import CartContext from "./cartContextInstance";
import { useAuth } from "./useAuth";

import {
  getCart,
  addCartItem,
  setCartItemQuantity,
  removeCartItem,
  clearCart,
} from "../data/api";

// Where the guest cart is kept
const GUEST_STORAGE_KEY = "smartcart_guest_cart";

/** Read the guest cart from localStorage, or return []. */
function readGuestCart() {
  try {
    const saved = localStorage.getItem(GUEST_STORAGE_KEY);
    const parsed = saved ? JSON.parse(saved) : [];

    // Guard against a corrupted or hand-edited value
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    localStorage.removeItem(GUEST_STORAGE_KEY);
    return [];
  }
}

/** Turn a list of items into the count/total the UI shows. */
function summarise(items) {
  const count = items.reduce((sum, item) => sum + item.quantity, 0);

  const total = items.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );

  return { count, total: Math.round(total * 100) / 100 };
}

export function CartProvider({ children }) {
  const { user, isLoggedIn } = useAuth();

  const [items, setItems] = useState(readGuestCart);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Keeps track of which user's cart we have already loaded, so the
  // effect below does not refetch on every unrelated re-render.
  const loadedFor = useRef(null);

  // =========================
  // Keeping localStorage in step
  // =========================
  // Guests get their cart persisted on every change. Logged-in users do
  // not need this - their cart is in the database.
  useEffect(() => {
    if (isLoggedIn) return;

    try {
      localStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(items));
    } catch {
      // Storage full or blocked - the cart still works for this page view
    }
  }, [items, isLoggedIn]);

  // =========================
  // Loading the cart
  // =========================
  useEffect(() => {
    // Logged out: fall back to the guest cart, nothing to fetch.
    if (!isLoggedIn) {
      loadedFor.current = null;
      return;
    }

    // Already loaded this user's cart? Nothing to do.
    if (loadedFor.current === user.id) return;

    const userId = user.id;

    // Anything that calls setState must happen asynchronously, so React
    // is not asked to re-render in the middle of this effect.
    let cancelled = false;

    (async () => {
      setLoading(true);

      try {
        // Anything the guest put in their basket moves into the account.
        const pending = readGuestCart();

        if (pending.length > 0) {
          for (const item of pending) {
            try {
              await addCartItem(item.product_id, item.quantity);
            } catch {
              // Product may have been deleted or sold out - skip it
            }
          }

          localStorage.removeItem(GUEST_STORAGE_KEY);
        }

        const data = await getCart();

        if (cancelled) return;

        setItems(data.items);
        setError(null);
        loadedFor.current = userId;
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isLoggedIn, user]);

  // =========================
  // ACTIONS
  // =========================

  /**
   * Add a product to the cart.
   *
   * Logged out: work it out locally, since there is no server cart.
   * Logged in:  let the server do it, then trust its answer.
   */
  const addItem = useCallback(
    async (product, quantity = 1) => {
      setError(null);

      if (!isLoggedIn) {
        setItems((current) => {
          const existing = current.find(
            (item) => item.product_id === product.id
          );

          if (existing) {
            return current.map((item) =>
              item.product_id === product.id
                ? { ...item, quantity: item.quantity + quantity }
                : item
            );
          }

          return [
            ...current,
            {
              product_id: product.id,
              name: product.name,
              price: product.price,
              image: product.image,
              category: product.category,
              stock: product.stock,
              quantity,
              subtotal: product.price * quantity,
            },
          ];
        });

        return { message: `${product.name} added to your cart.` };
      }

      try {
        const data = await addCartItem(product.id, quantity);
        setItems(data.items);

        return data;
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [isLoggedIn]
  );

  /** Set an item's quantity. 0 removes it. */
  const setQuantity = useCallback(
    async (productId, quantity) => {
      setError(null);

      if (!isLoggedIn) {
        setItems((current) =>
          quantity === 0
            ? current.filter((item) => item.product_id !== productId)
            : current.map((item) =>
                item.product_id === productId
                  ? {
                      ...item,
                      quantity,
                      subtotal: item.price * quantity,
                    }
                  : item
              )
        );

        return null;
      }

      try {
        const data = await setCartItemQuantity(productId, quantity);
        setItems(data.items);

        return data;
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [isLoggedIn]
  );

  /** Remove one product. */
  const removeItem = useCallback(
    async (productId) => {
      setError(null);

      if (!isLoggedIn) {
        setItems((current) =>
          current.filter((item) => item.product_id !== productId)
        );

        return null;
      }

      try {
        const data = await removeCartItem(productId);
        setItems(data.items);

        return data;
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [isLoggedIn]
  );

  /** Empty the cart. */
  const emptyCart = useCallback(async () => {
    setError(null);

    if (!isLoggedIn) {
      setItems([]);
      return null;
    }

    try {
      const data = await clearCart();
      setItems(data.items);

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [isLoggedIn]);

  /** Re-fetch the cart - useful after a checkout. */
  const refreshCart = useCallback(async () => {
    if (!isLoggedIn) return;

    try {
      const data = await getCart();
      setItems(data.items);
    } catch (err) {
      setError(err.message);
    }
  }, [isLoggedIn]);

  // =========================
  // DERIVED VALUES
  // =========================
  const { count: cartCount, total: cartTotal } = summarise(items);

  const value = {
    items,
    cartCount,
    cartTotal,
    loading,
    error,
    addItem,
    setQuantity,
    removeItem,
    emptyCart,
    refreshCart,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export default CartProvider;
