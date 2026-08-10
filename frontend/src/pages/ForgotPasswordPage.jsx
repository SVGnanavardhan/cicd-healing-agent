import {
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";


function ForgotPasswordPage() {
  const {
    resetPassword,
  } = useAuth();

  const [email, setEmail] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await resetPassword(
        email
      );

      setMessage(
        "Password reset link sent. Check your email."
      );
    } catch (resetError) {
      setError(
        resetError.message ||
          "Unable to send reset email"
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">
          Account Recovery
        </p>

        <h1>
          Reset Password
        </h1>

        <p className="auth-description">
          Enter your account email and we will
          send a password reset link.
        </p>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={
                (event) =>
                  setEmail(
                    event.target.value
                  )
              }
              required
              autoComplete="email"
            />
          </label>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {message && (
            <div className="success-message">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Sending..."
              : "Send Reset Link"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">
            Back to Login
          </Link>
        </div>
      </section>
    </main>
  );
}

export default ForgotPasswordPage;