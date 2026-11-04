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
import { useCapture, type CaptureStats } from "./hooks/useCapture";
import { ProcedurePanel } from "./components/ProcedurePanel";
import { CapturePanel } from "./components/CapturePanel";
import { Checklist } from "./components/Checklist";
import { AlertBanner } from "./components/AlertBanner";
import { DecisionTrace } from "./components/DecisionTrace";
import { StatsBar } from "./components/StatsBar";
import { PreviewCanvas } from "./components/PreviewCanvas";
import { ReplayMode } from "./components/ReplayMode";

const isReplayOnly =
  import.meta.env.VITE_REPLAY_ONLY === "true" ||
  import.meta.env.VITE_REPLAY_ONLY === true;

export function App() {
  const [health, setHealth] = useState<HealthInfo | null>(
    isReplayOnly ? { status: "ok", mode: "replay" } : null
  );
  const [procedure, setProcedure] = useState<ProcedureParseResult | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [states, setStates] = useState<Record<string, StepState>>({});
  const [currentStepId, setCurrentStepId] = useState<string | null>(null);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [latestUpdate, setLatestUpdate] = useState<StepUpdate | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [lastBlobUrl] = useState<string | null>(null);
  const [replayImageUrl, setReplayImageUrl] = useState<string | null>(null);
  const [appError, setAppError] = useState<string | null>(null);
  const [budget, setBudget] = useState<{ calls: number; spend: number }>({ calls: 0, spend: 0 });

  // Replay mode state
  const [isReplayMode, setIsReplayMode] = useState<boolean>(isReplayOnly);
  const [replayStats, setReplayStats] = useState<CaptureStats>({
    framesSeen: 0,
    framesSent: 0,
    framesSkipped: 0,
    latencies: [],
  });

  const lastSpokenWarningRef = useRef<string | null>(null);

  // Poll health & budget only in live mode
  const loadStatus = useCallback(async () => {
    if (isReplayOnly) return;
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
    if (isReplayOnly) return;
    const timer = setTimeout(() => {
      loadStatus();
    }, 0);
    const interval = setInterval(loadStatus, 4000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
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
      setReplayImageUrl(null);
    } catch (err: unknown) {
      setAppError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleOverride = async (stepId: string, state: StepState) => {
    if (isReplayMode) {
      setStates((prev) => ({ ...prev, [stepId]: state }));
      return;
    }
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
    if (isReplayMode) {
      handleReplayReset();
      return;
    }
    if (!sessionId) return;
    try {
      const res = await restartSession(sessionId);
      setStates(res.states);
      setCurrentStepId(res.current_step_id);
      setLatestUpdate(null);
      setTrace([]);
      setBannerDismissed(true);
      setReplayImageUrl(null);
    } catch (err: unknown) {
      setAppError(err instanceof Error ? err.message : String(err));
    }
  };

  // Replay handlers
  const handleReplayFrameUpdate = (data: {
    imageUrl: string;
    update: StepUpdate;
    states: Record<string, StepState>;
    currentStepId: string | null;
    traceEntry: TraceEntry;
    stats: CaptureStats;
    callsTotal: number;
    spendUsd: number;
  }) => {
    setReplayImageUrl(data.imageUrl);
    setLatestUpdate(data.update);
    setStates(data.states);
    setCurrentStepId(data.currentStepId);
    setTrace((prev) => [...prev, data.traceEntry]);
    setReplayStats(data.stats);
    setBudget({ calls: data.callsTotal, spend: data.spendUsd });
    setBannerDismissed(false);

    if (data.update.warning) {
      speakWarning(data.update.warning);
    }
  };

  const handleReplayReset = () => {
    setLatestUpdate(null);
    setTrace([]);
    setBannerDismissed(true);
    setStates({});
    setCurrentStepId(null);
    setReplayImageUrl(null);
    setReplayStats({ framesSeen: 0, framesSent: 0, framesSkipped: 0, latencies: [] });
    setBudget({ calls: 0, spend: 0 });
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
          {!isReplayOnly ? (
            <>
              <button
                className="btn-watch-replay"
                onClick={() => {
                  setIsReplayMode(!isReplayMode);
                  handleReplayReset();
                }}
              >
                {isReplayMode ? "✕ Exit Replay" : "🎬 Watch Recorded Demo"}
              </button>
              <div className="badge-item">
                <span
                  className={`status-dot ${health?.status === "ok" ? "dot-online" : "dot-offline"}`}
                />
                <span>{health ? `Backend ${health.status.toUpperCase()} (${health.mode})` : "Backend Offline"}</span>
              </div>
              {sessionId && <div className="badge-item session-tag">Session: {sessionId}</div>}
            </>
          ) : (
            <div className="badge-item replay-tag">STATIC REPLAY ONLY (NO BACKEND)</div>
          )}
        </div>
      </header>

      {/* Global Error Banner */}
      {appError && (
        <div className={`app-error-banner ${appError.includes("429") ? "error-banner-budget" : appError.includes("413") ? "error-banner-size" : appError.includes("415") ? "error-banner-media" : ""}`}>
          <div className="error-banner-text">
            <strong>{appError.includes("429") ? "LIMIT REACHED" : appError.includes("413") ? "FRAME OVERSIZE" : appError.includes("415") ? "FORMAT ERROR" : "ALERT"}:</strong> {appError}
          </div>
          <button onClick={() => setAppError(null)}>Dismiss</button>
        </div>
      )}

      {/* Stats Bar */}
      <StatsBar
        stats={isReplayMode ? replayStats : stats}
        callsTotal={budget.calls}
        estimatedSpendUsd={budget.spend}
      />

      {/* Main Grid: 2 Columns */}
      <div className="app-grid">
        {/* Left Column: Procedure & Checklist / Replay Controls */}
        <div className="col-left">
          {isReplayMode ? (
            <ReplayMode
              onFrameUpdate={handleReplayFrameUpdate}
              onProcedureLoaded={setProcedure}
              onReset={handleReplayReset}
              isReplayOnly={isReplayOnly}
              onExitReplay={() => {
                setIsReplayMode(false);
                handleReplayReset();
              }}
            />
          ) : (
            <>
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
            </>
          )}

          {procedure && (
            <Checklist
              steps={procedure.steps}
              states={states}
              currentStepId={currentStepId}
              onOverride={handleOverride}
            />
          )}
        </div>

        {/* Right Column: Preview, Alerts & Decision Trace */}
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
            lastBlobUrl={replayImageUrl || lastBlobUrl}
            boxes={latestUpdate?.boxes || []}
          />

          <DecisionTrace trace={trace} />
        </div>
      </div>
    </div>
  );
}

export default App;
