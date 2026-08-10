import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  getActivity,
} from "../services/runApi";


function formatAction(
  action = ""
) {
  return action
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function ActivityPage() {
  const [activity, setActivity] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    let active = true;

    async function loadActivity() {
      try {
        const data =
          await getActivity();

        if (active) {
          setActivity(
            data.activity ||
              []
          );
        }
      } catch (loadError) {
        if (active) {
          setError(
            loadError.message ||
              "Unable to load activity"
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadActivity();

    return () => {
      active = false;
    };
  }, []);


  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">
          Audit Trail
        </p>

        <h1>
          Activity
        </h1>

        <p>
          Review important actions performed
          through your account.
        </p>

        <div className="run-detail-navigation">
          <Link
            to="/"
            className="profile-link"
          >
            Back to Dashboard
          </Link>
        </div>
      </section>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <section className="panel">
        <div className="run-header">
          <div>
            <p className="eyebrow">
              Recent Events
            </p>

            <h2>
              Account Activity
            </h2>
          </div>

          <span className="activity-count">
            {activity.length} events
          </span>
        </div>

        {loading ? (
          <p className="empty-state">
            Loading activity...
          </p>
        ) : activity.length ? (
          <div className="activity-list">
            {activity.map(
              (item) => (
                <article
                  className="activity-card"
                  key={
                    item.id
                  }
                >
                  <div className="activity-icon">
                    •
                  </div>

                  <div className="activity-content">
                    <strong>
                      {formatAction(
                        item.action
                      )}
                    </strong>

                    <span>
                      {
                        item.entity_type
                      }
                      {item.entity_id
                        ? ` · ${item.entity_id}`
                        : ""}
                    </span>

                    {item.details
                      ?.repository_url && (
                      <p>
                        {
                          item.details
                            .repository_url
                        }
                      </p>
                    )}
                  </div>

                  <time>
                    {item.created_at
                      ? new Date(
                          item.created_at
                        )
                          .toLocaleString()
                      : ""}
                  </time>
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No activity recorded yet.
          </p>
        )}
      </section>
    </main>
  );
}

export default ActivityPage;