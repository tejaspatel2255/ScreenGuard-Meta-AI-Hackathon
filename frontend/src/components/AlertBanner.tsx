import React from "react";
import type { ActionType } from "../types";

interface AlertBannerProps {
  action: ActionType | null;
  warningText: string | null;
  reasonText: string | null;
  currentStepId: string | null;
  onDismiss: () => void;
  onConfirmDone: () => void;
  onNotDone: () => void;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  action,
  warningText,
  reasonText,
  onDismiss,
  onConfirmDone,
  onNotDone,
}) => {
  if (!action || action === "ADVANCE" || action === "WAIT") {
    return null;
  }

  if (action === "STOP") {
    return (
      <div className="alert-banner alert-stop">
        <div className="alert-content">
          <div className="alert-title">SUPERVISOR STOP (BLOCKING)</div>
          <div className="alert-message">{warningText || reasonText}</div>
        </div>
        <button className="alert-btn" onClick={onDismiss}>
          Acknowledge
        </button>
      </div>
    );
  }

  if (action === "WARN") {
    return (
      <div className="alert-banner alert-warn">
        <div className="alert-content">
          <div className="alert-title">PROCEDURE WARNING</div>
          <div className="alert-message">{warningText || reasonText}</div>
        </div>
        <button className="alert-dismiss" onClick={onDismiss}>
          ✕
        </button>
      </div>
    );
  }

  if (action === "ASK_USER") {
    return (
      <div className="alert-banner alert-ask">
        <div className="alert-content">
          <div className="alert-title">USER CONFIRMATION REQUIRED</div>
          <div className="alert-message">
            {warningText || reasonText || "Evidence is ambiguous on high-risk step. Did you complete this step?"}
          </div>
        </div>
        <div className="alert-actions">
          <button className="btn-confirm-yes" onClick={onConfirmDone}>
            Confirm Done
          </button>
          <button className="btn-confirm-no" onClick={onNotDone}>
            Not Done
          </button>
        </div>
      </div>
    );
  }

  return null;
};
