import React from "react";
import type { TraceEntry, ProcedureParseResult, StepState, HealthInfo } from "../types";

interface DecisionTraceProps {
  trace: TraceEntry[];
  procedure?: ProcedureParseResult | null;
  states?: Record<string, StepState>;
  health?: HealthInfo | null;
  estimatedSpendUsd?: number;
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({
  trace,
  procedure,
  states = {},
  health,
  estimatedSpendUsd = 0,
}) => {
  const downloadSessionJson = () => {
    const data = {
      timestamp: new Date().toISOString(),
      model_info: health?.model_info || { provider: "groq", vision_model: "qwen/qwen3.8-27b" },
      mode: health?.mode || "mock",
      spend_usd: estimatedSpendUsd,
      procedure: procedure?.title || "Unknown Procedure",
      steps: procedure?.steps || [],
      final_states: states,
      decision_trace: trace,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screenguard-session-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadSessionMarkdown = () => {
    const lines = [
      `# ScreenGuard Session Report`,
      ``,
      `- **Generated**: ${new Date().toLocaleString()}`,
      `- **Procedure**: ${procedure?.title || "Unknown Procedure"}`,
      `- **Mode**: ${health?.mode || "unknown"}`,
      `- **Model**: ${health?.model_info?.vision_model || "unknown"} (Provider: ${health?.model_info?.provider || "unknown"})`,
      `- **Estimated Spend**: $${estimatedSpendUsd.toFixed(4)} USD`,
      ``,
      `## Final Step States`,
      ``,
      `| Step | Instruction | Final State |`,
      `|---|---|---|`,
      ...(procedure?.steps || []).map(
        (s) => `| ${s.order} | ${s.instruction} | **${states[s.id] || "pending"}** |`
      ),
      ``,
      `## Supervisor Decision Trace`,
      ``,
      `| Time | Action | Step ID | Confidence | Reason / Warning |`,
      `|---|---|---|---|---|`,
      ...trace.map(
        (t) =>
          `| ${new Date(t.ts * 1000).toLocaleTimeString()} | **${t.action}** | ${t.step_id} | ${(t.confidence * 100).toFixed(0)}% | ${t.warning ? `⚠️ ${t.warning}` : t.reason} |`
      ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screenguard-session-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card trace-panel">
      <div className="trace-header-row">
        <h2>Supervisor Decision Trace</h2>
        <div className="trace-export-buttons">
          <button className="btn-export" onClick={downloadSessionJson} title="Download session as JSON">
            📥 JSON
          </button>
          <button className="btn-export" onClick={downloadSessionMarkdown} title="Download session as Markdown">
            📄 Markdown
          </button>
        </div>
      </div>
      <div className="trace-scroll-area">
        {trace.length === 0 ? (
          <p className="empty-trace">No actions recorded yet. Share a tab to begin supervision.</p>
        ) : (
          trace.map((item) => (
            <div key={item.id} className={`trace-item action-${item.action.toLowerCase()}`}>
              <div className="trace-item-header">
                <span className={`trace-action-badge badge-${item.action.toLowerCase()}`}>
                  {item.action}
                </span>
                <span className="trace-step-tag">Step: {item.step_id}</span>
                <span className="trace-conf-tag">Conf: {(item.confidence * 100).toFixed(0)}%</span>
                <span className="trace-time">
                  {new Date(item.ts * 1000).toLocaleTimeString()}
                </span>
              </div>
              <div className="trace-reason">{item.reason}</div>
              {item.warning && <div className="trace-warning-text">⚠️ {item.warning}</div>}
              {item.evidence && (
                <div className="trace-evidence">
                  <small>Evidence: {item.evidence}</small>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
