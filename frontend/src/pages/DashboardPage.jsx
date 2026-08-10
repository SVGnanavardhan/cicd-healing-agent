import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../contexts/AuthContext";

import {
  getPinnedRepositories,
  pinRepository,
  unpinRepository,
} from "../services/repositoryPreferenceApi";

import {
  cancelRun,
  createRun,
  deleteRun,
  downloadResults,
  getAnalytics,
  getRuns,
  retryRun,
  verifyGitHubToken,
  verifyRepositoryAccess,
  waitForRunCompletion,
} from "../services/runApi";

import {
  supabase,
} from "../services/supabaseClient";


const ACTIVE_STATUSES = new Set([
  "QUEUED",
  "RUNNING",
  "CANCELLING",
]);


function getStatusClass(
  status = ""
) {
  if (status === "QUEUED") {
    return "status-queued";
  }

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

  return "status-running";
}


function getRepositoryName(
  repositoryUrl = ""
) {
  return (
    repositoryUrl
      .replace(/\.git$/, "")
      .split("/")
      .filter(Boolean)
      .pop() ||
    "repository"
  );
}


async function requestNotificationPermission() {
  if (!("Notification" in window)) {
    return false;
  }

  if (
    Notification.permission ===
    "granted"
  ) {
    return true;
  }

  if (
    Notification.permission ===
    "denied"
  ) {
    return false;
  }

  const permission =
    await Notification.requestPermission();

  return permission === "granted";
}


function sendCompletionNotification(
  run
) {
  if (
    !("Notification" in window)
    || Notification.permission !==
      "granted"
  ) {
    return;
  }

  new Notification(
    "CI/CD Healing Run Completed",
    {
      body: `${run.status} · ${getRepositoryName(
        run.repository_url
      )}`,
    }
  );
}


function DashboardPage() {
  const navigate =
    useNavigate();

  const {
    user,
    profile,
    signOut,
  } = useAuth();

  const [formData, setFormData] =
    useState({
      repository_url: "",
      team_name: "",
      leader_name: "",
      retry_limit: 5,
      github_token: "",
    });

  const [runs, setRuns] =
    useState([]);

  const [
    selectedRun,
    setSelectedRun,
  ] = useState(null);

  const [
    githubConnection,
    setGithubConnection,
  ] = useState(null);

  const [
    repositoryAccess,
    setRepositoryAccess,
  ] = useState(null);

  const [
    pinnedRepositories,
    setPinnedRepositories,
  ] = useState(new Set());

  const [analytics, setAnalytics] =
    useState({
      total_runs: 0,
      successful_runs: 0,
      failed_runs: 0,
      cancelled_runs: 0,
      success_rate: 0,
      total_fixes: 0,
      total_pull_requests: 0,
      average_duration_seconds: 0,
    });

  const [loading, setLoading] =
    useState(false);

  const [
    verifyingToken,
    setVerifyingToken,
  ] = useState(false);

  const [
    verifyingRepository,
    setVerifyingRepository,
  ] = useState(false);

  const [
    cancelling,
    setCancelling,
  ] = useState(false);

  const [retrying, setRetrying] =
    useState(false);

  const [deleting, setDeleting] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    searchQuery,
    setSearchQuery,
  ] = useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] = useState("ALL");

  const [
    currentPage,
    setCurrentPage,
  ] = useState(1);

  const [
    totalPages,
    setTotalPages,
  ] = useState(1);

  const [
    totalRunsCount,
    setTotalRunsCount,
  ] = useState(0);

  const [
    browserNotifications,
    setBrowserNotifications,
  ] = useState(true);

  const runsPerPage = 5;


  async function loadSettings() {
    if (!user?.id) {
      return;
    }

    try {
      const {
        data,
        error:
          settingsError,
      } = await supabase
        .from("user_settings")
        .select("*")
        .eq(
          "user_id",
          user.id
        )
        .maybeSingle();

      if (settingsError) {
        console.error(
          settingsError.message
        );
        return;
      }

      if (!data) {
        return;
      }

      setBrowserNotifications(
        data.browser_notifications ??
          true
      );

      setFormData(
        (current) => ({
          ...current,

          team_name:
            current.team_name ||
            data.default_team_name ||
            "",

          leader_name:
            current.leader_name ||
            data.default_leader_name ||
            "",

          retry_limit:
            data.default_retry_limit ||
            current.retry_limit,
        })
      );
    } catch (settingsError) {
      console.error(
        settingsError
      );
    }
  }


  async function loadRuns() {
    try {
      const data =
        await getRuns({
          page:
            currentPage,

          pageSize:
            runsPerPage,

          statusFilter,

          searchQuery,
        });

      setRuns(
        data.runs || []
      );

      setTotalRunsCount(
        data.total || 0
      );

      setTotalPages(
        data.total_pages || 1
      );
    } catch (loadError) {
      setError(
        loadError.message ||
          "Unable to load run history"
      );
    }
  }


  async function loadAnalytics() {
    try {
      const data =
        await getAnalytics();

      setAnalytics(data);
    } catch (analyticsError) {
      console.error(
        analyticsError
      );
    }
  }


  async function loadPinnedRepositories() {
    if (!user?.id) {
      return;
    }

    try {
      const data =
        await getPinnedRepositories(
          user.id
        );

      setPinnedRepositories(
        new Set(
          data.map(
            (item) =>
              item.repository_url
          )
        )
      );
    } catch (pinError) {
      console.error(
        pinError
      );
    }
  }


  useEffect(() => {
    loadSettings();
    loadAnalytics();
    loadPinnedRepositories();
  }, [user?.id]);


  useEffect(() => {
    const timer =
      setTimeout(
        () => {
          loadRuns();
        },
        300
      );

    return () =>
      clearTimeout(timer);
  }, [
    currentPage,
    statusFilter,
    searchQuery,
  ]);


  useEffect(() => {
    setCurrentPage(1);
  }, [
    searchQuery,
    statusFilter,
  ]);


  function handleChange(
    event
  ) {
    const {
      name,
      value,
    } = event.target;

    if (
      name === "github_token"
    ) {
      setGithubConnection(null);
      setRepositoryAccess(null);
    }

    if (
      name === "repository_url"
    ) {
      setRepositoryAccess(null);
    }

    setFormData(
      (current) => ({
        ...current,

        [name]:
          name === "retry_limit"
            ? Number(value)
            : value,
      })
    );
  }


  async function handleLogout() {
    try {
      await signOut();

      navigate(
        "/login",
        {
          replace: true,
        }
      );
    } catch (logoutError) {
      setError(
        logoutError.message ||
          "Logout failed"
      );
    }
  }


  async function handleVerifyToken() {
    const token =
      formData.github_token.trim();

    if (!token) {
      setError(
        "Enter a GitHub token first."
      );
      return;
    }

    setVerifyingToken(true);
    setError("");

    try {
      const data =
        await verifyGitHubToken(
          token
        );

      setGithubConnection(
        data.github
      );

      setRepositoryAccess(null);
    } catch (verifyError) {
      setGithubConnection(null);

      setError(
        verifyError.message ||
          "GitHub verification failed"
      );
    } finally {
      setVerifyingToken(false);
    }
  }


  async function handleRepositoryAccess() {
    if (!githubConnection) {
      setError(
        "Verify GitHub token first."
      );
      return;
    }

    const repositoryUrl =
      formData.repository_url.trim();

    const githubToken =
      formData.github_token.trim();

    if (!repositoryUrl) {
      setError(
        "Enter repository URL."
      );
      return;
    }

    setVerifyingRepository(true);
    setError("");

    try {
      const data =
        await verifyRepositoryAccess(
          repositoryUrl,
          githubToken
        );

      setRepositoryAccess(
        data.repository
      );
    } catch (accessError) {
      setRepositoryAccess(null);

      setError(
        accessError.message ||
          "Repository access verification failed"
      );
    } finally {
      setVerifyingRepository(false);
    }
  }


  async function handleSubmit(
    event
  ) {
    event.preventDefault();

    const githubToken =
      formData.github_token.trim();

    if (
      githubToken &&
      !githubConnection
    ) {
      setError(
        "Verify the GitHub token before running the agent."
      );
      return;
    }

    if (
      githubToken &&
      !repositoryAccess
    ) {
      setError(
        "Check repository access before running the agent."
      );
      return;
    }

    setLoading(true);
    setError("");
    setSelectedRun(null);

    try {
      if (browserNotifications) {
        await requestNotificationPermission();
      }

      const queuedRun =
        await createRun({
          repository_url:
            formData.repository_url.trim(),

          team_name:
            formData.team_name.trim(),

          leader_name:
            formData.leader_name.trim(),

          retry_limit:
            formData.retry_limit,

          github_token:
            githubToken || null,
        });

      setSelectedRun(
        queuedRun
      );

      const completedRun =
        await waitForRunCompletion(
          queuedRun.run_id,
          (updatedRun) => {
            setSelectedRun(
              updatedRun
            );
          }
        );

      setSelectedRun(
        completedRun
      );

      if (
        browserNotifications
      ) {
        sendCompletionNotification(
          completedRun
        );
      }

      await Promise.all([
        loadRuns(),
        loadAnalytics(),
      ]);
    } catch (submitError) {
      setError(
        submitError.message ||
          "Run failed"
      );
    } finally {
      setLoading(false);

      setGithubConnection(null);
      setRepositoryAccess(null);

      setFormData(
        (current) => ({
          ...current,
          github_token: "",
        })
      );
    }
  }


  async function handleCancelRun() {
    if (!selectedRun?.run_id) {
      return;
    }

    setCancelling(true);
    setError("");

    try {
      const result =
        await cancelRun(
          selectedRun.run_id
        );

      setSelectedRun(
        (current) => ({
          ...current,
          status:
            result.status,
        })
      );
    } catch (cancelError) {
      setError(
        cancelError.message ||
          "Unable to cancel run"
      );
    } finally {
      setCancelling(false);
    }
  }


  async function handleRetryRun() {
    if (!selectedRun?.run_id) {
      return;
    }

    setRetrying(true);
    setError("");

    try {
      const queuedRun =
        await retryRun(
          selectedRun.run_id,
          formData.github_token
        );

      setSelectedRun(
        queuedRun
      );

      const completedRun =
        await waitForRunCompletion(
          queuedRun.run_id,
          setSelectedRun
        );

      setSelectedRun(
        completedRun
      );

      if (
        browserNotifications
      ) {
        sendCompletionNotification(
          completedRun
        );
      }

      await Promise.all([
        loadRuns(),
        loadAnalytics(),
      ]);
    } catch (retryError) {
      setError(
        retryError.message ||
          "Unable to retry run"
      );
    } finally {
      setRetrying(false);
    }
  }


  async function handleDeleteRun() {
    if (!selectedRun?.run_id) {
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
        selectedRun.run_id
      );

      setSelectedRun(null);

      await Promise.all([
        loadRuns(),
        loadAnalytics(),
      ]);
    } catch (deleteError) {
      setError(
        deleteError.message ||
          "Unable to delete run"
      );
    } finally {
      setDeleting(false);
    }
  }


  async function handleDownload() {
    if (!selectedRun?.run_id) {
      return;
    }

    try {
      await downloadResults(
        selectedRun.run_id
      );
    } catch (downloadError) {
      setError(
        downloadError.message ||
          "Download failed"
      );
    }
  }


  async function handleTogglePin(
    repositoryUrl
  ) {
    if (!user?.id) {
      return;
    }

    const currentlyPinned =
      pinnedRepositories.has(
        repositoryUrl
      );

    try {
      if (currentlyPinned) {
        await unpinRepository(
          user.id,
          repositoryUrl
        );
      } else {
        await pinRepository(
          user.id,
          repositoryUrl
        );
      }

      setPinnedRepositories(
        (current) => {
          const updated =
            new Set(current);

          if (currentlyPinned) {
            updated.delete(
              repositoryUrl
            );
          } else {
            updated.add(
              repositoryUrl
            );
          }

          return updated;
        }
      );
    } catch (pinError) {
      setError(
        pinError.message ||
          "Unable to update repository pin"
      );
    }
  }


  const sortedRuns =
    useMemo(() => {
      return [...runs].sort(
        (
          first,
          second
        ) => {
          const firstPinned =
            pinnedRepositories.has(
              first.repository_url
            );

          const secondPinned =
            pinnedRepositories.has(
              second.repository_url
            );

          return (
            Number(secondPinned) -
            Number(firstPinned)
          );
        }
      );
    }, [
      runs,
      pinnedRepositories,
    ]);


  const runIsActive =
    ACTIVE_STATUSES.has(
      selectedRun?.status
    );


  return (
    <main className="app-shell">
      <section className="hero">
        <div className="dashboard-user-bar">
          <div>
            <span>
              Signed in as
            </span>

            <strong>
              {profile?.full_name ||
                user?.email}
            </strong>
          </div>

          <div className="dashboard-user-actions">
            <Link
              to="/profile"
              className="profile-link"
            >
              Profile
            </Link>

            <Link
              to="/activity"
              className="profile-link"
            >
              Activity
            </Link>

            <Link
              to="/settings"
              className="profile-link"
            >
              Settings
            </Link>

            <button
              type="button"
              onClick={
                handleLogout
              }
            >
              Logout
            </button>
          </div>
        </div>

        <p className="eyebrow">
          Autonomous DevOps Platform
        </p>

        <h1>
          CI/CD Healing Agent
        </h1>

        <p>
          Detect failures, generate deterministic
          fixes, verify changes, automate GitHub
          workflows and monitor CI.
        </p>
      </section>


      <section className="analytics-grid">
        <article>
          <span>Total Runs</span>
          <strong>
            {analytics.total_runs}
          </strong>
        </article>

        <article>
          <span>Success Rate</span>
          <strong>
            {analytics.success_rate}%
          </strong>
        </article>

        <article>
          <span>Total Fixes</span>
          <strong>
            {analytics.total_fixes}
          </strong>
        </article>

        <article>
          <span>Pull Requests</span>
          <strong>
            {
              analytics.total_pull_requests
            }
          </strong>
        </article>
      </section>


      <section className="panel">
        <h2>
          Start Analysis
        </h2>

        {githubConnection && (
          <div className="github-connection-card">
            {githubConnection.avatar_url && (
              <img
                src={
                  githubConnection.avatar_url
                }
                alt=""
              />
            )}

            <div>
              <span>
                GitHub connected as
              </span>

              <strong>
                {githubConnection.login}
              </strong>
            </div>
          </div>
        )}

        <form
          className="run-form"
          onSubmit={
            handleSubmit
          }
        >
          <input
            name="repository_url"
            type="url"
            placeholder="https://github.com/owner/repository"
            value={
              formData.repository_url
            }
            onChange={
              handleChange
            }
            required
          />

          <input
            name="team_name"
            placeholder="Team name"
            value={
              formData.team_name
            }
            onChange={
              handleChange
            }
            required
          />

          <input
            name="leader_name"
            placeholder="Leader name"
            value={
              formData.leader_name
            }
            onChange={
              handleChange
            }
            required
          />

          <input
            name="retry_limit"
            type="number"
            min="1"
            max="10"
            value={
              formData.retry_limit
            }
            onChange={
              handleChange
            }
          />

          <div className="github-token-field">
            <input
              name="github_token"
              type="password"
              placeholder="GitHub token (optional)"
              value={
                formData.github_token
              }
              onChange={
                handleChange
              }
              autoComplete="off"
            />

            <button
              type="button"
              className="secondary-button"
              onClick={
                handleVerifyToken
              }
              disabled={
                verifyingToken ||
                !formData.github_token.trim()
              }
            >
              {verifyingToken
                ? "Verifying..."
                : "Verify Token"}
            </button>
          </div>

          {githubConnection && (
            <button
              type="button"
              className="secondary-button"
              onClick={
                handleRepositoryAccess
              }
              disabled={
                verifyingRepository
              }
            >
              {verifyingRepository
                ? "Checking..."
                : "Check Repository Access"}
            </button>
          )}

          {repositoryAccess && (
            <div className="repository-access-card">
              <div>
                <span>Repository</span>
                <strong>
                  {repositoryAccess.full_name}
                </strong>
              </div>

              <div>
                <span>Visibility</span>
                <strong>
                  {repositoryAccess.private
                    ? "Private"
                    : "Public"}
                </strong>
              </div>

              <div>
                <span>Read</span>
                <strong>
                  {repositoryAccess.permissions
                    ?.can_read
                    ? "Allowed"
                    : "Denied"}
                </strong>
              </div>

              <div>
                <span>Push</span>
                <strong>
                  {repositoryAccess.permissions
                    ?.can_push
                    ? "Allowed"
                    : "Denied"}
                </strong>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Healing Repository..."
              : "Run Agent"}
          </button>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </section>


      {selectedRun && (
        <section className="panel">
          <div className="run-header">
            <div>
              <p className="eyebrow">
                Latest Run
              </p>

              <h2
                className={`run-status ${getStatusClass(
                  selectedRun.status
                )}`}
              >
                {selectedRun.status}
              </h2>
            </div>

            <div className="run-actions">
              {runIsActive ? (
                <button
                  type="button"
                  className="cancel-button"
                  onClick={
                    handleCancelRun
                  }
                  disabled={
                    cancelling
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
                    onClick={
                      handleRetryRun
                    }
                    disabled={
                      retrying
                    }
                  >
                    {retrying
                      ? "Retrying..."
                      : "Retry Run"}
                  </button>

                  <button
                    type="button"
                    className="delete-button"
                    onClick={
                      handleDeleteRun
                    }
                    disabled={
                      deleting
                    }
                  >
                    {deleting
                      ? "Deleting..."
                      : "Delete Run"}
                  </button>
                </>
              )}

              {selectedRun.results_file && (
                <button
                  type="button"
                  className="download-button"
                  onClick={
                    handleDownload
                  }
                >
                  Download Results
                </button>
              )}
            </div>
          </div>

          {selectedRun.progress && (
            <div className="run-progress-card">
              <span>
                Current Stage
              </span>

              <strong>
                {selectedRun.progress.stage}
              </strong>

              <p>
                {selectedRun.progress.message}
              </p>
            </div>
          )}

          {selectedRun.error && (
            <div className="error-message">
              <strong>
                {selectedRun.error.type ||
                  "Run Error"}
              </strong>

              <p>
                {selectedRun.error.message}
              </p>
            </div>
          )}

          <div className="metrics-grid">
            <article>
              <span>
                Final Score
              </span>

              <strong>
                {selectedRun.score
                  ?.final_score ?? 0}
              </strong>
            </article>

            <article>
              <span>
                Iterations
              </span>

              <strong>
                {selectedRun.iterations
                  ?.used ?? 0}
                /
                {selectedRun.iterations
                  ?.limit ??
                  selectedRun.retry_limit ??
                  0}
              </strong>
            </article>

            <article>
              <span>
                Fixes Applied
              </span>

              <strong>
                {selectedRun
                  .fix_application
                  ?.total_applied ?? 0}
              </strong>
            </article>
            <article>
              <span>
                Verification
              </span>

              <strong>
                {selectedRun.verification_mode ===
                "STATIC_VERIFICATION"
                  ? "Static / Notebook"
                  : selectedRun.verification_mode ===
                      "TEST_SUITE"
                    ? "Test Suite"
                    : "N/A"}
              </strong>
            </article>
            <article>
              <span>
                CI/CD
              </span>

              <strong>
                {selectedRun.cicd
                  ?.status ||
                  "NOT_TRIGGERED"}
              </strong>
            </article>
          </div>

          <div className="run-actions">
            <Link
              className="profile-link"
              to={`/runs/${encodeURIComponent(
                selectedRun.run_id
              )}`}
            >
              View Full Details
            </Link>

            <Link
              className="profile-link"
              to={`/repositories/${encodeURIComponent(
                getRepositoryName(
                  selectedRun.repository_url
                )
              )}`}
            >
              Repository Workspace
            </Link>
          </div>
        </section>
      )}


      <section className="panel">
        <div className="run-header">
          <div>
            <p className="eyebrow">
              History
            </p>

            <h2>
              Run History
            </h2>
          </div>

          <span className="activity-count">
            {totalRunsCount} runs
          </span>
        </div>

        <div className="history-controls">
          <input
            type="search"
            placeholder="Search repository"
            value={
              searchQuery
            }
            onChange={
              (event) =>
                setSearchQuery(
                  event.target.value
                )
            }
          />

          <select
            value={
              statusFilter
            }
            onChange={
              (event) =>
                setStatusFilter(
                  event.target.value
                )
            }
          >
            <option value="ALL">
              All statuses
            </option>

            <option value="TESTS_PASSED">
              Tests Passed
            </option>

            <option value="FIX_VERIFIED">
              Fix Verified
            </option>

            <option value="FAILED">
              Failed
            </option>

            <option value="CANCELLED">
              Cancelled
            </option>

            <option value="NO_ACTIONABLE_FIXES">
              No Actionable Fixes
            </option>

            <option value="NO_TESTS_FOUND">
              No Tests Found
            </option>
            <option value="STATIC_VERIFICATION_PASSED">
              Static Verification Passed
            </option>
            <option value="ENVIRONMENT_SETUP_FAILED">
              Environment Failed
            </option>
          </select>
        </div>

        <div className="history-list">
          {sortedRuns.length ? (
            sortedRuns.map(
              (run) => {
                const pinned =
                  pinnedRepositories.has(
                    run.repository_url
                  );

                return (
                  <article
                    className="history-item"
                    key={
                      run.run_id
                    }
                    onClick={() =>
                      setSelectedRun(
                        run
                      )
                    }
                  >
                    <div>
                      <strong>
                        {run.status}
                      </strong>

                      <span>
                        {run.repository_url}
                      </span>

                      <div className="history-links">
                        <Link
                          to={`/runs/${encodeURIComponent(
                            run.run_id
                          )}`}
                          className="repository-link"
                          onClick={
                            (event) =>
                              event.stopPropagation()
                          }
                        >
                          View Details
                        </Link>

                        <Link
                          to={`/repositories/${encodeURIComponent(
                            getRepositoryName(
                              run.repository_url
                            )
                          )}`}
                          className="repository-link"
                          onClick={
                            (event) =>
                              event.stopPropagation()
                          }
                        >
                          Open Workspace
                        </Link>
                      </div>
                    </div>

                    <div className="history-actions">
                      <span>
                        {run.score
                          ?.final_score ?? 0}{" "}
                        pts
                      </span>

                      <button
                        type="button"
                        className={`pin-button ${
                          pinned
                            ? "pin-button-active"
                            : ""
                        }`}
                        onClick={
                          (event) => {
                            event.stopPropagation();

                            handleTogglePin(
                              run.repository_url
                            );
                          }
                        }
                      >
                        {pinned
                          ? "★"
                          : "☆"}
                      </button>
                    </div>
                  </article>
                );
              }
            )
          ) : (
            <p className="empty-state">
              No runs found.
            </p>
          )}
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <button
              type="button"
              disabled={
                currentPage === 1
              }
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.max(
                      1,
                      page - 1
                    )
                )
              }
            >
              Previous
            </button>

            <span>
              Page {currentPage} of{" "}
              {totalPages}
            </span>

            <button
              type="button"
              disabled={
                currentPage ===
                totalPages
              }
              onClick={() =>
                setCurrentPage(
                  (page) =>
                    Math.min(
                      totalPages,
                      page + 1
                    )
                )
              }
            >
              Next
            </button>
          </div>
        )}
      </section>
    </main>
  );
}

export default DashboardPage;