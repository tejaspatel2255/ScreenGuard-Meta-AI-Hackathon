import React, { useRef, useEffect } from "react";
import type { BoundingBox } from "../types";

interface PreviewCanvasProps {
  lastBlobUrl: string | null;
  boxes: BoundingBox[];
}

export const PreviewCanvas: React.FC<PreviewCanvasProps> = ({ lastBlobUrl, boxes }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !lastBlobUrl) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.src = lastBlobUrl;
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      ctx.drawImage(img, 0, 0);

      // Draw bounding boxes: normalized [ymin, xmin, ymax, xmax]
      boxes.forEach((b) => {
        const [ymin, xmin, ymax, xmax] = b.box_2d;
        const x = xmin * canvas.width;
        const y = ymin * canvas.height;
        const w = (xmax - xmin) * canvas.width;
        const h = (ymax - ymin) * canvas.height;

        ctx.strokeStyle = "#00e5ff";
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);

        ctx.fillStyle = "rgba(0, 229, 255, 0.25)";
        ctx.fillRect(x, y, w, h);

        // Label tag
        ctx.fillStyle = "#00e5ff";
        ctx.font = "bold 16px sans-serif";
        ctx.fillText(b.label, x + 4, Math.max(20, y - 6));
      });
    };
  }, [lastBlobUrl, boxes]);

  return (
    <div className="card preview-card">
      <div className="preview-header">
        <h2>Live Frame Vision View</h2>
        {boxes.length > 0 && <span className="boxes-count">{boxes.length} elements located</span>}
      </div>

      <div className="preview-canvas-wrapper">
        {lastBlobUrl ? (
          <canvas ref={canvasRef} className="preview-canvas" />
        ) : (
          <div className="preview-placeholder">
            <p>Awaiting shared browser tab...</p>
          </div>
        )}
      </div>
    </div>
  );
};
