// remotion/compositions/KineticQuote.tsx
// Bold text slams in, holds, fades out
// Used for emphasis overlays and as fallback for all channels

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  AbsoluteFill,
} from "remotion";

interface Props {
  text: string;
  primaryColor: string;
  backgroundColor: string;
  intensity: number;
}

export const KineticQuote: React.FC<Props> = ({
  text,
  primaryColor,
  backgroundColor,
  intensity,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Slam entrance: spring from 0 to 1 in first 8 frames
  const scaleSpring = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 200,
      mass: 0.5,
    },
  });

  const scale = interpolate(scaleSpring, [0, 1], [0, 1]);

  // Slight overshoot effect
  const overshootScale = frame < 10
    ? interpolate(frame, [0, 5, 8], [0, 1.15, 1.0], { extrapolateRight: "clamp" })
    : 1.0;

  // Fade out last 12 frames
  const opacity = interpolate(
    frame,
    [0, 4, durationInFrames - 12, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Word-by-word stagger for multi-word text
  const words = text.split(" ");

  // Accent bar pulse
  const barWidth = interpolate(frame, [0, 8, 20], [0, 100, 90], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      {/* Accent bar top */}
      <div
        style={{
          position: "absolute",
          top: 80,
          left: "50%",
          transform: "translateX(-50%)",
          width: `${barWidth}%`,
          height: 4,
          backgroundColor: primaryColor,
          opacity,
        }}
      />

      {/* Main text */}
      <div
        style={{
          transform: `scale(${overshootScale})`,
          opacity,
          padding: "0 60px",
          textAlign: "center",
        }}
      >
        {words.map((word, i) => {
          const wordDelay = i * 3;
          const wordOpacity = interpolate(
            frame,
            [wordDelay, wordDelay + 6, durationInFrames - 12, durationInFrames],
            [0, 1, 1, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );
          const wordY = interpolate(
            frame,
            [wordDelay, wordDelay + 8],
            [30, 0],
            { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
          );

          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                fontFamily: "Anton, Impact, sans-serif",
                fontSize: words.length > 4 ? 110 : 140,
                fontWeight: 900,
                color: "#ffffff",
                lineHeight: 1.05,
                letterSpacing: "-0.02em",
                textTransform: "uppercase",
                opacity: wordOpacity,
                transform: `translateY(${wordY}px)`,
                marginRight: "0.15em",
              }}
            >
              {/* Accent word highlight */}
              {i === words.length - 1 ? (
                <span style={{ color: primaryColor }}>{word}</span>
              ) : (
                word
              )}
            </span>
          );
        })}
      </div>

      {/* Accent bar bottom */}
      <div
        style={{
          position: "absolute",
          bottom: 80,
          left: "50%",
          transform: "translateX(-50%)",
          width: `${barWidth * 0.6}%`,
          height: 4,
          backgroundColor: primaryColor,
          opacity,
        }}
      />
    </AbsoluteFill>
  );
};
