import React, { useState, useEffect } from "react";
import { fetchHealth, fetchBudget } from "../api";
import type { HealthInfo } from "../types";

interface PreflightCheck {
  id: string;
  name: string;
  status: "pending" | "pass" | "fail";
  details: string;
  fix: string;
}

export const PreflightPanel: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [checks, setChecks] = useState<PreflightCheck[]>([
    {
      id: "backend",
      name: "Backend Health & Model",
      status: "pending",
      details: "Checking /api/health...",
      fix: "Start backend server: uvicorn backend.app.main:app --port 8000",
    },
    {
      id: "demo_target",
      name: "Demo App Reachability",
      status: "pending",
      details: "Checking http://localhost:5500...",
      fix: "Start target app: python -m http.server 5500 --directory demo_target",
    },
    {
      id: "budget",
      name: "API Budget Remaining",
      status: "pending",
      details: "Checking /api/budget...",
      fix: "Increase MAX_ESTIMATED_SPEND_USD in .env or restart session",
    },
    {
      id: "screen",
      name: "Display Capture Support",
      status: "pending",
      details: "Testing getDisplayMedia...",
      fix: "Use a modern browser (Chrome/Edge) with screen sharing permission",
    },
  ]);

  const runChecks = async () => {
    // 1. Backend Health
    try {
      const h: HealthInfo = await fetchHealth();
      const model = h.model_info?.vision_model || "unknown";
      const prov = h.model_info?.provider || "unknown";
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "backend"
            ? {
                ...c,
                status: h.status === "ok" ? "pass" : "fail",
                details: `Status: ${h.status}, Mode: ${h.mode}, Provider: ${prov}, Model: ${model}`,
              }
            : c
        )
      );
    } catch (e: unknown) {
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "backend"
            ? {
                ...c,
                status: "fail",
                details: `Error: ${e instanceof Error ? e.message : String(e)}`,
              }
            : c
        )
      );
    }

    // 2. Demo Target (Checks localhost if running locally, or the bundled app on Vercel)
    try {
      const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      const targetUrl = isLocal ? "http://localhost:5500" : "/demo_target/index.html";
      await fetch(targetUrl, { mode: "no-cors" });
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "demo_target"
            ? {
                ...c,
                status: "pass",
                details: isLocal
                  ? "Demo app responsive on port 5500"
                  : "Bundled demo app accessible on Vercel (/demo_target/index.html)",
              }
            : c
        )
      );
    } catch {
      const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "demo_target"
            ? {
                ...c,
                status: "fail",
                details: isLocal
                  ? "Could not connect to http://localhost:5500"
                  : "Could not load /demo_target/index.html",
                fix: isLocal
                  ? "Start target app: python -m http.server 5500 --directory demo_target"
                  : "Verify /demo_target/index.html exists in public directory",
              }
            : c
        )
      );
    }

    // 3. Budget
    try {
      const b = await fetchBudget();
      const left = Math.max(0, 100 - b.estimated_spend_usd);
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "budget"
            ? {
                ...c,
                status: left > 1.0 ? "pass" : "fail",
                details: `Spent: $${b.estimated_spend_usd.toFixed(4)}, Remaining: ~$${left.toFixed(2)}`,
              }
            : c
        )
      );
    } catch (e: unknown) {
      setChecks((prev) =>
        prev.map((c) =>
          c.id === "budget"
            ? {
                ...c,
                status: "fail",
                details: `Error: ${e instanceof Error ? e.message : String(e)}`,
              }
            : c
        )
      );
    }

    // 4. Screen Capture Support
    const hasMedia =
      typeof navigator !== "undefined" &&
      !!navigator.mediaDevices &&
      typeof navigator.mediaDevices.getDisplayMedia === "function";

    setChecks((prev) =>
      prev.map((c) =>
        c.id === "screen"
          ? {
              ...c,
              status: hasMedia ? "pass" : "fail",
              details: hasMedia ? "getDisplayMedia API available in browser" : "Screen sharing API not supported",
            }
          : c
      )
    );
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      runChecks();
    }, 0);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="eval-modal-backdrop">
      <div className="eval-modal-content card preflight-card">
        <div className="eval-modal-header">
          <div className="eval-title-group">
            <h2>Preflight Checklist for Demo Recording</h2>
            <span className="eval-subtitle">Ensure environment readiness before video recording</span>
          </div>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="preflight-body">
          <div className="preflight-list">
            {checks.map((check) => (
              <div key={check.id} className={`preflight-item preflight-${check.status}`}>
                <div className="preflight-indicator">
                  {check.status === "pass" && "✓"}
                  {check.status === "fail" && "✗"}
                  {check.status === "pending" && "⋯"}
                </div>
                <div className="preflight-content">
                  <div className="preflight-title">
                    <strong>{check.name}</strong>
                    <span className={`preflight-badge badge-${check.status}`}>{check.status.toUpperCase()}</span>
                  </div>
                  <div className="preflight-desc">{check.details}</div>
                  {check.status === "fail" && (
                    <div className="preflight-fix">
                      <span>Fix:</span> <code>{check.fix}</code>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="preflight-actions">
            <button className="btn-primary" onClick={runChecks}>Re-run Checks</button>
            <button className="btn-secondary" onClick={onClose}>Close Preflight</button>
          </div>
        </div>
      </div>
    </div>
  );
};
