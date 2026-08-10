import {
  useEffect,
  useState,
} from "react";

import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  cancelRun,
  deleteRun,
  downloadResults,
  getRun,
  retryRun,
  waitForRunCompletion,
} from "../services/runApi";


const ACTIVE_STATUSES =
  new Set([
    "QUEUED",
    "RUNNING",
    "CANCELLING",
  ]);


function statusClass(
  status = ""
) {
  if (
    [
      "TESTS_PASSED",
      "STATIC_VERIFICATION_PASSED",
      "FIX_VERIFIED",
      "PASSED",
    ].includes(status)
  ) {
    return "status-success";
  }

  if (
    [
      "FAILED",
      "CANCELLED",
      "RETRY_LIMIT_REACHED",
      "ENVIRONMENT_SETUP_FAILED",
      "NO_ACTIONABLE_FIXES",
      "NO_TESTS_FOUND",
    ].includes(status)
  ) {
    return "status-failed";
  }

  if (
    status === "QUEUED"
  ) {
    return "status-queued";
  }

  return "status-running";
}


function readableStatus(
  status
) {
  if (!status) {
    return "N/A";
  }

  if (
    status ===
    "STATIC_VERIFICATION_PASSED"
  ) {
    return (
      "Static Verification Passed"
    );
  }

  return status
    .replaceAll("_", " ");
}


function readableVerification(
  run
) {
  if (
    run?.verification_mode ===
    "STATIC_VERIFICATION"
  ) {
    const commands =
      run?.tests?.commands ||
      [];

    const notebook =
      commands.some(
        (item) =>
          item.framework ===
          "notebook_verify"
      );

    return notebook
      ? "Notebook Static Verification"
      : "Static Verification";
  }

  if (
    run?.verification_mode ===
    "TEST_SUITE"
  ) {
    return "Automated Test Suite";
  }

  return "N/A";
}


function readableCommand(
  command
) {
  if (
    command ===
    "__NOTEBOOK_VERIFY__"
  ) {
    return (
      "Jupyter Notebook Static Verification"
    );
  }

  return (
    command ||
    "Verification Command"
  );
}


function formatDuration(
  seconds
) {
  const value =
    Number(seconds);

  if (
    !Number.isFinite(value)
  ) {
    return "N/A";
  }

  if (value < 60) {
    return `${value.toFixed(2)} sec`;
  }

  const minutes =
    Math.floor(
      value / 60
    );

  const remaining =
    Math.round(
      value % 60
    );

  return (
    `${minutes}m ${remaining}s`
  );
}


function RunDetailPage() {
  const {
    runId,
  } = useParams();

  const navigate =
    useNavigate();

  const [run, setRun] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [
    downloading,
    setDownloading,
  ] = useState(false);

  const [
    cancelling,
    setCancelling,
  ] = useState(false);

  const [
    retrying,
    setRetrying,
  ] = useState(false);

  const [
    deleting,
    setDeleting,
  ] = useState(false);


  async function loadRun() {
    if (!runId) {
      return;
    }

    try {
      setError("");

      const data =
        await getRun(
          runId
        );

      setRun(data);
    } catch (
      loadError
    ) {
      setError(
        loadError.message ||
          "Unable to load run details"
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadRun();
  }, [runId]);


  useEffect(() => {
    if (
      !runId ||
      !ACTIVE_STATUSES.has(
        run?.status
      )
    ) {
      return;
    }

    const timer =
      setInterval(
        async () => {
          try {
            const latest =
              await getRun(
                runId
              );

            setRun(
              latest
            );

            if (
              !ACTIVE_STATUSES.has(
                latest.status
              )
            ) {
              clearInterval(
                timer
              );
            }
          } catch {
            // Keep current data visible.
          }
        },
        3000
      );

    return () =>
      clearInterval(
        timer
      );
  }, [
    runId,
    run?.status,
  ]);


  async function handleDownload() {
    if (!runId) {
      return;
    }

    setDownloading(
      true
    );

    setError("");

    try {
      await downloadResults(
        runId
      );
    } catch (
      downloadError
    ) {
      setError(
        downloadError.message ||
          "Unable to download PDF report"
      );
    } finally {
      setDownloading(
        false
      );
    }
  }


  async function handleCancel() {
    if (!runId) {
      return;
    }

    setCancelling(
      true
    );

    setError("");

    try {
      const result =
        await cancelRun(
          runId
        );

      setRun(
        (current) => ({
          ...current,
          status:
            result.status,
        })
      );
    } catch (
      cancelError
    ) {
      setError(
        cancelError.message ||
          "Unable to cancel run"
      );
    } finally {
      setCancelling(
        false
      );
    }
  }


  async function handleRetry() {
    if (!runId) {
      return;
    }

    const githubToken =
      window.prompt(
        "GitHub token for retry (leave empty for public/read-only run):"
      );

    if (
      githubToken === null
    ) {
      return;
    }

    setRetrying(true);
    setError("");

    try {
      const queued =
        await retryRun(
          runId,
          githubToken || null
        );

      const completed =
        await waitForRunCompletion(
          queued.run_id
        );

      navigate(
        `/runs/${encodeURIComponent(
          completed.run_id
        )}`
      );
    } catch (
      retryError
    ) {
      setError(
        retryError.message ||
          "Unable to retry run"
      );
    } finally {
      setRetrying(false);
    }
  }


  async function handleDelete() {
    if (!runId) {
      return;
    }

    const confirmed =
      window.confirm(
        "Delete this run permanently?"
      );

    if (!confirmed) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      await deleteRun(
        runId
      );

      navigate(
        "/dashboard",
        {
          replace: true,
        }
      );
    } catch (
      deleteError
    ) {
      setError(
        deleteError.message ||
          "Unable to delete run"
      );
    } finally {
      setDeleting(false);
    }
  }


  if (loading) {
    return (
      <main className="app-shell">
        <section className="panel">
          <p>
            Loading run details...
          </p>
        </section>
      </main>
    );
  }


  if (
    error &&
    !run
  ) {
    return (
      <main className="app-shell">
        <section className="panel">
          <div className="error-message">
            {error}
          </div>

          <Link
            to="/dashboard"
            className="profile-link"
          >
            Back to Dashboard
          </Link>
        </section>
      </main>
    );
  }


  if (!run) {
    return null;
  }


  const active =
    ACTIVE_STATUSES.has(
      run.status
    );

  const verificationResults =
    run.verification
      ?.results ||
    run.tests
      ?.execution_results ||
    [];

  const timeline =
    run.iterations
      ?.timeline ||
    [];

  const fixes =
    run.fix_application
      ?.applied_fixes ||
    [];

  const failures =
    run.analysis
      ?.failures ||
    [];

  const git =
    run.git || {};

  const pullRequest =
    run.pull_request || {};

  const cicd =
    run.cicd || {};


  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">
          Autonomous DevOps Platform
        </p>

        <h1>
          Run Details
        </h1>

        <p>
          Complete analysis,
          verification, healing,
          Git and CI/CD report.
        </p>
      </section>


      <section className="panel">
        <div className="run-header">
          <div>
            <p className="eyebrow">
              Run Status
            </p>

            <h2
              className={`run-status ${statusClass(
                run.status
              )}`}
            >
              {readableStatus(
                run.status
              )}
            </h2>
          </div>

          <div className="run-actions">
            <Link
              to="/dashboard"
              className="profile-link"
            >
              Dashboard
            </Link>

            {active ? (
              <button
                type="button"
                className="cancel-button"
                disabled={
                  cancelling
                }
                onClick={
                  handleCancel
                }
              >
                {cancelling
                  ? "Cancelling..."
                  : "Cancel Run"}
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="retry-button"
                  disabled={
                    retrying
                  }
                  onClick={
                    handleRetry
                  }
                >
                  {retrying
                    ? "Retrying..."
                    : "Retry Run"}
                </button>

                <button
                  type="button"
                  className="delete-button"
                  disabled={
                    deleting
                  }
                  onClick={
                    handleDelete
                  }
                >
                  {deleting
                    ? "Deleting..."
                    : "Delete Run"}
                </button>

                <button
                  type="button"
                  className="download-button"
                  disabled={
                    downloading
                  }
                  onClick={
                    handleDownload
                  }
                >
                  {downloading
                    ? "Preparing PDF..."
                    : "Download PDF"}
                </button>
              </>
            )}
          </div>
        </div>


        {error && (
          <div className="error-message">
            {error}
          </div>
        )}


        {run.progress && (
          <div className="run-progress-card">
            <span>
              Current Stage
            </span>

            <strong>
              {run.progress.stage}
            </strong>

            <p>
              {run.progress.message}
            </p>
          </div>
        )}


        <div className="metrics-grid">
          <article>
            <span>
              Final Score
            </span>

            <strong>
              {run.score
                ?.final_score ??
                0}
            </strong>
          </article>

          <article>
            <span>
              Verification
            </span>

            <strong>
              {readableVerification(
                run
              )}
            </strong>
          </article>

          <article>
            <span>
              Iterations
            </span>

            <strong>
              {run.iterations
                ?.used ?? 0}
              /
              {run.iterations
                ?.limit ??
                run.retry_limit ??
                0}
            </strong>
          </article>

          <article>
            <span>
              Fixes Applied
            </span>

            <strong>
              {run.fix_application
                ?.total_applied ??
                0}
            </strong>
          </article>

          <article>
            <span>
              Duration
            </span>

            <strong>
              {formatDuration(
                run.duration_seconds
              )}
            </strong>
          </article>

          <article>
            <span>
              CI/CD
            </span>

            <strong>
              {cicd.status ||
                "NOT_TRIGGERED"}
            </strong>
          </article>
        </div>
      </section>


      <section className="panel">
        <h2>
          Repository
        </h2>

        <div className="detail-grid">
          <article>
            <span>
              Repository URL
            </span>

            <strong>
              {run.repository_url}
            </strong>
          </article>

          <article>
            <span>
              Team
            </span>

            <strong>
              {run.team_name}
            </strong>
          </article>

          <article>
            <span>
              Leader
            </span>

            <strong>
              {run.leader_name}
            </strong>
          </article>

          <article>
            <span>
              Files Scanned
            </span>

            <strong>
              {run.repository
                ?.total_files_scanned ??
                0}
            </strong>
          </article>
        </div>
      </section>


      <section className="panel">
        <h2>
          Verification Logs
        </h2>

        {verificationResults.length ? (
          <div className="timeline-list">
            {verificationResults.map(
              (
                result,
                index
              ) => (
                <article
                  key={
                    `${result.command}-${index}`
                  }
                  className="timeline-item"
                >
                  <div className="run-header">
                    <strong>
                      {readableCommand(
                        result.command
                      )}
                    </strong>

                    <span
                      className={`run-status ${statusClass(
                        result.status
                      )}`}
                    >
                      {readableStatus(
                        result.status
                      )}
                    </span>
                  </div>

                  {result.framework && (
                    <p>
                      Framework:{" "}
                      {result.framework ===
                      "notebook_verify"
                        ? "Jupyter Notebook Verification"
                        : result.framework}
                    </p>
                  )}

                  {result.stdout && (
                    <pre className="log-output">
                      {result.stdout}
                    </pre>
                  )}

                  {result.stderr && (
                    <pre className="log-output error-log">
                      {result.stderr}
                    </pre>
                  )}
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No verification logs available.
          </p>
        )}
      </section>


      <section className="panel">
        <h2>
          Healing Timeline
        </h2>

        {timeline.length ? (
          <div className="timeline-list">
            {timeline.map(
              (
                item,
                index
              ) => (
                <article
                  className="timeline-item"
                  key={
                    `${item.iteration}-${index}`
                  }
                >
                  <div>
                    <span>
                      Iteration{" "}
                      {item.iteration}
                    </span>

                    <strong>
                      {readableStatus(
                        item.status
                      )}
                    </strong>
                  </div>

                  <p>
                    Verification:{" "}
                    {item.verification_mode ===
                    "STATIC_VERIFICATION"
                      ? "Static / Notebook"
                      : item.verification_mode ===
                          "TEST_SUITE"
                        ? "Test Suite"
                        : "N/A"}
                  </p>

                  <p>
                    Fixes applied:{" "}
                    {item.fixes_applied ??
                      0}
                  </p>
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No healing iterations recorded.
          </p>
        )}
      </section>


      <section className="panel">
        <h2>
          Detected Failures
        </h2>

        {failures.length ? (
          <div className="timeline-list">
            {failures.map(
              (
                failure,
                index
              ) => (
                <article
                  className="timeline-item"
                  key={index}
                >
                  <strong>
                    {failure.type ||
                      failure.failure_type ||
                      "Failure"}
                  </strong>

                  <p>
                    {failure.message ||
                      failure.detail ||
                      JSON.stringify(
                        failure
                      )}
                  </p>
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No failures detected.
          </p>
        )}
      </section>


      <section className="panel">
        <h2>
          Applied Fixes
        </h2>

        {fixes.length ? (
          <div className="timeline-list">
            {fixes.map(
              (
                fix,
                index
              ) => (
                <article
                  className="timeline-item"
                  key={index}
                >
                  <strong>
                    Fix {index + 1}
                  </strong>

                  <p>
                    File:{" "}
                    {fix.file ||
                      fix.file_path ||
                      "N/A"}
                  </p>

                  <p>
                    Status:{" "}
                    {fix.apply_status ||
                      "N/A"}
                  </p>

                  {fix.reason && (
                    <p>
                      Reason:{" "}
                      {fix.reason}
                    </p>
                  )}
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            No fixes were required.
          </p>
        )}
      </section>


      <section className="panel">
        <h2>
          Git Automation
        </h2>

        <div className="detail-grid">
          <article>
            <span>
              Branch
            </span>

            <strong>
              {git.branch_name ||
                "Not created"}
            </strong>
          </article>

          <article>
            <span>
              Commit
            </span>

            <strong>
              {git.commit_sha ||
                "N/A"}
            </strong>
          </article>

          <article>
            <span>
              Push Status
            </span>

            <strong>
              {git.push_status ||
                "NOT_TRIGGERED"}
            </strong>
          </article>
        </div>
      </section>


      <section className="panel">
        <h2>
          Pull Request
        </h2>

        <div className="detail-grid">
          <article>
            <span>
              PR Number
            </span>

            <strong>
              {pullRequest.number ??
                "Not created"}
            </strong>
          </article>

          <article>
            <span>
              State
            </span>

            <strong>
              {pullRequest.state ||
                pullRequest.status ||
                "NOT_TRIGGERED"}
            </strong>
          </article>

          <article>
            <span>
              Title
            </span>

            <strong>
              {pullRequest.title ||
                "N/A"}
            </strong>
          </article>
        </div>

        {pullRequest.url && (
          <a
            href={
              pullRequest.url
            }
            target="_blank"
            rel="noreferrer"
            className="profile-link"
          >
            Open Pull Request
          </a>
        )}
      </section>


      <section className="panel">
        <h2>
          CI/CD Timeline
        </h2>

        {cicd.timeline
          ?.length ? (
          <div className="timeline-list">
            {cicd.timeline.map(
              (
                item,
                index
              ) => (
                <article
                  className="timeline-item"
                  key={index}
                >
                  <strong>
                    {item.name ||
                      "GitHub Actions"}
                  </strong>

                  <p>
                    Status:{" "}
                    {item.status ||
                      "N/A"}
                  </p>

                  <p>
                    Conclusion:{" "}
                    {item.conclusion ||
                      "Pending"}
                  </p>

                  {item.workflow_url && (
                    <a
                      href={
                        item.workflow_url
                      }
                      target="_blank"
                      rel="noreferrer"
                      className="profile-link"
                    >
                      Open Workflow
                    </a>
                  )}
                </article>
              )
            )}
          </div>
        ) : (
          <p className="empty-state">
            CI/CD was not triggered for this run.
          </p>
        )}
      </section>
    </main>
  );
}


export default RunDetailPage;