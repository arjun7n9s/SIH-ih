/** Brand assets — keep sprite meta in sync with public/brand/iiitdmj-logo-sprite.json */
export const ORG_HEADER_SRC = "/brand/iiitdmj-org-header.png";
export const MARK_SRC = "/iiitdmj-logo.png";

export const SITE_PAPER = "#F1F4EC";
export const SITE_MIST = "#E6ECE3";

/**
 * User 32-frame sprite (enhanced 2×): 8×4 grid, 256² cells, row-major.
 * Assemble → full mark + satellite → disassemble. Seamless loop (~1.33s @ 24fps).
 */
export const LOGO_SPRITE = {
  src: "/brand/iiitdmj-logo-sprite.png",
  frames: 32,
  cols: 8,
  rows: 4,
  frameWidth: 256,
  frameHeight: 256,
  fps: 24,
  durationMs: Math.round((32 / 24) * 1000), // ~1333ms
} as const;
