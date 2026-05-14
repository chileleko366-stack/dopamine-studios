// remotion/compositions/CelebrityCard.tsx
//
// Cinematic celebrity portrait composition.
//
// Takes a celebrity cutout PNG URL + channel-specific treatment props,
// renders a designed editorial frame around them. The cutout itself does
// not animate -- the frame moves (Ken-Burns zoom, particles, light leaks,
// grain, color grade) so the static photo reads as cinematic motion.
//
// Treatments differ per channel:
//   CH1 Dopamine Loop  -> cinematic_dark    (yellow accent, particles, deep shadow)
//   CH2 FinanceFiction -> cinematic_graph   (graph overlay behind portrait)
//   CH3 REDACTED       -> archival_redact   (sepia, redaction bar over name)
//   CH4 Grey Matter    -> editorial_clean   (clean indigo bg, serif annotation)
//   CH5 Quiet Record   -> archival_sepia    (parchment bg, Ken-Burns, serif caption)
//
// Falls back to text-only treatment if no cutout URL is provided.

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  AbsoluteFill,
  Img,
} from "remotion";

type Treatment =
  | "cinematic_dark"
  | "cinematic_graph"
  | "archival_redact"
  | "editorial_clean"
  | "archival_sepia";

interface CelebrityCardProps {
  celebrityName: string;
  cutoutUrl?: string;             // PNG with transparent bg, or omit for text-only
  treatment: Treatment;
  primaryColor: string;
  backgroundColor: string;
  accentColor?: string;
  context?: string;               // 1-line context, e.g. "MUSICIAN, 2019" or "1967-2021"
  quote?: string;                 // Short pull quote (max ~10 words)
  intensity?: number;             // 0-1, affects motion amount
}

export const CelebrityCard: React.FC<CelebrityCardProps> = ({
  celebrityName,
  cutoutUrl,
  treatment,
  primaryColor,
  backgroundColor,
  accentColor,
  context,
  quote,
  intensity = 0.6,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width } = useVideoConfig();

  const accent = accentColor || primaryColor;

  // Master opacity envelope: fade in, hold, fade out
  const opacity = interpolate(
    frame,
    [0, 12, durationInFrames - 12, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Slow Ken-Burns on the cutout: subtle scale + drift
  const kenBurnsScale = interpolate(
    frame,
    [0, durationInFrames],
    [1.0, 1.0 + 0.06 * intensity]
  );
  const kenBurnsX = interpolate(frame, [0, durationInFrames], [0, -8 * intensity]);

  // Treatment-specific rendering
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      {/* Background layer (per treatment) */}
      <BackgroundLayer treatment={treatment} primaryColor={primaryColor} accent={accent} frame={frame} intensity={intensity} />

      {/* Celebrity cutout layer */}
      {cutoutUrl ? (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              transform: `scale(${kenBurnsScale}) translateX(${kenBurnsX}px)`,
              height: "85%",
              filter: getCutoutFilter(treatment),
            }}
          >
            <Img
              src={cutoutUrl}
              style={{
                height: "100%",
                width: "auto",
                objectFit: "contain",
              }}
            />
          </div>
        </div>
      ) : (
        // No cutout available -- text-only fallback
        <NoCutoutFallback celebrityName={celebrityName} treatment={treatment} primaryColor={primaryColor} />
      )}

      {/* Foreground overlays (particles, grain, light leaks per treatment) */}
      <ForegroundLayer treatment={treatment} primaryColor={primaryColor} accent={accent} frame={frame} intensity={intensity} />

      {/* Text composition layer */}
      <TextLayer
        treatment={treatment}
        celebrityName={celebrityName}
        context={context}
        quote={quote}
        primaryColor={primaryColor}
        accent={accent}
        frame={frame}
        durationInFrames={durationInFrames}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------------------
// Background layers per treatment
// ---------------------------------------------------------------------------

const BackgroundLayer: React.FC<{
  treatment: Treatment;
  primaryColor: string;
  accent: string;
  frame: number;
  intensity: number;
}> = ({ treatment, primaryColor, accent, frame, intensity }) => {
  switch (treatment) {
    case "cinematic_dark": {
      // Radial spotlight from upper-left, deep falloff
      return (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `radial-gradient(circle at 30% 30%, ${accent}22 0%, transparent 50%)`,
          }}
        />
      );
    }

    case "cinematic_graph": {
      // Faint financial grid + a rising line behind
      const lineProgress = interpolate(frame, [0, 90], [0, 100], {
        extrapolateRight: "clamp",
      });
      return (
        <>
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ position: "absolute", inset: 0, opacity: 0.15 }}
          >
            {[10, 25, 40, 55, 70, 85].map((y) => (
              <line key={y} x1="0" y1={y} x2="100" y2={y} stroke={accent} strokeWidth="0.2" />
            ))}
            {[15, 30, 45, 60, 75, 90].map((x) => (
              <line key={x} x1={x} y1="0" x2={x} y2="100" stroke={accent} strokeWidth="0.2" />
            ))}
          </svg>
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ position: "absolute", inset: 0 }}
          >
            <polyline
              points={`0,80 ${lineProgress * 0.2},75 ${lineProgress * 0.4},68 ${lineProgress * 0.6},55 ${lineProgress * 0.8},40 ${lineProgress},25`}
              stroke={accent}
              strokeWidth="0.4"
              fill="none"
              opacity={0.5}
            />
          </svg>
        </>
      );
    }

    case "archival_redact": {
      // Manila/parchment base + faint typewriter texture
      return (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(180deg, #1a1008 0%, #0d0805 100%)`,
          }}
        />
      );
    }

    case "editorial_clean": {
      // Soft vertical gradient, generous negative space
      return (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(180deg, ${accent}08 0%, transparent 60%)`,
          }}
        />
      );
    }

    case "archival_sepia": {
      // Parchment / lamplight warmth
      return (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `radial-gradient(ellipse at 50% 60%, #2a1d10 0%, #150c06 70%)`,
          }}
        />
      );
    }
  }
};

// ---------------------------------------------------------------------------
// Cutout image filter per treatment (CSS filter chain)
// ---------------------------------------------------------------------------

function getCutoutFilter(treatment: Treatment): string {
  switch (treatment) {
    case "cinematic_dark":
      return "brightness(0.95) contrast(1.1) saturate(0.4) drop-shadow(0 10px 40px rgba(0,0,0,0.8))";
    case "cinematic_graph":
      return "brightness(0.9) contrast(1.15) saturate(0.3) drop-shadow(0 8px 30px rgba(0,0,0,0.7))";
    case "archival_redact":
      return "sepia(0.7) brightness(0.85) contrast(1.1) saturate(0.5)";
    case "editorial_clean":
      return "brightness(1.0) contrast(1.05) saturate(0.9)";
    case "archival_sepia":
      return "sepia(0.85) brightness(0.9) contrast(1.05) saturate(0.7)";
  }
}

// ---------------------------------------------------------------------------
// Foreground overlays per treatment
// ---------------------------------------------------------------------------

const ForegroundLayer: React.FC<{
  treatment: Treatment;
  primaryColor: string;
  accent: string;
  frame: number;
  intensity: number;
}> = ({ treatment, primaryColor, accent, frame, intensity }) => {
  // Common film grain (all treatments use it, varying opacity)
  const grainOpacity = treatment === "editorial_clean" ? 0.04 : treatment === "cinematic_dark" ? 0.15 : 0.10;

  return (
    <>
      {/* Procedural film grain */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: grainOpacity,
          mixBlendMode: "overlay",
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundSize: "200px 200px",
        }}
      />

      {/* Treatment-specific particles or overlays */}
      {treatment === "cinematic_dark" && (
        <DustParticles accent={accent} frame={frame} intensity={intensity} />
      )}

      {treatment === "cinematic_graph" && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(0deg, ${accent}10 0%, transparent 30%)`,
          }}
        />
      )}

      {treatment === "archival_redact" && (
        // Subtle scanline overlay -- typewriter / photocopy feel
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 3px)`,
            pointerEvents: "none",
          }}
        />
      )}

      {treatment === "archival_sepia" && (
        // Vignette darkening
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,0.6) 100%)`,
            pointerEvents: "none",
          }}
        />
      )}
    </>
  );
};

// ---------------------------------------------------------------------------
// Dust particles for cinematic_dark treatment
// ---------------------------------------------------------------------------

const DustParticles: React.FC<{ accent: string; frame: number; intensity: number }> = ({
  accent,
  frame,
  intensity,
}) => {
  // Deterministic particles using seeded positions
  const particles = Array.from({ length: 30 }, (_, i) => {
    const seed = i * 137.5;
    const baseX = (seed * 7.31) % 100;
    const baseY = (seed * 4.13) % 100;
    const drift = Math.sin(frame * 0.02 + i) * 3;
    const size = 1 + (i % 4) * 0.5;
    const opacity = 0.15 + (i % 5) * 0.1;
    return {
      x: baseX + drift,
      y: baseY + drift * 0.5,
      size,
      opacity,
    };
  });

  return (
    <svg
      width="100%"
      height="100%"
      style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
    >
      {particles.map((p, i) => (
        <circle
          key={i}
          cx={`${p.x}%`}
          cy={`${p.y}%`}
          r={p.size}
          fill={accent}
          opacity={p.opacity * intensity}
        />
      ))}
    </svg>
  );
};

// ---------------------------------------------------------------------------
// Text overlays per treatment
// ---------------------------------------------------------------------------

const TextLayer: React.FC<{
  treatment: Treatment;
  celebrityName: string;
  context?: string;
  quote?: string;
  primaryColor: string;
  accent: string;
  frame: number;
  durationInFrames: number;
}> = ({ treatment, celebrityName, context, quote, primaryColor, accent, frame, durationInFrames }) => {
  // Name fades in slightly after the cutout
  const nameOpacity = interpolate(
    frame,
    [20, 30, durationInFrames - 15, durationInFrames - 5],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Quote fades in later still
  const quoteOpacity = quote
    ? interpolate(
        frame,
        [40, 55, durationInFrames - 20, durationInFrames - 5],
        [0, 1, 1, 0],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
      )
    : 0;

  // Layout per treatment
  switch (treatment) {
    case "cinematic_dark":
    case "cinematic_graph":
      return (
        <>
          {/* Name in bottom-left, Anton condensed all-caps */}
          <div
            style={{
              position: "absolute",
              bottom: "8%",
              left: "6%",
              opacity: nameOpacity,
              fontFamily: "Anton, sans-serif",
              color: "white",
              fontSize: 72,
              textTransform: "uppercase",
              letterSpacing: 2,
              lineHeight: 1,
            }}
          >
            {celebrityName}
            {context && (
              <div
                style={{
                  fontSize: 28,
                  color: accent,
                  letterSpacing: 6,
                  marginTop: 8,
                  opacity: 0.9,
                }}
              >
                {context}
              </div>
            )}
          </div>

          {/* Pull quote top-right if present */}
          {quote && (
            <div
              style={{
                position: "absolute",
                top: "10%",
                right: "6%",
                maxWidth: "40%",
                opacity: quoteOpacity,
                fontFamily: "Anton, sans-serif",
                color: accent,
                fontSize: 42,
                textTransform: "uppercase",
                letterSpacing: 1,
                lineHeight: 1.1,
                textAlign: "right",
              }}
            >
              "{quote}"
            </div>
          )}
        </>
      );

    case "archival_redact":
      return (
        <>
          {/* Typewriter-font caption with redaction bar over part of the name */}
          <div
            style={{
              position: "absolute",
              bottom: "10%",
              left: "8%",
              opacity: nameOpacity,
              fontFamily: "'Courier Prime', 'Courier New', monospace",
              color: "#f0e8d8",
              fontSize: 56,
              textTransform: "uppercase",
              letterSpacing: 4,
              lineHeight: 1.1,
            }}
          >
            {celebrityName}
            {context && (
              <div
                style={{
                  fontSize: 24,
                  color: "#c8a24b",
                  marginTop: 12,
                  letterSpacing: 2,
                }}
              >
                {context}
              </div>
            )}
          </div>

          {/* Classification stamp top-right */}
          <div
            style={{
              position: "absolute",
              top: "8%",
              right: "6%",
              fontFamily: "'Courier Prime', monospace",
              fontSize: 36,
              color: "#ff3333",
              border: "3px solid #ff3333",
              padding: "8px 20px",
              transform: "rotate(-5deg)",
              letterSpacing: 4,
              opacity: nameOpacity * 0.85,
            }}
          >
            DECLASSIFIED
          </div>

          {quote && (
            <div
              style={{
                position: "absolute",
                top: "20%",
                left: "8%",
                maxWidth: "45%",
                opacity: quoteOpacity,
                fontFamily: "'Courier Prime', monospace",
                color: "#f0e8d8",
                fontSize: 28,
                lineHeight: 1.4,
                fontStyle: "italic",
              }}
            >
              "{quote}"
            </div>
          )}
        </>
      );

    case "editorial_clean":
      return (
        <>
          {/* Serif name in bottom area, generous spacing */}
          <div
            style={{
              position: "absolute",
              bottom: "12%",
              left: "8%",
              opacity: nameOpacity,
              fontFamily: "'Tiempos Text', 'Crimson Text', Georgia, serif",
              color: "white",
              fontSize: 64,
              fontWeight: 500,
              lineHeight: 1,
              letterSpacing: -0.5,
            }}
          >
            {celebrityName}
            {context && (
              <div
                style={{
                  fontSize: 22,
                  color: accent,
                  marginTop: 16,
                  fontFamily: "'Inter', sans-serif",
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  fontWeight: 400,
                }}
              >
                {context}
              </div>
            )}
          </div>

          {quote && (
            <div
              style={{
                position: "absolute",
                top: "12%",
                right: "6%",
                maxWidth: "38%",
                opacity: quoteOpacity,
                fontFamily: "'Tiempos Text', 'Crimson Text', Georgia, serif",
                color: "white",
                fontSize: 36,
                lineHeight: 1.3,
                fontStyle: "italic",
                textAlign: "right",
              }}
            >
              "{quote}"
            </div>
          )}
        </>
      );

    case "archival_sepia":
      return (
        <>
          {/* Serif caption like a museum plaque */}
          <div
            style={{
              position: "absolute",
              bottom: "10%",
              left: "50%",
              transform: "translateX(-50%)",
              opacity: nameOpacity,
              textAlign: "center",
              fontFamily: "'Crimson Text', 'Sabon', Georgia, serif",
              color: "#e8d8b8",
              fontSize: 56,
              lineHeight: 1,
              letterSpacing: 1,
            }}
          >
            {celebrityName}
            {context && (
              <div
                style={{
                  fontSize: 22,
                  color: "#c8a24b",
                  marginTop: 12,
                  fontStyle: "italic",
                  letterSpacing: 2,
                }}
              >
                {context}
              </div>
            )}
          </div>

          {quote && (
            <div
              style={{
                position: "absolute",
                top: "12%",
                left: "50%",
                transform: "translateX(-50%)",
                maxWidth: "60%",
                opacity: quoteOpacity,
                textAlign: "center",
                fontFamily: "'Crimson Text', Georgia, serif",
                color: "#e8d8b8",
                fontSize: 32,
                lineHeight: 1.4,
                fontStyle: "italic",
              }}
            >
              "{quote}"
            </div>
          )}
        </>
      );
  }
};

// ---------------------------------------------------------------------------
// Text-only fallback when no cutout PNG is available
// ---------------------------------------------------------------------------

const NoCutoutFallback: React.FC<{
  celebrityName: string;
  treatment: Treatment;
  primaryColor: string;
}> = ({ celebrityName, treatment, primaryColor }) => {
  const isSerif = treatment === "editorial_clean" || treatment === "archival_sepia";
  const fontFamily = isSerif
    ? "'Tiempos Text', 'Crimson Text', Georgia, serif"
    : treatment === "archival_redact"
    ? "'Courier Prime', 'Courier New', monospace"
    : "Anton, sans-serif";

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          textAlign: "center",
          fontFamily,
          color: "white",
          fontSize: 120,
          textTransform: isSerif ? "none" : "uppercase",
          letterSpacing: isSerif ? -1 : 2,
          opacity: 0.5,
        }}
      >
        [ {celebrityName} ]
      </div>
    </div>
  );
};
