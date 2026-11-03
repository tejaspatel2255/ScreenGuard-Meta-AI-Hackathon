export type StepState = "pending" | "active" | "done" | "wrong" | "skipped" | "uncertain";

export type RiskLevel = "low" | "high";

export interface ProcedureStep {
  id: string;
  order: number;
  instruction: string;
  expected_elements: string[];
  success_condition: string;
  forbidden_actions: string[];
  depends_on: string[];
  risk: RiskLevel;
}

export interface ProcedureParseResult {
  title: string;
  steps: ProcedureStep[];
  source: "real" | "mock";
  confidence: number;
}

export interface BoundingBox {
  label: string;
  box_2d: [number, number, number, number]; // [ymin, xmin, ymax, xmax] normalized 0..1
  confidence: number;
}

export interface VerdictResult {
  step_id: string;
  status: "done" | "in_progress" | "wrong" | "uncertain";
  observed_step_ids: string[];
  evidence: string;
  warning_text?: string | null;
  confidence: number;
  source: "real" | "mock";
}

export type ActionType = "ADVANCE" | "WAIT" | "WARN" | "RECHECK" | "ASK_USER" | "STOP";

export interface EngineEvent {
  ts: number;
  step_id: string;
  kind: string;
  reason: string;
}

export interface StepUpdate {
  session_id: string;
  frame_id: string;
  states: Record<string, StepState>;
  current_step_id: string | null;
  action: ActionType;
  reason: string;
  warning?: string | null;
  blocking: boolean;
  boxes: BoundingBox[];
  verdict?: VerdictResult | null;
  calls_used: number;
  estimated_spend_usd: number;
  latency_ms: number;
  cached: boolean;
  events: EngineEvent[];
}

export interface TraceEntry {
  id: string;
  ts: number;
  action: ActionType;
  reason: string;
  step_id: string;
  status: string;
  confidence: number;
  evidence: string;
  warning?: string | null;
  calls_used: number;
  latency_ms: number;
}

export interface SessionDetail {
  session_id: string;
  states: Record<string, StepState>;
  current_step_id: string | null;
  progress: { done: number; total: number };
  is_complete: boolean;
  events: EngineEvent[];
}

export interface BudgetInfo {
  calls_total: number;
  calls_this_minute: number;
  estimated_spend_usd: number;
  spend_limit_usd: number;
}

export interface HealthInfo {
  status: string;
  mode: string;
}
