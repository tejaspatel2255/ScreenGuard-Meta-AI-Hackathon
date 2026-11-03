import { useState, useEffect, useCallback, useRef } from "react";
import "./App.css";
import {
  fetchHealth,
  fetchBudget,
  startSession,
  overrideStep,
  restartSession,
  fetchTrace,
} from "./api";
import type {
  HealthInfo,
  ProcedureParseResult,
  StepState,
  StepUpdate,
  TraceEntry,
} from "./types";
import { useCapture } from "./hooks/useCapture";
import { ProcedurePanel } from "./components/ProcedurePanel";
import { CapturePanel } from "./components/CapturePanel";
import { Checklist } from "./components/Checklist";
import { AlertBanner } from "./components/AlertBanner";
import { DecisionTrace } from "./components/DecisionTrace";
import { StatsBar } from "./components/StatsBar";
import { PreviewCanvas } from "./components/PreviewCanvas";

export function App() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [procedure, setProcedure] = useState<ProcedureParseResult | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [states, setStates] = useState<Record<string, StepState>>({});
  const [currentStepId, setCurrentStepId] = useState<string | null>(null);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [latestUpdate, setLatestUpdate] = useState<StepUpdate | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [lastBlobUrl] = useState<string | null>(null);
  const [appError, setAppError] = useState<string | null>(null);
  const [budget, setBudget] = useState<{ calls: number; spend: number }>({ calls: 0, spend: 0 });

  const lastSpokenWarningRef = useRef<string | null>(null);

  // Poll health & budget
  const loadStatus = useCallback(async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
      const b = await fetchBudget();
      setBudget({ calls: b.calls_total, spend: b.estimated_spend_usd });
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 4000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  // Voice output for warnings
  const speakWarning = useCallback(
    (text: string) => {
      if (!voiceEnabled || !window.speechSynthesis) return;
      if (lastSpokenWarningRef.current === text) return;
      lastSpokenWarningRef.current = text;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    },
    [voiceEnabled]
  );

  const handleFrameUpdate = useCallback(
    (update: StepUpdate) => {
      setLatestUpdate(update);
      setBannerDismissed(false);
      setStates(update.states);
      setCurrentStepId(update.current_step_id);

      if (update.warning) {
        speakWarning(update.warning);
      }

      // Refresh trace
      if (sessionId) {
        fetchTrace(sessionId).then(setTrace).catch(console.error);
      }
    },
    [sessionId, speakWarning]
  );

  const handleCaptureError = useCallback((err: string) => {
    setAppError(err);
  }, []);

  const { isSharing, startCapture, stopCapture, checkNow, stats } = useCapture({
    sessionId,
    onUpdate: handleFrameUpdate,
    onError: handleCaptureError,
  });

  const handleStartSession = async () => {
    if (!procedure) return;
    try {
      setAppError(null);
      const res = await startSession(procedure);
      setSessionId(res.session_id);
      setStates(res.states);
      setCurrentStepId(res.current_step_id);
      setTrace([]);
      setLatestUpdate(null);
    } catch (err: unknown) {
      setAppError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleOverride = async (stepId: string, state: StepState) => {
    if (!sessionId) return;
    try {
      const res = await overrideStep(sessionId, stepId, state);
      setStates(res.states);
      setCurrentStepId(res.current_step_id);
      setBannerDismissed(true);
    } catch (err: unknown) {
      setAppError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleRestart = async () => {
    if (!sessionId) return;
    try {
      const res = await restartSession(sessionId);
      setStates(res.states);
      setCurrentStepId(res.current_step_id);
      setLatestUpdate(null);
      setTrace([]);
      setBannerDismissed(true);
    } catch (err: unknown) {
      setAppError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="screenguard-app">
      {/* Header */}
      <header className="app-topbar">
        <div className="brand-group">
          <h1>
            Screen<span className="accent">Guard</span>
          </h1>
          <span className="tagline">AI Supervisor Agent for Enterprise Procedures</span>
        </div>

        <div className="header-badges">
          <div className="badge-item">
            <span
              className={`status-dot ${health?.status === "ok" ? "dot-online" : "dot-offline"}`}
            />
            <span>{health ? `Backend ${health.status.toUpperCase()} (${health.mode})` : "Backend Offline"}</span>
          </div>
          {sessionId && <div className="badge-item session-tag">Session: {sessionId}</div>}
        </div>
      </header>

      {/* Global Error Banner */}
      {appError && (
        <div className="app-error-banner">
          <span>{appError}</span>
          <button onClick={() => setAppError(null)}>Dismiss</button>
        </div>
      )}

      {/* Stats Bar */}
      <StatsBar
        stats={stats}
        callsTotal={budget.calls}
        estimatedSpendUsd={budget.spend}
      />

      {/* Main Grid: 2 Columns */}
      <div className="app-grid">
        {/* Left Column: Procedure & Checklist */}
        <div className="col-left">
          <ProcedurePanel
            procedure={procedure}
            onProcedureParsed={setProcedure}
            onStartSession={handleStartSession}
            isSessionActive={!!sessionId}
            isLoading={false}
          />

          <CapturePanel
            isSharing={isSharing}
            onStartShare={startCapture}
            onStopShare={stopCapture}
            onCheckNow={checkNow}
            isSessionActive={!!sessionId}
            voiceEnabled={voiceEnabled}
            onToggleVoice={() => setVoiceEnabled(!voiceEnabled)}
            onRestartSession={handleRestart}
          />

          {procedure && (
            <Checklist
              steps={procedure.steps}
              states={states}
              currentStepId={currentStepId}
              onOverride={handleOverride}
            />
          )}
        </div>

        {/* Right Column: Preview, Alerts & Trace */}
        <div className="col-right">
          {!bannerDismissed && latestUpdate && (
            <AlertBanner
              action={latestUpdate.action}
              warningText={latestUpdate.warning || null}
              reasonText={latestUpdate.reason}
              currentStepId={currentStepId}
              onDismiss={() => setBannerDismissed(true)}
              onConfirmDone={() => currentStepId && handleOverride(currentStepId, "done")}
              onNotDone={() => setBannerDismissed(true)}
            />
          )}

          <PreviewCanvas
            lastBlobUrl={lastBlobUrl}
            boxes={latestUpdate?.boxes || []}
          />

          <DecisionTrace trace={trace} />
        </div>
      </div>
    </div>
  );
}

export default App;
