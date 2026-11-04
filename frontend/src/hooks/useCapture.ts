import { useState, useRef, useEffect, useCallback } from "react";
import { ChangeDetector } from "../lib/changeDetection";
import { sendFrame } from "../api";
import type { StepUpdate } from "../types";

export interface CaptureStats {
  framesSeen: number;
  framesSent: number;
  framesSkipped: number;
  latencies: number[];
}

interface UseCaptureProps {
  sessionId: string | null;
  onUpdate: (update: StepUpdate) => void;
  onError: (err: string) => void;
}

export function useCapture({ sessionId, onUpdate, onError }: UseCaptureProps) {
  const [isSharing, setIsSharing] = useState(false);
  const [stats, setStats] = useState<CaptureStats>({
    framesSeen: 0,
    framesSent: 0,
    framesSkipped: 0,
    latencies: [],
  });

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const thumbCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const detectorRef = useRef<ChangeDetector>(new ChangeDetector(12, 800));
  const isSendingRef = useRef<boolean>(false);

  // Stop sharing cleanly
  const stopCapture = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    detectorRef.current.reset();
    setIsSharing(false);
  }, []);

  const captureAndEvaluate = useCallback(
    async (forceSend = false) => {
      if (!videoRef.current || !canvasRef.current || !sessionId) return;
      if (videoRef.current.readyState < 2) return; // HAVE_CURRENT_DATA
      if (isSendingRef.current) {
        setStats((s) => ({ ...s, framesSkipped: s.framesSkipped + 1 }));
        return;
      }

      setStats((s) => ({ ...s, framesSeen: s.framesSeen + 1 }));

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Downscale to max 1024 width
      const maxW = 1024;
      const ratio = video.videoWidth > maxW ? maxW / video.videoWidth : 1;
      const targetW = Math.round(video.videoWidth * ratio);
      const targetH = Math.round(video.videoHeight * ratio);

      if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
      }
      ctx.drawImage(video, 0, 0, targetW, targetH);

      // Create 32x32 thumbnail for change detection
      if (!thumbCanvasRef.current) {
        thumbCanvasRef.current = document.createElement("canvas");
        thumbCanvasRef.current.width = 32;
        thumbCanvasRef.current.height = 32;
      }
      const tCanvas = thumbCanvasRef.current;
      const tCtx = tCanvas.getContext("2d");
      if (!tCtx) return;

      tCtx.drawImage(canvas, 0, 0, 32, 32);
      const imgData = tCtx.getImageData(0, 0, 32, 32);
      const d = imgData.data;

      // Convert to 1024 grayscale values
      const thumb = new Uint8ClampedArray(1024);
      for (let i = 0, j = 0; i < d.length; i += 4, j++) {
        thumb[j] = Math.round(0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]);
      }

      const { shouldSend } = detectorRef.current.update(thumb);

      if (shouldSend || forceSend) {
        isSendingRef.current = true;
        canvas.toBlob(
          async (blob) => {
            if (!blob) {
              isSendingRef.current = false;
              return;
            }
            try {
              const update = await sendFrame(sessionId, blob);
              setStats((s) => ({
                ...s,
                framesSent: s.framesSent + 1,
                latencies: [...s.latencies, update.latency_ms].slice(-20),
              }));
              onUpdate(update);
            } catch (err: unknown) {
              const msg = err instanceof Error ? err.message : String(err);
              onError(msg);
              if (msg.includes("413") || msg.includes("415") || msg.includes("429")) {
                stopCapture();
              }
            } finally {
              isSendingRef.current = false;
            }
          },
          "image/jpeg",
          0.7
        );
      } else {
        setStats((s) => ({ ...s, framesSkipped: s.framesSkipped + 1 }));
      }
    },
    [sessionId, onUpdate, onError, stopCapture]
  );

  const startCapture = useCallback(async () => {
    if (!sessionId) {
      onError("Please start a procedure session first.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: "browser" },
        audio: false,
      });

      streamRef.current = stream;

      // Listen for browser stop button
      stream.getVideoTracks()[0].addEventListener("ended", () => {
        stopCapture();
      });

      if (!videoRef.current) {
        videoRef.current = document.createElement("video");
        videoRef.current.autoplay = true;
        videoRef.current.playsInline = true;
        videoRef.current.muted = true;
      }
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      if (!canvasRef.current) {
        canvasRef.current = document.createElement("canvas");
      }

      detectorRef.current.reset();
      setIsSharing(true);

      // Check every 700 ms
      timerRef.current = window.setInterval(() => {
        captureAndEvaluate(false);
      }, 700);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("Permission denied") || msg.includes("denied")) {
        onError("Screen capture permission was denied by the user.");
      } else {
        onError(`Capture failed: ${msg}`);
      }
      stopCapture();
    }
  }, [sessionId, onError, stopCapture, captureAndEvaluate]);

  const checkNow = useCallback(() => {
    captureAndEvaluate(true);
  }, [captureAndEvaluate]);

  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, [stopCapture]);

  return {
    isSharing,
    startCapture,
    stopCapture,
    checkNow,
    stats,
  };
}
