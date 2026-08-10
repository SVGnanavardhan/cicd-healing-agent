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

import {
  supabase,
} from "../services/supabaseClient";


function SettingsPage() {
  const {
    user,
  } = useAuth();

  const [settings, setSettings] =
    useState({
      default_team_name: "",
      default_leader_name: "",
      default_retry_limit: 5,
      browser_notifications: true,
    });

  const [
    initialLoading,
    setInitialLoading,
  ] = useState(true);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  useEffect(() => {
    let active = true;

    async function loadSettings() {
      if (!user?.id) {
        setInitialLoading(false);
        return;
      }

      try {
        const {
          data,
          error:
            loadError,
        } = await supabase
          .from(
            "user_settings"
          )
          .select("*")
          .eq(
            "user_id",
            user.id
          )
          .maybeSingle();

        if (loadError) {
          throw loadError;
        }

        if (
          active &&
          data
        ) {
          setSettings({
            default_team_name:
              data.default_team_name ||
              "",

            default_leader_name:
              data.default_leader_name ||
              "",

            default_retry_limit:
              data.default_retry_limit ||
              5,

            browser_notifications:
              data.browser_notifications ??
              true,
          });
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError.message ||
              "Unable to load settings"
          );
        }
      } finally {
        if (active) {
          setInitialLoading(
            false
          );
        }
      }
    }

    loadSettings();

    return () => {
      active = false;
    };
  }, [
    user?.id,
  ]);


  function handleChange(
    event
  ) {
    const {
      name,
      value,
      checked,
      type,
    } = event.target;

    setSettings(
      (current) => ({
        ...current,

        [name]:
          type ===
          "checkbox"
            ? checked
            : name ===
                "default_retry_limit"
              ? Number(value)
              : value,
      })
    );
  }


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    if (!user?.id) {
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const {
        error:
          saveError,
      } = await supabase
        .from(
          "user_settings"
        )
        .upsert(
          {
            user_id:
              user.id,

            ...settings,

            updated_at:
              new Date()
                .toISOString(),
          },
          {
            onConflict:
              "user_id",
          }
        );

      if (saveError) {
        throw saveError;
      }

      setMessage(
        "Settings saved successfully."
      );
    } catch (saveError) {
      setError(
        saveError.message ||
          "Unable to save settings"
      );
    } finally {
      setLoading(false);
    }
  }


  if (initialLoading) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <h1>
            Loading settings...
          </h1>
        </section>
      </main>
    );
  }


  return (
    <main className="auth-shell">
      <section className="auth-card settings-card">
        <p className="eyebrow">
          Preferences
        </p>

        <h1>
          Settings
        </h1>

        <form
          className="auth-form"
          onSubmit={
            handleSubmit
          }
        >
          <label>
            Default Team Name

            <input
              name="default_team_name"
              value={
                settings.default_team_name
              }
              onChange={
                handleChange
              }
            />
          </label>

          <label>
            Default Leader Name

            <input
              name="default_leader_name"
              value={
                settings.default_leader_name
              }
              onChange={
                handleChange
              }
            />
          </label>

          <label>
            Default Retry Limit

            <input
              name="default_retry_limit"
              type="number"
              min="1"
              max="10"
              value={
                settings.default_retry_limit
              }
              onChange={
                handleChange
              }
            />
          </label>

          <label className="settings-checkbox">
            <input
              name="browser_notifications"
              type="checkbox"
              checked={
                settings.browser_notifications
              }
              onChange={
                handleChange
              }
            />

            <span>
              Enable browser notifications
            </span>
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
              : "Save Settings"}
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

export default SettingsPage;