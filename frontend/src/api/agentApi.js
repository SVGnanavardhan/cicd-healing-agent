const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function triggerRun({ repo_url, team_name, leader_name }) {
  const res = await fetch(`${BASE}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url, team_name, leader_name }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function pollRun(runId) {
  const res = await fetch(`${BASE}/api/run/${runId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getResults(runId) {
  const res = await fetch(`${BASE}/api/run/${runId}/results`);
  if (res.status === 202) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function healthCheck() {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch { return false; }
}
