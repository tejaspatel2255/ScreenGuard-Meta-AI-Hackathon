import { describe, it, expect, beforeEach } from "vitest";
import { ChangeDetector } from "./changeDetection";

describe("ChangeDetector unit tests", () => {
  let detector: ChangeDetector;

  beforeEach(() => {
    detector = new ChangeDetector(10, 800);
  });

  it("1. Sends initial baseline frame", () => {
    const thumb = new Uint8ClampedArray(1024).fill(128);
    const res = detector.update(thumb, 1000);
    expect(res.changed).toBe(true);
    expect(res.shouldSend).toBe(true);
  });

  it("2. Identical frames do not trigger change or send", () => {
    const thumb = new Uint8ClampedArray(1024).fill(128);
    detector.update(thumb, 1000); // Baseline

    const res2 = detector.update(thumb, 1500);
    expect(res2.changed).toBe(false);
    expect(res2.shouldSend).toBe(false);
  });

  it("3. Small insignificant noise below threshold is ignored", () => {
    const thumb1 = new Uint8ClampedArray(1024).fill(100);
    detector.update(thumb1, 1000);

    // Change by 4 levels (below threshold 10)
    const thumb2 = new Uint8ClampedArray(1024).fill(104);
    const res = detector.update(thumb2, 1700);
    expect(res.changed).toBe(false);
    expect(res.shouldSend).toBe(false);
  });

  it("4. Big change flags change and waits for stability period", () => {
    const thumb1 = new Uint8ClampedArray(1024).fill(50);
    detector.update(thumb1, 1000);

    // Large difference (diff = 50 > 10)
    const thumb2 = new Uint8ClampedArray(1024).fill(100);
    const resChange = detector.update(thumb2, 2000);
    expect(resChange.changed).toBe(true);
    expect(resChange.shouldSend).toBe(false); // Wait for stabilization

    // 400ms later (not stable yet, 400 < 800)
    const resWait = detector.update(thumb2, 2400);
    expect(resWait.shouldSend).toBe(false);

    // 850ms later (stable for >= 800ms)
    const resSend = detector.update(thumb2, 2850);
    expect(resSend.shouldSend).toBe(true);
  });

  it("5. Reset clears previous thumbnail and state", () => {
    const thumb = new Uint8ClampedArray(1024).fill(128);
    detector.update(thumb, 1000);
    detector.reset();

    // After reset, should behave like initial baseline again
    const res = detector.update(thumb, 2000);
    expect(res.changed).toBe(true);
    expect(res.shouldSend).toBe(true);
  });
});
