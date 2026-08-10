import {
  useState,
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";


function LoginPage() {
  const {
    signIn,
    isAuthenticated,
    authLoading,
  } = useAuth();

  const navigate =
    useNavigate();

  const location =
    useLocation();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  if (
    !authLoading &&
    isAuthenticated
  ) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      await signIn(
        email,
        password
      );

      navigate(
        location.state?.from ||
          "/",
        {
          replace:
            true,
        }
      );
    } catch (loginError) {
      setError(
        loginError.message ||
          "Login failed"
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">
          Autonomous DevOps Platform
        </p>

        <h1>
          Welcome Back
        </h1>

        <p className="auth-description">
          Sign in to manage your autonomous
          CI/CD healing runs.
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

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={
                (event) =>
                  setPassword(
                    event.target.value
                  )
              }
              required
              autoComplete="current-password"
            />
          </label>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Signing in..."
              : "Sign In"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/signup">
            Create Account
          </Link>

          <Link to="/forgot-password">
            Forgot Password?
          </Link>
        </div>
      </section>
    </main>
  );
}

export default LoginPage;