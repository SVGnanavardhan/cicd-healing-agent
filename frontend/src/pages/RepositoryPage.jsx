import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

import {
  getRuns,
} from "../services/runApi";


function getRepositoryName(
  repositoryUrl = ""
) {
  return (
    repositoryUrl
      .replace(/\.git$/, "")
      .split("/")
      .filter(Boolean)
      .pop() ||
    ""
  );
}


function RepositoryPage() {
  const {
    repositoryName,
  } = useParams();

  const [runs, setRuns] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    async function loadRepositoryRuns() {
      setLoading(true);

      try {
        const data =
          await getRuns({
            page: 1,
            pageSize: 100,
            statusFilter: "ALL",
            searchQuery:
              repositoryName,
          });

        setRuns(
          data.runs || []
        );
      } catch (loadError) {
        setError(
          loadError.message ||
            "Unable to load repository"
        );
      } finally {
        setLoading(false);
      }
    }

    loadRepositoryRuns();
  }, [
    repositoryName,
  ]);


  const repositoryRuns =
    useMemo(
      () =>
        runs.filter(
          (run) =>
            getRepositoryName(
              run.repository_url
            ) ===
            repositoryName
        ),
      [
        runs,
        repositoryName,
      ]
    );


  const successful =
    repositoryRuns.filter(
      (run) =>
        [
          "TESTS_PASSED",
          "FIX_VERIFIED",
        ].includes(
          run.status
        )
    ).length;


  const totalFixes =
    repositoryRuns.reduce(
      (
        total,
        run
      ) =>
        total +
        (
          run.fix_application
            ?.total_applied ||
          0
        ),
      0
    );


  const totalPRs =
    repositoryRuns.filter(
      (run) =>
        [
          "CREATED",
          "ALREADY_EXISTS",
        ].includes(
          run.pull_request
            ?.status
        )
    ).length;


  const successRate =
    repositoryRuns.length
      ? Math.round(
          (
            successful /
            repositoryRuns.length
          ) *
            100
        )
      : 0;


  const latestRun =
    repositoryRuns[0];


  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">
          Repository Workspace
        </p>

        <h1>
          {repositoryName}
        </h1>

        <p>
          Repository-specific healing history,
          fixes and CI/CD performance.
        </p>

        <div className="run-detail-navigation">
          <Link
            to="/"
            className="profile-link"
          >
            Back to Dashboard
          </Link>

          {latestRun
            ?.repository_url && (
            <a
              href={
                latestRun.repository_url
              }
              target="_blank"
              rel="noreferrer"
              className="profile-link"
            >
              Open GitHub
            </a>
          )}
        </div>
      </section>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <section className="analytics-grid">
        <article>
          <span>Total Runs</span>
          <strong>
            {repositoryRuns.length}
          </strong>
        </article>

        <article>
          <span>Success Rate</span>
          <strong>
            {successRate}%
          </strong>
        </article>

        <article>
          <span>Total Fixes</span>
          <strong>
            {totalFixes}
          </strong>
        </article>

        <article>
          <span>Pull Requests</span>
          <strong>
            {totalPRs}
          </strong>
        </article>
      </section>

      <section className="panel">
        <h2>
          Healing Runs
        </h2>

        {loading ? (
          <p className="empty-state">
            Loading...
          </p>
        ) : repositoryRuns.length ? (
          <div className="history-list">
            {repositoryRuns.map(
              (run) => (
                <article
                  className="repository-run-card"
                  key={
                    run.run_id
                  }
                >
                  <div>
                    <span>Status</span>

                    <strong>
                      {run.status}
                    </strong>
                  </div>

                  <div>
                    <span>Score</span>

                    <strong>
                      {run.score
                        ?.final_score ??
                        0}
                    </strong>
                  </div>

                  <div>
                    <span>Fixes</span>

                    <strong>
                      {run
                        .fix_application
                        ?.total_applied ??
                        0}
                    </strong>
                  </div>

                  <div>
                    <span>Details</span>

                    <Link
                      to={`/runs/${encodeURIComponent(
                        run.run_id
                      )}`}
                      className="repository-link"
                    >
                      View Run
                    </Link>
                  </div>
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No repository runs found.
          </p>
        )}
      </section>
    </main>
  );
}

export default RepositoryPage;