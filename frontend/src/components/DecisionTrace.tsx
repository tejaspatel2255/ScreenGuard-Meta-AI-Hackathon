import React from "react";
import type { TraceEntry } from "../types";

interface DecisionTraceProps {
  trace: TraceEntry[];
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ trace }) => {
  return (
    <div className="card trace-panel">
      <h2>Supervisor Decision Trace</h2>
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
