/* iOS 26 Liquid Glass Ergonomics & Spring Physics Engine */
(() => {
  "use strict";

  const initLiquidGlass = () => {
    // 1. Device Gyro / Parallax Optical Tilt for Mobile
    if (window.DeviceOrientationEvent) {
      window.addEventListener("deviceorientation", (e) => {
        if (e.gamma !== null && e.beta !== null) {
          const tiltX = Math.max(-12, Math.min(12, e.gamma));
          const tiltY = Math.max(-12, Math.min(12, e.beta - 45));
          document.documentElement.style.setProperty("--tilt-x", `${tiltX.toFixed(2)}deg`);
          document.documentElement.style.setProperty("--tilt-y", `${tiltY.toFixed(2)}deg`);
        }
      }, { passive: true });
    }

    // 2. Fluid Spring Tactile Micro-Interactions (Scale Compress on Active)
    document.addEventListener("pointerdown", (e) => {
      const btn = e.target.closest("button, .btn, .chip, .tool, .nav-item, .pick, .option, .context-chip");
      if (btn) {
        btn.style.setProperty("--press-scale", "0.968");
      }
    }, { passive: true });

    document.addEventListener("pointerup", (e) => {
      const btn = e.target.closest("button, .btn, .chip, .tool, .nav-item, .pick, .option, .context-chip");
      if (btn) {
        btn.style.removeProperty("--press-scale");
      }
    }, { passive: true });

    document.addEventListener("pointercancel", () => {
      document.querySelectorAll("[style*='--press-scale']").forEach((el) => {
        el.style.removeProperty("--press-scale");
      });
    }, { passive: true });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLiquidGlass);
  } else {
    initLiquidGlass();
  }
})();
