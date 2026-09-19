import { useCallback, useEffect, useState } from "react";

import { useAuth } from "../context/useAuth";

import {
  getAdminStats,
  getAdminUsers,
  setUserRole,
  deleteUser,
} from "../data/api";

// The roles an admin can hand out, with a label and a short
// explanation so the dropdown is self-describing. A beginner reading
// the panel should not have to guess what "seller" unlocks.
const ROLE_OPTIONS = [
  { value: "buyer", label: "Buyer", hint: "Can shop and leave reviews" },
  { value: "seller", label: "Seller", hint: "Can also list products" },
  { value: "admin", label: "Admin", hint: "Full access to this panel" },
];

function StatCard({ label, value, note }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {note && <span className="stat-note">{note}</span>}
    </div>
  );
}

/**
 * The admin dashboard - /admin
 *
 * Only reachable by an admin, and only the BACKEND is trusted to
 * decide that. If a buyer guesses this URL, every request the page
 * makes comes back 403 and the page shows an error instead of data.
 * Hiding a route in React is not security.
 *
 * The one rule worth reading carefully is the "last admin" protection:
 * an admin cannot demote or delete themselves, and cannot remove the
 * final admin. Without it, one careless click would lock everybody out
 * of the panel with no way back in through the UI.
 */
function Admin() {
  const { user } = useAuth();

  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // One message for the whole page, used for both success and failure
  // of an action. `noticeKind` drives the colour.
  const [notice, setNotice] = useState(null);
  const [noticeKind, setNoticeKind] = useState("success");

  // Which row is mid-action, so we can disable just that row's buttons
  // rather than freezing the whole table.
  const [busyUserId, setBusyUserId] = useState(null);

  // A two-step confirmation for deleting an account, because there is
  // no undo. We store the id and ask again.
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const [search, setSearch] = useState("");

  // =========================
  // LOAD
  // =========================
  const load = useCallback(async () => {
    try {
      const [statsData, usersData] = await Promise.all([
        getAdminStats(),
        getAdminUsers(),
      ]);

      setStats(statsData);
      setUsers(usersData.users);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const [statsData, usersData] = await Promise.all([
          getAdminStats(),
          getAdminUsers(),
        ]);

        if (cancelled) return;

        setStats(statsData);
        setUsers(usersData.users);
        setError(null);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // =========================
  // ACTIONS
  // =========================
  const flash = (kind, message) => {
    setNoticeKind(kind);
    setNotice(message);
  };

  const handleRoleChange = async (targetUser, newRole) => {
    if (newRole === targetUser.role) return;

    setBusyUserId(targetUser.id);
    setNotice(null);

    try {
      const data = await setUserRole(targetUser.id, newRole);

      // The server's message already names the user and the new role,
      // so we do not have to build that sentence again here.
      flash("success", data.message);

      await load();
    } catch (err) {
      flash("error", err.message);
    } finally {
      setBusyUserId(null);
    }
  };

  const handleDelete = async (targetUser) => {
    setBusyUserId(targetUser.id);
    setNotice(null);

    try {
      const data = await deleteUser(targetUser.id);

      flash("success", data.message);
      setConfirmDeleteId(null);

      await load();
    } catch (err) {
      flash("error", err.message);
    } finally {
      setBusyUserId(null);
    }
  };

  // =========================
  // FILTER
  // =========================
  const term = search.trim().toLowerCase();

  const visibleUsers = term
    ? users.filter(
        (u) =>
          u.name.toLowerCase().includes(term) ||
          u.email.toLowerCase().includes(term) ||
          u.role.toLowerCase().includes(term),
      )
    : users;

  // =========================
  // RENDER
  // =========================
  if (loading) {
    return (
      <main className="page-wrapper">
        <p className="products-status">Loading the admin panel...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page-wrapper">
        <div className="products-status products-error">
          <strong>You cannot open the admin panel.</strong>
          <p>{error}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="page-wrapper">
      <section className="page-head">
        <span className="section-label">ADMINISTRATION</span>

        <h1>
          Admin <span>Panel</span>
        </h1>

        <p>
          Manage accounts and see how the shop is doing. Changes take
          effect immediately.
        </p>
      </section>

      {notice && (
        <div
          className={`products-status ${
            noticeKind === "error" ? "products-error" : "products-success"
          }`}
          role="status"
        >
          {notice}
        </div>
      )}

      {/* ==========================================
          STATS
          ========================================== */}
      <section className="stat-grid">
        <StatCard label="Users" value={stats.users} />
        <StatCard label="Products" value={stats.products} note={`${stats.out_of_stock} out of stock`} />
        <StatCard label="Orders" value={stats.orders} />
        <StatCard label="Reviews" value={stats.reviews} />
        <StatCard
          label="Revenue"
          value={`Rs. ${stats.revenue.toLocaleString()}`}
          note="Excludes cancelled orders"
        />
      </section>

      {/* A small breakdown of order statuses. Plain flex bars rather
          than a chart library - there is nothing here worth pulling a
          dependency in for. */}
      <section className="status-breakdown">
        <h3>Orders by status</h3>

        <div className="status-bars">
          {Object.entries(stats.orders_by_status).map(([status, count]) => {
            const share = stats.orders === 0 ? 0 : (count / stats.orders) * 100;

            return (
              <div className="status-bar-row" key={status}>
                <span className="status-bar-label">{status}</span>

                <div className="status-bar-track">
                  <div
                    className={`status-bar-fill status-${status.toLowerCase()}`}
                    style={{ width: `${share}%` }}
                  />
                </div>

                <span className="status-bar-count">{count}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ==========================================
          USERS
          ========================================== */}
      <section className="admin-section">
        <div className="admin-section-head">
          <h3>Accounts ({users.length})</h3>

          <input
            className="admin-search"
            type="search"
            placeholder="Search by name, email or role"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {visibleUsers.length === 0 ? (
          <p className="products-status">No accounts match that search.</p>
        ) : (
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Orders</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {visibleUsers.map((row) => {
                  const isMe = row.id === user?.id;
                  const busy = busyUserId === row.id;
                  const confirming = confirmDeleteId === row.id;

                  return (
                    <tr key={row.id} className={isMe ? "admin-row-me" : ""}>
                      <td>
                        {row.name}
                        {isMe && <span className="admin-you-tag">you</span>}
                      </td>

                      <td className="admin-email">{row.email}</td>

                      <td>{row.order_count}</td>

                      <td>
                        {/* Your own role cannot be changed by you, so
                            show it as plain text rather than a control
                            that will just fail. */}
                        {isMe ? (
                          <span className={`role-badge role-${row.role}`}>
                            {row.role}
                          </span>
                        ) : (
                          <select
                            className="role-select"
                            value={row.role}
                            disabled={busy}
                            onChange={(e) =>
                              handleRoleChange(row, e.target.value)
                            }
                          >
                            {ROLE_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        )}
                      </td>

                      <td>
                        {isMe ? (
                          <span className="admin-hint">
                            You cannot change or delete your own account.
                          </span>
                        ) : confirming ? (
                          <span className="admin-confirm">
                            <span>Delete everything?</span>

                            <button
                              className="admin-btn admin-btn-danger"
                              disabled={busy}
                              onClick={() => handleDelete(row)}
                            >
                              {busy ? "Deleting..." : "Yes, delete"}
                            </button>

                            <button
                              className="admin-btn"
                              disabled={busy}
                              onClick={() => setConfirmDeleteId(null)}
                            >
                              Cancel
                            </button>
                          </span>
                        ) : (
                          <button
                            className="admin-btn admin-btn-danger"
                            disabled={busy}
                            onClick={() => setConfirmDeleteId(row.id)}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <p className="admin-footnote">
          Deleting an account removes their cart, orders and reviews.
          Any products they listed stay in the shop and become
          shop-owned, so nobody loses their order history.
        </p>
      </section>

      {/* ==========================================
          ROLE REFERENCE
          ========================================== */}
      <section className="admin-section">
        <h3>What each role can do</h3>

        <div className="role-reference">
          {ROLE_OPTIONS.map((option) => (
            <div className="role-card" key={option.value}>
              <span className={`role-badge role-${option.value}`}>
                {option.label}
              </span>

              <p>{option.hint}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

export default Admin;
