import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";


function ProfilePage() {
  const {
    user,
    profile,
    updateProfile,
  } = useAuth();

  const [formData, setFormData] =
    useState({
      full_name: "",
      github_username: "",
      avatar_url: "",
    });

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  useEffect(() => {
    setFormData({
      full_name:
        profile?.full_name ||
        user?.user_metadata
          ?.full_name ||
        "",

      github_username:
        profile
          ?.github_username ||
        "",

      avatar_url:
        profile?.avatar_url ||
        "",
    });
  }, [
    profile,
    user,
  ]);


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
        [name]: value,
      })
    );
  }


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await updateProfile(
        formData
      );

      setMessage(
        "Profile updated successfully."
      );
    } catch (updateError) {
      setError(
        updateError.message ||
          "Unable to update profile"
      );
    } finally {
      setLoading(false);
    }
  }


  const initial =
    (
      formData.full_name ||
      user?.email ||
      "U"
    )
      .charAt(0)
      .toUpperCase();


  return (
    <main className="auth-shell">
      <section className="auth-card profile-card">
        <p className="eyebrow">
          Account
        </p>

        <h1>
          Profile
        </h1>

        <div className="profile-avatar-wrapper">
          {formData.avatar_url ? (
            <img
              src={
                formData.avatar_url
              }
              alt="Profile"
              className="profile-avatar"
            />
          ) : (
            <div className="profile-avatar-placeholder">
              {initial}
            </div>
          )}
        </div>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          <label>
            Email

            <input
              value={
                user?.email ||
                ""
              }
              disabled
            />
          </label>

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
            />
          </label>

          <label>
            GitHub Username

            <input
              name="github_username"
              value={
                formData.github_username
              }
              onChange={
                handleChange
              }
            />
          </label>

          <label>
            Avatar URL

            <input
              name="avatar_url"
              type="url"
              value={
                formData.avatar_url
              }
              onChange={
                handleChange
              }
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
              ? "Saving..."
              : "Save Profile"}
          </button>
        </form>

        <div className="auth-links">
          <Link to="/">
            Back to Dashboard
          </Link>
        </div>
      </section>
    </main>
  );
}

export default ProfilePage;