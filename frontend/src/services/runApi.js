import {
  supabase,
} from "./supabaseClient";


export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


export const TERMINAL_STATUSES =
  new Set([
    "TESTS_PASSED",
    "STATIC_VERIFICATION_PASSED",
    "FIX_VERIFIED",
    "NO_ACTIONABLE_FIXES",
    "NO_TESTS_FOUND",
    "ENVIRONMENT_SETUP_FAILED",
    "RETRY_LIMIT_REACHED",
    "FAILED",
    "CANCELLED",
  ]);


async function getAccessToken() {
  const {
    data: {
      session,
    },
    error,
  } =
    await supabase.auth.getSession();

  if (error) {
    throw new Error(
      error.message
    );
  }

  if (!session?.access_token) {
    throw new Error(
      "Your session expired. Please login again."
    );
  }

  return session.access_token;
}


async function authenticatedFetch(
  path,
  options = {}
) {
  const accessToken =
    await getAccessToken();

  const hasBody =
    options.body !== undefined;

  try {
    return await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...options,

        headers: {
          Accept:
            "application/json",

          Authorization:
            `Bearer ${accessToken}`,

          ...(hasBody
            ? {
                "Content-Type":
                  "application/json",
              }
            : {}),

          ...(options.headers || {}),
        },
      }
    );
  } catch {
    throw new Error(
      `Unable to reach backend at ${API_BASE_URL}. Make sure FastAPI is running.`
    );
  }
}


async function parseError(
  response,
  fallbackMessage
) {
  const errorData =
    await response
      .json()
      .catch(
        () => null
      );

  const detail =
    errorData?.detail;

  if (
    typeof detail ===
    "string"
  ) {
    return new Error(
      detail
    );
  }

  if (
    Array.isArray(detail)
  ) {
    const message =
      detail
        .map(
          (item) =>
            item?.msg
        )
        .filter(Boolean)
        .join(", ");

    return new Error(
      message ||
        fallbackMessage
    );
  }

  if (
    detail &&
    typeof detail ===
      "object"
  ) {
    return new Error(
      detail.message ||
        fallbackMessage
    );
  }

  return new Error(
    fallbackMessage
  );
}


export async function verifyGitHubToken(
  githubToken
) {
  const token =
    githubToken?.trim();

  if (!token) {
    throw new Error(
      "Enter a GitHub token first"
    );
  }

  const response =
    await authenticatedFetch(
      "/api/github/verify",
      {
        method: "POST",

        body:
          JSON.stringify({
            github_token:
              token,
          }),
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "GitHub token verification failed"
    );
  }

  return response.json();
}


export async function verifyRepositoryAccess(
  repositoryUrl,
  githubToken
) {
  const repository =
    repositoryUrl?.trim();

  const token =
    githubToken?.trim();

  if (!repository) {
    throw new Error(
      "Repository URL is required"
    );
  }

  if (!token) {
    throw new Error(
      "GitHub token is required"
    );
  }

  const response =
    await authenticatedFetch(
      "/api/github/repository-access",
      {
        method: "POST",

        body:
          JSON.stringify({
            repository_url:
              repository,

            github_token:
              token,
          }),
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Repository access verification failed"
    );
  }

  return response.json();
}


export async function createRun(
  payload
) {
  const response =
    await authenticatedFetch(
      "/api/runs/start",
      {
        method: "POST",

        body:
          JSON.stringify(
            payload
          ),
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to start run"
    );
  }

  return response.json();
}


export async function getRuns({
  page = 1,
  pageSize = 10,
  statusFilter = "ALL",
  searchQuery = "",
} = {}) {
  const params =
    new URLSearchParams({
      page:
        String(page),

      page_size:
        String(pageSize),
    });

  if (
    statusFilter &&
    statusFilter !== "ALL"
  ) {
    params.set(
      "status_filter",
      statusFilter
    );
  }

  if (
    searchQuery?.trim()
  ) {
    params.set(
      "search_query",
      searchQuery.trim()
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs?${params.toString()}`
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to fetch run history"
    );
  }

  return response.json();
}


export async function getRun(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}`
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to fetch run"
    );
  }

  return response.json();
}


export async function getRunStatus(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}/status`
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to fetch run status"
    );
  }

  return response.json();
}


export async function cancelRun(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}/cancel`,
      {
        method: "POST",
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to cancel run"
    );
  }

  return response.json();
}


export async function retryRun(
  runId,
  githubToken = null
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}/retry`,
      {
        method: "POST",

        body:
          JSON.stringify({
            github_token:
              githubToken
                ?.trim() ||
              null,
          }),
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to retry run"
    );
  }

  return response.json();
}


export async function deleteRun(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}`,
      {
        method: "DELETE",
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to delete run"
    );
  }

  return response.json();
}


export async function getAnalytics() {
  const response =
    await authenticatedFetch(
      "/api/analytics"
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to fetch analytics"
    );
  }

  return response.json();
}


export async function getActivity(
  limit = 50
) {
  const params =
    new URLSearchParams({
      limit:
        String(limit),
    });

  const response =
    await authenticatedFetch(
      `/api/activity?${params.toString()}`
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to fetch activity"
    );
  }

  return response.json();
}


export async function downloadResults(
  runId
) {
  if (!runId) {
    throw new Error(
      "Run ID is required"
    );
  }

  const response =
    await authenticatedFetch(
      `/api/runs/${encodeURIComponent(
        runId
      )}/results/download`,
      {
        headers: {
          Accept:
            "application/pdf",
        },
      }
    );

  if (!response.ok) {
    throw await parseError(
      response,
      "Failed to download PDF report"
    );
  }

  const blob =
    await response.blob();

  const contentType =
    response.headers.get(
      "content-type"
    ) || "";

  if (
    !contentType.includes(
      "application/pdf"
    )
  ) {
    throw new Error(
      "Backend did not return a PDF report"
    );
  }

  const downloadUrl =
    URL.createObjectURL(
      blob
    );

  const anchor =
    document.createElement(
      "a"
    );

  anchor.href =
    downloadUrl;

  anchor.download =
    `${runId}-results.pdf`;

  document.body.appendChild(
    anchor
  );

  anchor.click();

  anchor.remove();

  URL.revokeObjectURL(
    downloadUrl
  );
}


function wait(
  milliseconds,
  signal
) {
  return new Promise(
    (
      resolve,
      reject
    ) => {
      const timeoutId =
        setTimeout(
          resolve,
          milliseconds
        );

      if (!signal) {
        return;
      }

      signal.addEventListener(
        "abort",
        () => {
          clearTimeout(
            timeoutId
          );

          reject(
            new DOMException(
              "Run polling cancelled",
              "AbortError"
            )
          );
        },
        {
          once: true,
        }
      );
    }
  );
}


export async function waitForRunCompletion(
  runId,
  onUpdate,
  intervalMs = 3000,
  options = {}
) {
  const {
    signal,
    timeoutMs =
      30 * 60 * 1000,
  } = options;

  const startedAt =
    Date.now();

  while (true) {
    if (
      signal?.aborted
    ) {
      throw new DOMException(
        "Run polling cancelled",
        "AbortError"
      );
    }

    if (
      Date.now() -
        startedAt >
      timeoutMs
    ) {
      throw new Error(
        "Run polling timed out. Check run history for the latest status."
      );
    }

    const run =
      await getRun(
        runId
      );

    if (
      typeof onUpdate ===
      "function"
    ) {
      onUpdate(
        run
      );
    }

    if (
      TERMINAL_STATUSES.has(
        run.status
      )
    ) {
      return run;
    }

    await wait(
      intervalMs,
      signal
    );
  }
}