import React from "react";
import type { CaptureStats } from "../hooks/useCapture";

interface StatsBarProps {
  stats: CaptureStats;
  callsTotal: number;
  estimatedSpendUsd: number;
  maxCallsPerSession?: number;
  warningsCount?: number;
  stopsCount?: number;
  highRiskGuardedCount?: number;
}

export const StatsBar: React.FC<StatsBarProps> = ({
  stats,
  callsTotal,
  estimatedSpendUsd,
  maxCallsPerSession = 300,
  warningsCount = 0,
  stopsCount = 0,
  highRiskGuardedCount = 0,
}) => {
  const lastLatency = stats.latencies.length > 0 ? stats.latencies[stats.latencies.length - 1] : 0;
  const callsLeft = Math.max(0, maxCallsPerSession - callsTotal);

  const medianLatency = () => {
    if (stats.latencies.length === 0) return 0;
    const sorted = [...stats.latencies].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  };

  return (
    <div className="card stats-bar">
      <div className="stat-item">
        <span className="stat-label">Frames Seen</span>
        <span className="stat-val">{stats.framesSeen}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Frames Sent</span>
        <span className="stat-val accent-sent">{stats.framesSent}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Frames Skipped</span>
        <span className="stat-val">{stats.framesSkipped}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Calls Used</span>
        <span className="stat-val">{callsTotal}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Calls Left</span>
        <span className="stat-val accent-sent">{callsLeft}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Warnings</span>
        <span className="stat-val stat-warning">{warningsCount}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Stops</span>
        <span className="stat-val stat-stop">{stopsCount}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">High-Risk Guarded</span>
        <span className="stat-val stat-guarded">{highRiskGuardedCount}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Est. Spend</span>
        <span className="stat-val accent-spend">${estimatedSpendUsd.toFixed(4)}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Last Latency</span>
        <span className="stat-val">{lastLatency > 0 ? `${lastLatency.toFixed(0)}ms` : "—"}</span>
      </div>

      <div className="stat-item">
        <span className="stat-label">Median Latency</span>
        <span className="stat-val">{stats.latencies.length > 0 ? `${medianLatency().toFixed(0)}ms` : "—"}</span>
      </div>
    </div>
  );
};
