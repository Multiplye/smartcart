import { useState } from "react";
import { login, register } from "../data/api";
import { useAuth } from "../context/useAuth";

function Auth() {
  const { user, isLoggedIn, signIn, signOut } = useAuth();

  const [isLogin, setIsLogin] = useState(true);

  // The form fields. One piece of state per input keeps this easy to follow.
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("buyer");

  // Feedback shown to the user
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  /** Clear the form back to empty. */
  const resetForm = () => {
    setName("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setRole("buyer");
    setError(null);
  };

  /** Switch between the Login and Register views. */
  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
    resetForm();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError(null);
    setSuccess(null);

    // --- Local check before we bother the server ---
    if (!isLogin && password !== confirmPassword) {
      setError("Those passwords do not match.");
      return;
    }

    setSubmitting(true);

    try {
      if (isLogin) {
        const data = await login({ email, password });
        signIn(data.user);
        setSuccess(data.message);
      } else {
        const data = await register({ name, email, password, role });
        // Sign them straight in so they do not have to log in again
        signIn(data.user);
        setSuccess(data.message);
      }

      // Clear the password fields once it worked
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // =========================
  // ALREADY LOGGED IN
  // =========================
  if (isLoggedIn) {
    return (
      <section className="auth-section" id="auth">
        <div className="auth-container">

          <div className="auth-header">
            <div className="auth-icon">🛒</div>

            <h2>Hello, {user.name}!</h2>

            <p>
              You are logged in as{" "}
              <strong>{user.email}</strong>{" "}
              ({user.role}).
            </p>
          </div>

          {success && (
            <div className="auth-message auth-success">{success}</div>
          )}

          <button
            type="button"
            className="auth-btn"
            onClick={() => {
              signOut();
              setSuccess(null);
              resetForm();
            }}
          >
            Log Out
          </button>

        </div>
      </section>
    );
  }

  // =========================
  // LOGIN / REGISTER FORM
  // =========================
  return (
    <section className="auth-section" id="auth">

      <div className="auth-container">

        <div className="auth-header">
          <div className="auth-icon">
            🛒
          </div>

          <h2>
            {isLogin ? "Welcome Back!" : "Create Your Account"}
          </h2>

          <p>
            {isLogin
              ? "Login to continue shopping with SmartCart."
              : "Create an account to start shopping."}
          </p>
        </div>

        {error && (
          <div className="auth-message auth-error">
            {error}
          </div>
        )}

        {success && (
          <div className="auth-message auth-success">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          {!isLogin && (
            <div className="form-group">
              <label>Full Name</label>

              <input
                type="text"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Email Address</label>

            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>

            <input
              type="password"
              placeholder={
                isLogin
                  ? "Enter your password"
                  : "At least 6 characters"
              }
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label>Confirm Password</label>

              <input
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          {!isLogin && (
            <div className="form-group">
              <label>I want to join as a</label>

              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="buyer">Buyer — browse and buy products</option>
                <option value="seller">Seller — list and sell products</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="auth-btn"
            disabled={submitting}
          >
            {submitting
              ? "Please wait..."
              : isLogin
                ? "Login"
                : "Create Account"}
          </button>

        </form>

        <div className="auth-switch">

          <p>
            {isLogin
              ? "Don't have an account?"
              : "Already have an account?"}

            <button
              type="button"
              onClick={toggleMode}
            >
              {isLogin ? " Register" : " Login"}
            </button>
          </p>

        </div>

      </div>

    </section>
  );
}

export default Auth;
