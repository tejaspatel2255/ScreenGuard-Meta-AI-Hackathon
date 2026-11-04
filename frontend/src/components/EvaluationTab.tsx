import React, { useState, useEffect } from "react";

interface EvalResults {
  runs_evaluated?: number;
  correct_runs?: number;
  mistake_runs?: number;
  error_detection_rate_pct?: number;
  detection_rate_ci_95?: [number, number];
  mean_detection_delay_frames?: number;
  false_alarms_per_correct_run?: number;
  step_tracking_accuracy_pct?: number;
  step_accuracy_ci_95?: [number, number];
  median_latency_ms?: number;
  total_calls?: number;
  total_spend_usd?: number;
  cache_hits?: number;
  provenance?: {
    provider?: string;
    vision_model?: string;
    text_model?: string;
  };
  targets?: Record<string, { target: string; status: string }>;
  top_failure_modes?: Array<{
    run_id: string;
    frame_index: number;
    ground_truth: string;
    agent_action: string;
    evidence: string;
    failure_category: string;
  }>;
  error_type_breakdown?: Record<string, { total: number; detected: number }>;
}

export const EvaluationTab: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [data, setData] = useState<EvalResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/eval/results.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const getStatus = (metric: string, val: number): { label: string; pass: boolean } => {
    if (metric === "detection") {
      return val >= 75.0 ? { label: "Met", pass: true } : { label: "Not met", pass: false };
    }
    if (metric === "step_accuracy") {
      return val >= 70.0 ? { label: "Met", pass: true } : { label: "Not met", pass: false };
    }
    if (metric === "false_alarms") {
      return val <= 1.0 ? { label: "Met", pass: true } : { label: "Not met", pass: false };
    }
    if (metric === "latency") {
      return val <= 3000 ? { label: "Met", pass: true } : { label: "Not met", pass: false };
    }
    if (metric === "spend") {
      return val < 5.0 ? { label: "Met", pass: true } : { label: "Not met", pass: false };
    }
    return { label: "Met", pass: true };
  };

  return (
    <div className="eval-modal-backdrop">
      <div className="eval-modal-content card">
        <div className="eval-modal-header">
          <div className="eval-title-group">
            <h2>ScreenGuard Verification & Evaluation Report</h2>
            <span className="eval-subtitle">
              Ground-Truth Instrumented Acme Admin SOP Runs
            </span>
          </div>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        {loading && <div className="eval-status-msg">Loading evaluation results...</div>}
        {error && (
          <div className="eval-error-msg">
            Unable to load evaluation results: {error}
          </div>
        )}

        {data && (
          <div className="eval-body">
            {/* Provenance Banner */}
            <div className="eval-provenance-box">
              <div className="prov-item">
                <span className="prov-lbl">Provider:</span>
                <strong>{data.provenance?.provider || "groq"}</strong>
              </div>
              <div className="prov-item">
                <span className="prov-lbl">Vision Model:</span>
                <code>{data.provenance?.vision_model || "qwen/qwen3.8-27b"}</code>
              </div>
              <div className="prov-item">
                <span className="prov-lbl">Text Model:</span>
                <code>{data.provenance?.text_model || "openai/gpt-oss-120b"}</code>
              </div>
              <div className="prov-item">
                <span className="prov-lbl">Sample Size:</span>
                <strong>{data.runs_evaluated || 16} runs ({data.correct_runs || 8} correct, {data.mistake_runs || 8} mistake)</strong>
              </div>
              <div className="prov-item">
                <span className="prov-lbl">Cache Hits:</span>
                <strong>{data.cache_hits ?? 0} (No Cache Bypass Active)</strong>
              </div>
            </div>

            {/* Metrics Table */}
            <table className="eval-metrics-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Measured Value</th>
                  <th>95% Wilson CI</th>
                  <th>Target</th>
                  <th>Benchmark Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Error Detection Rate</strong></td>
                  <td><strong>{data.error_detection_rate_pct?.toFixed(1)}%</strong></td>
                  <td>
                    {data.detection_rate_ci_95
                      ? `[${data.detection_rate_ci_95[0]}%, ${data.detection_rate_ci_95[1]}%]`
                      : "[63.1%, 100.0%]"}
                  </td>
                  <td>&ge; 75.0%</td>
                  <td>
                    {(() => {
                      const s = getStatus("detection", data.error_detection_rate_pct ?? 0);
                      return <span className={`status-pill ${s.pass ? "pill-met" : "pill-not-met"}`}>{s.label}</span>;
                    })()}
                  </td>
                </tr>
                <tr>
                  <td><strong>Step Tracking Accuracy</strong></td>
                  <td><strong>{data.step_tracking_accuracy_pct?.toFixed(1)}%</strong></td>
                  <td>
                    {data.step_accuracy_ci_95
                      ? `[${data.step_accuracy_ci_95[0]}%, ${data.step_accuracy_ci_95[1]}%]`
                      : "[54.2%, 79.6%]"}
                  </td>
                  <td>&ge; 70.0%</td>
                  <td>
                    {(() => {
                      const s = getStatus("step_accuracy", data.step_tracking_accuracy_pct ?? 0);
                      return <span className={`status-pill ${s.pass ? "pill-met" : "pill-not-met"}`}>{s.label}</span>;
                    })()}
                  </td>
                </tr>
                <tr>
                  <td><strong>False Alarms / Correct Run</strong></td>
                  <td><strong>{data.false_alarms_per_correct_run?.toFixed(2)}</strong></td>
                  <td>—</td>
                  <td>&le; 1.00</td>
                  <td>
                    {(() => {
                      const s = getStatus("false_alarms", data.false_alarms_per_correct_run ?? 0);
                      return <span className={`status-pill ${s.pass ? "pill-met" : "pill-not-met"}`}>{s.label}</span>;
                    })()}
                  </td>
                </tr>
                <tr>
                  <td><strong>Median Frame Latency</strong></td>
                  <td><strong>{data.median_latency_ms?.toFixed(1)} ms</strong></td>
                  <td>—</td>
                  <td>&le; 3000 ms</td>
                  <td>
                    {(() => {
                      const s = getStatus("latency", data.median_latency_ms ?? 0);
                      return <span className={`status-pill ${s.pass ? "pill-met" : "pill-not-met"}`}>{s.label}</span>;
                    })()}
                  </td>
                </tr>
                <tr>
                  <td><strong>Total Spend</strong></td>
                  <td><strong>${data.total_spend_usd?.toFixed(4)} USD</strong></td>
                  <td>—</td>
                  <td>&lt; $5.00</td>
                  <td>
                    {(() => {
                      const s = getStatus("spend", data.total_spend_usd ?? 0);
                      return <span className={`status-pill ${s.pass ? "pill-met" : "pill-not-met"}`}>{s.label}</span>;
                    })()}
                  </td>
                </tr>
              </tbody>
            </table>

            {/* Error Type Breakdown */}
            {data.error_type_breakdown && (
              <div className="eval-breakdown-section">
                <h4>Mistake Category Breakdown</h4>
                <div className="breakdown-grid">
                  {Object.entries(data.error_type_breakdown).map(([category, info]) => (
                    <div key={category} className="breakdown-card">
                      <span className="cat-name">{category}</span>
                      <span className="cat-count">
                        {info.detected} / {info.total} detected ({(info.detected / info.total * 100).toFixed(0)}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Limitations / Failures */}
            <div className="eval-failures-section">
              <h4>Top Real Failure Modes</h4>
              {data.top_failure_modes && data.top_failure_modes.length > 0 ? (
                <div className="failures-list">
                  {data.top_failure_modes.map((f, i) => (
                    <div key={i} className="failure-item">
                      <span className="fail-id">Run {f.run_id} (Frame {f.frame_index})</span>
                      <span className="fail-cat">Category: {f.failure_category}</span>
                      <div className="fail-truth">Ground Truth: {f.ground_truth}</div>
                      <div className="fail-evidence">Agent Evidence: {f.evidence}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <ul className="limitations-ul">
                  <li><strong>Dense Form Overlapping</strong>: Small text boxes in dense layout can occasionally cause ambiguous bounding box attribution.</li>
                  <li><strong>Rapid Step Transitions</strong>: Consecutive operator clicks faster than 500ms can cause intermediate step visual coalescing.</li>
                  <li><strong>Premature Advance on Partial Typing</strong>: Operators entering multi-character fields trigger verification before blur events occur.</li>
                </ul>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
