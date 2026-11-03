/**
 * Fast change detection using 32x32 grayscale thumbnails.
 */
export class ChangeDetector {
  private previousThumbnail: Uint8ClampedArray | null = null;
  private lastChangeTime: number = 0;
  private changeDetected: boolean = false;
  private threshold: number;
  private stableMs: number;

  constructor(threshold = 12, stableMs = 800) {
    this.threshold = threshold;
    this.stableMs = stableMs;
  }

  /**
   * Resets the change detector state.
   */
  public reset(): void {
    this.previousThumbnail = null;
    this.lastChangeTime = 0;
    this.changeDetected = false;
  }

  /**
   * Compares two 32x32 grayscale arrays (1024 elements).
   * Returns average absolute difference per pixel.
   */
  public calculateDiff(current: Uint8ClampedArray, previous: Uint8ClampedArray): number {
    let diffSum = 0;
    const len = Math.min(current.length, previous.length);
    for (let i = 0; i < len; i++) {
      diffSum += Math.abs(current[i] - previous[i]);
    }
    return diffSum / len;
  }

  /**
   * Processes a new thumbnail and determines if the screen changed and then stabilized.
   *
   * @param currentThumbnail 32x32 grayscale values (length 1024)
   * @param now Current timestamp in milliseconds
   * @returns { changed: boolean, shouldSend: boolean }
   */
  public update(
    currentThumbnail: Uint8ClampedArray,
    now = Date.now()
  ): { changed: boolean; shouldSend: boolean } {
    if (!this.previousThumbnail) {
      this.previousThumbnail = new Uint8ClampedArray(currentThumbnail);
      this.lastChangeTime = now;
      this.changeDetected = false;
      return { changed: true, shouldSend: true }; // Send initial baseline frame
    }

    const diff = this.calculateDiff(currentThumbnail, this.previousThumbnail);
    const hasMeaningfulChange = diff >= this.threshold;

    if (hasMeaningfulChange) {
      // Screen is actively changing
      this.previousThumbnail = new Uint8ClampedArray(currentThumbnail);
      this.lastChangeTime = now;
      this.changeDetected = true;
      return { changed: true, shouldSend: false };
    }

    // No new change: check if it was previously changing and has now been stable for stableMs
    if (this.changeDetected) {
      const elapsed = now - this.lastChangeTime;
      if (elapsed >= this.stableMs) {
        this.changeDetected = false;
        return { changed: false, shouldSend: true };
      }
    }

    return { changed: false, shouldSend: false };
  }
}
