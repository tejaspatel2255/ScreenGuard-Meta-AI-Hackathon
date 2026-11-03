import React from "react";

interface CapturePanelProps {
  isSharing: boolean;
  onStartShare: () => void;
  onStopShare: () => void;
  onCheckNow: () => void;
  isSessionActive: boolean;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  onRestartSession: () => void;
}

export const CapturePanel: React.FC<CapturePanelProps> = ({
  isSharing,
  onStartShare,
  onStopShare,
  onCheckNow,
  isSessionActive,
  voiceEnabled,
  onToggleVoice,
  onRestartSession,
}) => {
  return (
    <div className="card capture-panel">
      <div className="privacy-callout">
        <span className="privacy-badge">Privacy Safeguard</span>
        <p>
          Only the chosen browser tab is captured. Screen frames stay strictly in memory and are
          never stored on disk.
        </p>
      </div>

      <div className="capture-controls">
        {!isSharing ? (
          <button
            className="btn-capture-start"
            onClick={onStartShare}
            disabled={!isSessionActive}
          >
            Share Tab & Begin Supervision
          </button>
        ) : (
          <div className="sharing-active-group">
            <button className="btn-capture-stop" onClick={onStopShare}>
              Stop Sharing
            </button>
            <button className="btn-check-now" onClick={onCheckNow}>
              Check Now (Instant Frame)
            </button>
          </div>
        )}

        <div className="secondary-toggles">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={voiceEnabled}
              onChange={onToggleVoice}
            />
            Spoken Audio Warnings
          </label>

          {isSessionActive && (
            <button className="btn-restart-sm" onClick={onRestartSession}>
              Restart Session
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
