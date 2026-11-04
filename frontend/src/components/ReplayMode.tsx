import React, { useState, useEffect, useRef, useCallback } from "react";
import type { ProcedureParseResult, StepState, StepUpdate, TraceEntry } from "../types";
import type { CaptureStats } from "../hooks/useCapture";

export interface ReplayManifest {
  captured_date: string;
  model: string;
  runs: {
    id: string;
    title: string;
    description: string;
    frame_count: number;
    session_file: string;
    frame_dir: string;
  }[];
}

export interface ReplayFrame {
  frame: string;
  frame_idx: number;
  truth_step?: number;
  agent_step?: string | null;
  action: "ADVANCE" | "WAIT" | "WARN" | "RECHECK" | "ASK_USER" | "STOP";
  reason: string;
  warning?: string | null;
  blocking?: boolean;
  confidence?: number;
  latency_ms?: number;
  calls_used?: number;
}

interface ReplayModeProps {
  onFrameUpdate: (data: {
    imageUrl: string;
    update: StepUpdate;
    states: Record<string, StepState>;
    currentStepId: string | null;
    traceEntry: TraceEntry;
    stats: CaptureStats;
    callsTotal: number;
    spendUsd: number;
  }) => void;
  onProcedureLoaded: (proc: ProcedureParseResult) => void;
  onReset: () => void;
  isReplayOnly?: boolean;
  onExitReplay?: () => void;
}

export const ReplayMode: React.FC<ReplayModeProps> = ({
  onFrameUpdate,
  onProcedureLoaded,
  onReset,
  isReplayOnly = false,
  onExitReplay,
}) => {
  const [manifest, setManifest] = useState<ReplayManifest | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string>("correct");
  const [frames, setFrames] = useState<ReplayFrame[]>([]);
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const currentIdxRef = useRef<number>(0);
  const framesRef = useRef<ReplayFrame[]>([]);

  useEffect(() => {
    currentIdxRef.current = currentIdx;
  }, [currentIdx]);

  useEffect(() => {
    framesRef.current = frames;
  }, [frames]);

  const stopPlayback = useCallback(() => {
    setIsPlaying(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const emitFrame = useCallback(
    (allFrames: ReplayFrame[], idx: number, run: ReplayManifest["runs"][0]) => {
      const f = allFrames[idx];
      const imageUrl = `${run.frame_dir}/${f.frame}`;

      // Compute cumulative states
      const states: Record<string, StepState> = {};
      for (let i = 0; i <= idx; i++) {
        const step = allFrames[i].agent_step;
        const action = allFrames[i].action;
        if (step) {
          if (action === "ADVANCE") states[step] = "done";
          else if (action === "WARN" || action === "STOP") states[step] = "wrong";
          else states[step] = "active";
        }
      }

      const pseudoUpdate: StepUpdate = {
        session_id: `replay-${run.id}`,
        frame_id: f.frame,
        states,
        current_step_id: f.agent_step || null,
        action: f.action,
        reason: f.reason,
        warning: f.warning || null,
        blocking: f.blocking || false,
        boxes: [],
        verdict: null,
        calls_used: f.calls_used || 1,
        estimated_spend_usd: (idx + 1) * 0.0003,
        latency_ms: f.latency_ms || 24,
        cached: false,
        events: [],
      };

      const traceEntry: TraceEntry = {
        id: `trc-replay-${idx}-${f.frame}`,
        ts: Date.now() / 1000,
        action: f.action,
        reason: f.reason,
        step_id: f.agent_step || "all",
        status: f.action === "ADVANCE" ? "done" : f.action === "WARN" ? "wrong" : "in_progress",
        confidence: f.confidence || 0.95,
        evidence: f.reason,
        warning: f.warning || null,
        calls_used: f.calls_used || 1,
        latency_ms: f.latency_ms || 24,
      };

      const latencies = allFrames.slice(0, idx + 1).map((x) => x.latency_ms || 24);

      const stats: CaptureStats = {
        framesSeen: idx + 1,
        framesSent: idx + 1,
        framesSkipped: 0,
        latencies,
      };

      onFrameUpdate({
        imageUrl,
        update: pseudoUpdate,
        states,
        currentStepId: f.agent_step || null,
        traceEntry,
        stats,
        callsTotal: idx + 1,
        spendUsd: (idx + 1) * 0.0003,
      });
    },
    [onFrameUpdate]
  );

  // 1. Load manifest and demo procedure on mount
  useEffect(() => {
    async function init() {
      try {
        const [manifestRes, procRes] = await Promise.all([
          fetch("/replay/manifest.json"),
          fetch("/demo-procedure.json"),
        ]);
        if (!manifestRes.ok) throw new Error("Failed to load /replay/manifest.json");
        const m: ReplayManifest = await manifestRes.json();
        setManifest(m);

        if (procRes.ok) {
          const p: ProcedureParseResult = await procRes.json();
          onProcedureLoaded(p);
        }
      } catch (e: any) {
        setError(`Replay init error: ${e.message}`);
      }
    }
    init();
  }, [onProcedureLoaded]);

  // 2. Load frames when selectedRunId changes
  useEffect(() => {
    if (!manifest) return;
    const run = manifest.runs.find((r) => r.id === selectedRunId);
    if (!run) return;

    let isSubscribed = true;
    async function loadRun() {
      try {
        stopPlayback();
        const res = await fetch(run!.session_file);
        if (!res.ok) throw new Error(`Could not load ${run!.session_file}`);
        const data: ReplayFrame[] = await res.json();
        if (!isSubscribed) return;
        setFrames(data);
        setCurrentIdx(0);
        onReset();
        // Emit first frame
        if (data.length > 0) {
          emitFrame(data, 0, run!);
        }
      } catch (e: any) {
        if (isSubscribed) {
          setError(`Failed to load replay session: ${e.message}`);
        }
      }
    }
    loadRun();
    return () => {
      isSubscribed = false;
    };
  }, [manifest, selectedRunId, stopPlayback, emitFrame, onReset]);

  // 3. Playback timer (1 frame per second)
  useEffect(() => {
    if (isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        const nextIdx = currentIdxRef.current + 1;
        const run = manifest?.runs.find((r) => r.id === selectedRunId);
        if (!run || !framesRef.current || nextIdx >= framesRef.current.length) {
          setIsPlaying(false);
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
          return;
        }
        currentIdxRef.current = nextIdx;
        setCurrentIdx(nextIdx);
        emitFrame(framesRef.current, nextIdx, run);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPlaying, manifest, selectedRunId, emitFrame]);

  const handlePlayPause = () => {
    if (isPlaying) {
      stopPlayback();
    } else {
      if (currentIdx >= frames.length - 1) {
        handleRestart();
      }
      setIsPlaying(true);
    }
  };

  const handleRestart = () => {
    stopPlayback();
    setCurrentIdx(0);
    onReset();
    const run = manifest?.runs.find((r) => r.id === selectedRunId);
    if (run && frames.length > 0) {
      emitFrame(frames, 0, run);
    }
  };

  const currentRun = manifest?.runs.find((r) => r.id === selectedRunId);

  return (
    <div className="card replay-controller">
      {/* Required Label: Never presented as live */}
      <div className="replay-disclaimer-banner">
        <span className="replay-tag">REPLAY MODE</span>
        <span className="replay-text">
          Recorded session: real outputs of <strong>{manifest?.model || "evaluation model"}</strong> captured on {manifest?.captured_date || "2026-11-03"}. Replay is never presented as live.
        </span>
      </div>

      {error && <div className="replay-error">{error}</div>}

      <div className="replay-controls-row">
        <div className="replay-select-group">
          <label htmlFor="run-picker">Select Recorded Run:</label>
          <select
            id="run-picker"
            className="replay-select"
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
          >
            {manifest?.runs.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title}
              </option>
            ))}
          </select>
        </div>

        <div className="replay-btn-group">
          <button className="btn-replay-action" onClick={handlePlayPause}>
            {isPlaying ? "⏸ Pause" : "▶ Play"}
          </button>
          <button className="btn-replay-action" onClick={handleRestart}>
            ↺ Restart
          </button>
          {!isReplayOnly && onExitReplay && (
            <button className="btn-replay-exit" onClick={onExitReplay}>
              ✕ Exit Replay
            </button>
          )}
        </div>
      </div>

      {currentRun && (
        <div className="replay-run-info">
          <p className="run-desc">{currentRun.description}</p>
          <div className="run-progress">
            <span>
              Frame <strong>{frames.length > 0 ? currentIdx + 1 : 0}</strong> of <strong>{frames.length}</strong> (1 frame/sec)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
