import React, { useState } from "react";
import type { ProcedureParseResult } from "../types";
import { parseProcedure } from "../api";

interface ProcedurePanelProps {
  procedure: ProcedureParseResult | null;
  onProcedureParsed: (proc: ProcedureParseResult) => void;
  onStartSession: () => void;
  isSessionActive: boolean;
  isLoading: boolean;
}

export const ProcedurePanel: React.FC<ProcedurePanelProps> = ({
  procedure,
  onProcedureParsed,
  onStartSession,
  isSessionActive,
  isLoading,
}) => {
  const [text, setText] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDemoProcedure = async () => {
    try {
      setError(null);
      const res = await fetch("/demo-procedure.txt");
      if (!res.ok) throw new Error("Could not load /demo-procedure.txt");
      const content = await res.text();
      setText(content);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleParse = async () => {
    if (!text.trim()) {
      setError("Please paste or load a procedure first.");
      return;
    }
    try {
      setIsParsing(true);
      setError(null);
      const result = await parseProcedure(text);
      onProcedureParsed(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="card procedure-panel">
      <div className="card-header">
        <div className="card-title-group">
          <h2>Standard Operating Procedure</h2>
        </div>
        <button
          className="btn-secondary-sm"
          onClick={() => window.open("http://localhost:5500", "_blank")}
          title="Opens Acme Admin Target App in a new tab"
        >
          Open Demo App (Acme Admin) ↗
        </button>
      </div>

      <div className="form-group">
        <textarea
          className="procedure-textarea"
          rows={5}
          placeholder="Paste numbered procedure steps here (or click Load Demo Procedure)..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isSessionActive}
        />
      </div>

      {error && <div className="panel-error">{error}</div>}

      <div className="panel-actions">
        <button
          className="btn-secondary-sm"
          onClick={loadDemoProcedure}
          disabled={isSessionActive || isParsing}
        >
          Load Demo Procedure
        </button>

        <button
          className="btn-primary-sm"
          onClick={handleParse}
          disabled={isSessionActive || isParsing || !text.trim()}
        >
          {isParsing ? "Parsing..." : "Parse Steps"}
        </button>

        {procedure && !isSessionActive && (
          <button
            className="btn-accent-sm"
            onClick={onStartSession}
            disabled={isLoading || isParsing}
          >
            Start Session
          </button>
        )}
      </div>

      {procedure && (
        <div className="parsed-summary">
          <strong>{procedure.title}</strong> ({procedure.steps.length} steps)
          <span className="source-tag">Source: {procedure.source}</span>
        </div>
      )}
    </div>
  );
};
