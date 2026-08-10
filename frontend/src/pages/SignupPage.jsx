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


function SignupPage() {
  const {
    signUp,
  } = useAuth();

  const navigate =
    useNavigate();

  const [formData, setFormData] =
    useState({
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
    });

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  function handleChange(
    event
  ) {
    const {
      name,
      value,
    } = event.target;

    setFormData(
      (current) => ({
        ...current,
        [name]:
          value,
      })
    );
  }


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    setError("");
    setMessage("");

    if (
      formData.password !==
      formData.confirm_password
    ) {
      setError(
        "Passwords do not match"
      );

      return;
    }

    if (
      formData.password.length <
      8
    ) {
      setError(
        "Password must contain at least 8 characters"
      );

      return;
    }

    setLoading(true);

    try {
      const data =
        await signUp(
          formData.email,
          formData.password,
          formData.full_name
        );

      if (
        data.session
      ) {
        navigate(
          "/",
          {
            replace:
              true,
          }
        );

        return;
      }

      setMessage(
        "Account created. Check your email to confirm your account."
      );
    } catch (signupError) {
      setError(
        signupError.message ||
          "Account creation failed"
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
          Create Account
        </h1>

        <p className="auth-description">
          Create your workspace for autonomous
          repository healing.
        </p>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          <label>
            Full Name

            <input
              name="full_name"
              value={
                formData.full_name
              }
              onChange={
                handleChange
              }
              required
            />
          </label>

          <label>
            Email

            <input
              name="email"
              type="email"
              value={
                formData.email
              }
              onChange={
                handleChange
              }
              required
              autoComplete="email"
            />
          </label>

          <label>
            Password

            <input
              name="password"
              type="password"
              value={
                formData.password
              }
              onChange={
                handleChange
              }
              required
              minLength="8"
              autoComplete="new-password"
            />
          </label>

          <label>
            Confirm Password

            <input
              name="confirm_password"
              type="password"
              value={
                formData.confirm_password
              }
              onChange={
                handleChange
              }
              required
              minLength="8"
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
              ? "Creating..."
              : "Create Account"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/login">
            Already have an account?
          </Link>
        </div>
      </section>
    </main>
  );
}

export default SignupPage;