import {
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";


function ResetPasswordPage() {
  const {
    updatePassword,
  } = useAuth();

  const navigate =
    useNavigate();

  const [password, setPassword] =
    useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

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

    setError("");
    setMessage("");

    if (password.length < 8) {
      setError(
        "Password must contain at least 8 characters"
      );
      return;
    }

    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Passwords do not match"
      );
      return;
    }

    setLoading(true);

    try {
      await updatePassword(
        password
      );

      setMessage(
        "Password updated successfully."
      );

      setTimeout(
        () => {
          navigate(
            "/",
            {
              replace: true,
            }
          );
        },
        1200
      );
    } catch (updateError) {
      setError(
        updateError.message ||
          "Unable to update password"
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
          Choose New Password
        </h1>

        <p className="auth-description">
          Enter a new password for your account.
        </p>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          <label>
            New Password

            <input
              type="password"
              value={password}
              onChange={
                (event) =>
                  setPassword(
                    event.target.value
                  )
              }
              minLength="8"
              required
              autoComplete="new-password"
            />
          </label>

          <label>
            Confirm Password

            <input
              type="password"
              value={
                confirmPassword
              }
              onChange={
                (event) =>
                  setConfirmPassword(
                    event.target.value
                  )
              }
              minLength="8"
              required
              autoComplete="new-password"
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
              ? "Updating..."
              : "Update Password"}
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

export default ResetPasswordPage;