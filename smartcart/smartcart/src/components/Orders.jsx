import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAuth } from "../context/useAuth";
import { getOrders, updateOrderStatus, cancelOrder } from "../data/api";

// The status colours, so the badge looks different at each stage
const STATUS_CLASS = {
  Pending: "status-pending",
  Confirmed: "status-confirmed",
  Shipped: "status-shipped",
  Delivered: "status-delivered",
  Cancelled: "status-cancelled",
};

// What each role can do next. Mirrors the backend's
// ALLOWED_STATUS_TRANSITIONS, so the buttons offered match what the
// server will actually accept.
const NEXT_STATUS = {
  Pending: ["Confirmed", "Cancelled"],
  Confirmed: ["Shipped", "Cancelled"],
  Shipped: ["Delivered"],
  Delivered: [],
  Cancelled: [],
};

// Say "19 September 2026" rather than an ISO timestamp
function formatDate(isoString) {
  if (!isoString) return "";

  const date = new Date(isoString);

  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function Orders() {
  const location = useLocation();
  const { isLoggedIn, isSeller, isAdmin } = useAuth();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Which order is currently being updated, so its buttons can be disabled
  const [busyId, setBusyId] = useState(null);
  const [notice, setNotice] = useState(null);

  // Set when we arrive here straight after checking out
  const justPlaced = location.state?.justPlaced ?? null;

  // =========================
  // LOAD THE ORDERS
  // =========================
  useEffect(() => {
    if (!isLoggedIn) return;

    let cancelled = false;

    (async () => {
      try {
        const data = await getOrders();

        if (!cancelled) {
          setOrders(data);
          setError(null);
        }
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
  }, [isLoggedIn]);

  const showLoading = isLoggedIn && loading;

  /** Replace one order in the list with the updated version. */
  const replaceOrder = (updated) => {
    setOrders((current) =>
      current.map((order) => (order.id === updated.id ? updated : order))
    );
  };

  // =========================
  // CHANGE A STATUS
  // =========================
  const handleStatusChange = async (order, newStatus) => {
    setNotice(null);
    setError(null);
    setBusyId(order.id);

    try {
      const data = await updateOrderStatus(order.id, newStatus);
      replaceOrder(data.order);
      setNotice(data.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  // =========================
  // CANCEL AN ORDER
  // =========================
  const handleCancel = async (order) => {
    const sure = window.confirm(
      `Cancel order #${order.id}? The items will go back into stock.`
    );

    if (!sure) return;

    setNotice(null);
    setError(null);
    setBusyId(order.id);

    try {
      const data = await cancelOrder(order.id);
      replaceOrder(data.order);
      setNotice(data.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  };

  // =========================
  // NOT LOGGED IN
  // =========================
  if (!isLoggedIn) {
    return (
      <main className="all-products-page">
        <section className="products-page-header">
          <p>YOUR ACCOUNT</p>
          <h1>My Orders</h1>

          <div className="products-status products-error">
            <strong>Please log in.</strong>
            <p>Your order history is tied to your account.</p>
          </div>

          <Link to="/" className="learn-btn">
            Back to Home
          </Link>
        </section>
      </main>
    );
  }

  // =========================
  // THE PAGE
  // =========================
  const pageTitle = isAdmin
    ? "All Orders"
    : isSeller
      ? "Orders For My Products"
      : "My Orders";

  const subtitle = isAdmin
    ? "Every order placed on SmartCart."
    : isSeller
      ? "Orders that include at least one of your products."
      : "Everything you have ordered, newest first.";

  return (
    <main className="all-products-page">
      <section className="products-page-header">
        <p>YOUR ACCOUNT</p>

        <h1>{pageTitle}</h1>

        <span>{subtitle}</span>

        <Link to="/products" className="learn-btn">
          Browse Products
        </Link>
      </section>

      <section className="collection-section">

        {justPlaced && (
          <div className="products-status products-success">
            <strong>Order #{justPlaced} placed successfully.</strong>
            <p>
              You will pay cash when it arrives. Keep an eye on the status
              below.
            </p>
          </div>
        )}

        {notice && (
          <div className="products-status products-success">{notice}</div>
        )}

        {error && (
          <div className="products-status products-error">
            <strong>Something went wrong.</strong>
            <p>{error}</p>
          </div>
        )}

        {showLoading && <p className="products-status">Loading orders...</p>}

        {!showLoading && orders.length === 0 && (
          <div className="empty-cart">
            <div className="empty-cart-icon">00</div>

            <h3>
              {isSeller || isAdmin
                ? "No orders yet"
                : "You have not ordered anything yet"}
            </h3>

            <p>
              {isSeller
                ? "Once a shopper orders one of your products, it will appear here."
                : "Browse the shop and place your first order."}
            </p>

            <Link to="/products">
              <button className="shop-btn">Browse Products</button>
            </Link>
          </div>
        )}

        {!showLoading && orders.length > 0 && (
          <div className="order-list">
            {orders.map((order) => {
              const nextOptions = NEXT_STATUS[order.status] || [];
              const isBusy = busyId === order.id;
              const isFinished =
                order.status === "Delivered" || order.status === "Cancelled";

              return (
                <div
                  className={`order-card ${
                    justPlaced === order.id ? "order-card-new" : ""
                  }`}
                  key={order.id}
                >
                  {/* ---------- header ---------- */}
                  <div className="order-head">
                    <div>
                      <h3>Order #{order.id}</h3>
                      <small>Placed {formatDate(order.created_at)}</small>
                    </div>

                    <span
                      className={`order-status ${
                        STATUS_CLASS[order.status] || ""
                      }`}
                    >
                      {order.status}
                    </span>
                  </div>

                  {/* ---------- the items ---------- */}
                  <div className="order-items">
                    {order.items.map((item, index) => (
                      <div
                        className="order-line"
                        key={`${order.id}-${index}`}
                      >
                        <span className="order-line-name">
                          {item.product_name}
                        </span>

                        <span className="order-line-math">
                          {item.quantity} x Rs.{" "}
                          {item.unit_price.toLocaleString()}
                        </span>

                        <span className="order-line-total">
                          Rs. {item.subtotal.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* ---------- delivery + money ---------- */}
                  <div className="order-meta">
                    <div>
                      <strong>Deliver to</strong>
                      <span>{order.full_name}</span>
                      <span>{order.phone}</span>
                      <span>
                        {order.address}, {order.city}
                      </span>
                    </div>

                    <div>
                      <strong>Payment</strong>
                      <span>{order.payment_method}</span>
                    </div>

                    <div>
                      <strong>Total</strong>
                      <span className="order-total">
                        Rs. {order.total.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* ---------- actions ---------- */}
                  {(isSeller || isAdmin) && !isFinished && (
                    <div className="order-actions">
                      <span className="order-actions-label">
                        Move to:
                      </span>

                      {nextOptions
                        .filter((status) => status !== "Cancelled")
                        .map((status) => (
                          <button
                            key={status}
                            type="button"
                            className="order-advance-btn"
                            disabled={isBusy}
                            onClick={() =>
                              handleStatusChange(order, status)
                            }
                          >
                            {status}
                          </button>
                        ))}

                      {nextOptions.includes("Cancelled") && (
                        <button
                          type="button"
                          className="order-cancel-btn"
                          disabled={isBusy}
                          onClick={() => handleCancel(order)}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  )}

                  {/* A buyer's only action is cancelling a Pending order */}
                  {!isSeller && !isAdmin && order.status === "Pending" && (
                    <div className="order-actions">
                      <button
                        type="button"
                        className="order-cancel-btn"
                        disabled={isBusy}
                        onClick={() => handleCancel(order)}
                      >
                        Cancel Order
                      </button>
                    </div>
                  )}

                  {isFinished && (
                    <p className="order-finished">
                      {order.status === "Delivered"
                        ? "This order was delivered."
                        : "This order was cancelled and the stock was returned."}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}

export default Orders;
