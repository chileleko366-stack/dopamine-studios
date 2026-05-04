// remotion/compositions/ParticlesAscending.tsx
import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";

interface Props { primaryColor: string; backgroundColor: string; intensity: number; }

export const ParticlesAscending: React.FC<Props> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const particles = Array.from({ length: Math.floor(30 * intensity) }, (_, i) => {
    const seed = i * 137.508;
    const x = (seed % 100);
    const startY = 110 + (seed % 20);
    const speed = 0.3 + (i % 5) * 0.15 * intensity;
    const size = 4 + (i % 8);
    const delay = (i * 2) % 20;
    const opacity = interpolate(
      frame,
      [delay, delay + 10, durationInFrames - 10, durationInFrames],
      [0, 0.8, 0.8, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
    const y = startY - (frame - delay) * speed * 1.2;

    return { x, y, size, opacity, key: i };
  });

  const mainOpacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor }}>
      <svg width="100%" height="100%" viewBox="0 0 100 120" preserveAspectRatio="none">
        {particles.map(p => (
          <circle key={p.key} cx={`${p.x}%`} cy={`${p.y}%`} r={p.size * 0.3} fill={primaryColor} opacity={p.opacity} />
        ))}
        <text x="50" y="55" textAnchor="middle" dominantBaseline="middle"
          fontFamily="Anton, sans-serif" fontSize="12" fill="white" opacity={mainOpacity}
          textDecoration="uppercase" letterSpacing="-0.5">
          RISING
        </text>
      </svg>
    </AbsoluteFill>
  );
};
