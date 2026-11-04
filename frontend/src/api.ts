import type {
  BudgetInfo,
  HealthInfo,
  ProcedureParseResult,
  SessionDetail,
  StepState,
  StepUpdate,
  TraceEntry,
} from "./types";

const API_BASE = "";

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function parseProcedure(text: string): Promise<ProcedureParseResult> {
  const res = await fetch(`${API_BASE}/api/procedure/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Parse failed: ${await res.text()}`);
  return res.json();
}

export async function startSession(procedure: ProcedureParseResult): Promise<{
  session_id: string;
  steps: ProcedureParseResult["steps"];
  states: Record<string, StepState>;
  current_step_id: string | null;
}> {
  const res = await fetch(`${API_BASE}/api/session/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ procedure }),
  });
  if (!res.ok) throw new Error(`Start session failed: ${await res.text()}`);
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}`);
  if (!res.ok) throw new Error(`Get session failed: ${await res.text()}`);
  return res.json();
}

export async function overrideStep(
  sessionId: string,
  stepId: string,
  state: StepState
): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_id: stepId, state }),
  });
  if (!res.ok) throw new Error(`Override failed: ${await res.text()}`);
  return res.json();
}

export async function restartSession(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/restart`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Restart failed: ${await res.text()}`);
  return res.json();
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function sendFrame(sessionId: string, jpegBlob: Blob): Promise<StepUpdate> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/frame`, {
    method: "POST",
    headers: { "Content-Type": "image/jpeg" },
    body: jpegBlob,
  });
  if (!res.ok) {
    const errorText = await res.text();
    if (res.status === 413) {
      throw new ApiError(413, "Frame Payload Too Large (HTTP 413): Screenshot exceeds 1.5 MB limit. Please check screen downscaling.");
    }
    if (res.status === 415) {
      throw new ApiError(415, "Unsupported Media Type (HTTP 415): Frame must be a valid JPEG or PNG image.");
    }
    if (res.status === 429) {
      throw new ApiError(429, `Rate or Budget Limit Reached (HTTP 429): ${errorText || "Maximum session calls or spend limit reached."}`);
    }
    throw new ApiError(res.status, `Frame processing error (${res.status}): ${errorText}`);
  }
  return res.json();
}

export async function fetchTrace(sessionId: string): Promise<TraceEntry[]> {
  const res = await fetch(`${API_BASE}/api/session/${sessionId}/trace`);
  if (!res.ok) throw new Error(`Trace failed: ${await res.text()}`);
  return res.json();
}

export async function fetchBudget(): Promise<BudgetInfo> {
  const res = await fetch(`${API_BASE}/api/budget`);
  if (!res.ok) throw new Error(`Budget failed: ${await res.text()}`);
  return res.json();
}

export async function fetchReplay(kind: "correct" | "mistake"): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/replay/${kind}`);
  if (!res.ok) throw new Error(`Replay failed: ${await res.text()}`);
  return res.json();
}
