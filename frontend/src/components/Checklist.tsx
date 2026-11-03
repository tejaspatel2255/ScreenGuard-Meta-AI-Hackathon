import React from "react";
import type { ProcedureStep, StepState } from "../types";

interface ChecklistProps {
  steps: ProcedureStep[];
  states: Record<string, StepState>;
  currentStepId: string | null;
  onOverride: (stepId: string, state: StepState) => void;
}

export const Checklist: React.FC<ChecklistProps> = ({
  steps,
  states,
  currentStepId,
  onOverride,
}) => {
  const getStatusIcon = (st: StepState) => {
    switch (st) {
      case "done":
        return "✓";
      case "active":
        return "▶";
      case "wrong":
        return "✕";
      case "skipped":
        return "⏭";
      case "uncertain":
        return "?";
      default:
        return "○";
    }
  };

  return (
    <div className="card checklist-panel">
      <h2>Live Procedure Checklist</h2>
      <div className="steps-container">
        {steps.map((step) => {
          const state = states[step.id] || "pending";
          const isCurrent = step.id === currentStepId;

          return (
            <div
              key={step.id}
              className={`step-row state-${state} ${isCurrent ? "current" : ""}`}
            >
              <div className="step-left">
                <span className={`status-chip chip-${state}`}>
                  <span className="chip-icon">{getStatusIcon(state)}</span>
                  <span className="chip-text">{state.toUpperCase()}</span>
                </span>
                <span className="step-order">#{step.order}</span>
              </div>

              <div className="step-body">
                <div className="step-instruction">
                  {step.instruction}
                  {step.risk === "high" && (
                    <span className="risk-badge" title="High-risk action requiring extra verification">
                      HIGH RISK
                    </span>
                  )}
                </div>
                <div className="step-condition">
                  Condition: <em>{step.success_condition}</em>
                </div>
              </div>

              <div className="step-actions">
                {state !== "done" && (
                  <button
                    className="btn-mini btn-mini-done"
                    title="Manually mark done"
                    onClick={() => onOverride(step.id, "done")}
                  >
                    Done
                  </button>
                )}
                {state !== "skipped" && state !== "done" && (
                  <button
                    className="btn-mini btn-mini-skip"
                    title="Manually skip step"
                    onClick={() => onOverride(step.id, "skipped")}
                  >
                    Skip
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
