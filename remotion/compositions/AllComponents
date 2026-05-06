// remotion/compositions/DataGraphRise.tsx
import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, AbsoluteFill } from "remotion";
interface Props { primaryColor: string; backgroundColor: string; intensity: number; label: string; }
export const DataGraphRise: React.FC<Props> = ({ primaryColor, backgroundColor, intensity, label }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const bars = [0.3, 0.5, 0.4, 0.7, 0.6, 0.85, 0.75, 1.0];
  const progress = interpolate(frame, [0, 40], [0, 1], { extrapolateRight: "clamp" });
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor, justifyContent: "center", alignItems: "center", flexDirection: "column" }}>
      <div style={{ opacity, width: "80%", display: "flex", alignItems: "flex-end", gap: 12, height: 400, justifyContent: "center" }}>
        {bars.map((h, i) => {
          const barDelay = i * 3;
          const barProgress = interpolate(frame, [barDelay, barDelay + 25], [0, h], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={i} style={{ flex: 1, height: `${barProgress * 100}%`, backgroundColor: i === bars.length - 1 ? primaryColor : primaryColor + "80", borderRadius: "4px 4px 0 0", transition: "height 0.1s" }} />
          );
        })}
      </div>
      <div style={{ color: primaryColor, fontFamily: "Anton, sans-serif", fontSize: 72, textTransform: "uppercase", letterSpacing: 4, opacity, marginTop: 40 }}>{label}</div>
    </AbsoluteFill>
  );
};

// remotion/compositions/GlitchTransition.tsx
export const GlitchTransition: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const glitchOffset = Math.sin(frame * 15.7) * 20 * intensity;
  const opacity = interpolate(frame, [0, 3, 18, 24], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      <div style={{ position: "absolute", inset: 0, backgroundColor: primaryColor, clipPath: `inset(${30 + glitchOffset}% 0 ${40 - glitchOffset}% 0)`, opacity: 0.8 }} />
      <div style={{ position: "absolute", inset: 0, backgroundColor: "#ff0000", clipPath: `inset(${50 + glitchOffset * 0.5}% 0 ${20 - glitchOffset * 0.3}% 0)`, opacity: 0.3, transform: `translateX(${glitchOffset * 2}px)` }} />
      <div style={{ position: "absolute", inset: 0, backgroundColor: "#00ffff", clipPath: `inset(${20 - glitchOffset}% 0 ${60 + glitchOffset * 0.7}% 0)`, opacity: 0.3, transform: `translateX(${-glitchOffset * 2}px)` }} />
    </AbsoluteFill>
  );
};

// remotion/compositions/CRTTextOverlay.tsx
export const CRTTextOverlay: React.FC<{ text: string; primaryColor: string; backgroundColor: string; intensity: number }> = ({ text, primaryColor, backgroundColor }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const charCount = Math.floor(interpolate(frame, [0, 20], [0, text.length], { extrapolateRight: "clamp" }));
  const displayText = text.slice(0, charCount);
  const opacity = interpolate(frame, [0, 5, durationInFrames - 10, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scanlineOpacity = (Math.sin(frame * 0.5) + 1) * 0.05;
  return (
    <AbsoluteFill style={{ backgroundColor, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", inset: 0, background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,${scanlineOpacity}) 2px, rgba(0,0,0,${scanlineOpacity}) 4px)`, pointerEvents: "none" }} />
      <div style={{ opacity, padding: "0 80px", textAlign: "center" }}>
        <span style={{ fontFamily: "'VT323', 'Share Tech Mono', 'Courier New', monospace", fontSize: 96, color: primaryColor, letterSpacing: 4, textShadow: `0 0 20px ${primaryColor}`, lineHeight: 1.2, textTransform: "uppercase" }}>
          {displayText}
          {charCount < text.length && <span style={{ opacity: Math.sin(frame * 0.5) > 0 ? 1 : 0 }}>_</span>}
        </span>
      </div>
    </AbsoluteFill>
  );
};

// remotion/compositions/FireIgnite.tsx
export const FireIgnite: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flames = Array.from({ length: 12 }, (_, i) => {
    const x = 10 + i * 7.5;
    const height = 30 + Math.sin(frame * 0.3 + i) * 20 * intensity;
    const flameOpacity = 0.6 + Math.sin(frame * 0.5 + i * 0.7) * 0.4;
    return { x, height, opacity: flameOpacity };
  });
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      <svg width="100%" height="100%" viewBox="0 0 100 120">
        {flames.map((f, i) => (
          <ellipse key={i} cx={`${f.x}%`} cy={`${110 - f.height * 0.3}%`} rx="3.5" ry={f.height * 0.4} fill={primaryColor} opacity={f.opacity} />
        ))}
        <text x="50" y="45" textAnchor="middle" fontFamily="Anton, sans-serif" fontSize="14" fill="white" letterSpacing="-0.5" textTransform="uppercase">FIRE</text>
      </svg>
    </AbsoluteFill>
  );
};

// remotion/compositions/ChainsBreak.tsx
export const ChainsBreak: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const breakPoint = 36;
  const separationLeft = frame > breakPoint ? interpolate(frame, [breakPoint, breakPoint + 15], [0, -200 * intensity], { extrapolateRight: "clamp" }) : 0;
  const separationRight = frame > breakPoint ? interpolate(frame, [breakPoint, breakPoint + 15], [0, 200 * intensity], { extrapolateRight: "clamp" }) : 0;
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flashOpacity = frame > breakPoint ? interpolate(frame, [breakPoint, breakPoint + 5], [1, 0], { extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ backgroundColor, opacity, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", inset: 0, backgroundColor: primaryColor, opacity: flashOpacity }} />
      <div style={{ transform: `translateX(${separationLeft}px)`, fontSize: 180, fontFamily: "Anton, sans-serif", color: primaryColor, letterSpacing: -8 }}>⛓</div>
      <div style={{ transform: `translateX(${separationRight}px)`, fontSize: 180, fontFamily: "Anton, sans-serif", color: primaryColor, letterSpacing: -8, position: "absolute" }}>⛓</div>
      {frame > breakPoint + 8 && (
        <div style={{ position: "absolute", bottom: "25%", fontFamily: "Anton, sans-serif", fontSize: 100, color: "white", textTransform: "uppercase", letterSpacing: 6, opacity: interpolate(frame, [breakPoint + 8, breakPoint + 20], [0, 1], { extrapolateRight: "clamp" }) }}>FREE</div>
      )}
    </AbsoluteFill>
  );
};

// remotion/compositions/ClockDissolve.tsx
export const ClockDissolve: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const rotation = interpolate(frame, [0, durationInFrames], [0, 360 * intensity]);
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor, opacity, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", width: 600, height: 600 }}>
        <svg width="600" height="600" viewBox="0 0 600 600">
          <circle cx="300" cy="300" r="280" fill="none" stroke={primaryColor} strokeWidth="6" />
          <line x1="300" y1="300" x2="300" y2="60" stroke={primaryColor} strokeWidth="8" strokeLinecap="round" transform={`rotate(${rotation}, 300, 300)`} />
          <line x1="300" y1="300" x2="300" y2="120" stroke="white" strokeWidth="5" strokeLinecap="round" transform={`rotate(${rotation * 12}, 300, 300)`} />
          {[0,30,60,90,120,150,180,210,240,270,300,330].map(deg => (
            <line key={deg} x1="300" y1="30" x2="300" y2={deg % 90 === 0 ? 60 : 45} stroke={primaryColor} strokeWidth={deg % 90 === 0 ? 4 : 2} transform={`rotate(${deg}, 300, 300)`} />
          ))}
        </svg>
      </div>
      <div style={{ position: "absolute", bottom: "20%", fontFamily: "Anton, sans-serif", fontSize: 80, color: primaryColor, textTransform: "uppercase", letterSpacing: 8 }}>TIME</div>
    </AbsoluteFill>
  );
};

// remotion/compositions/MazeFragment.tsx
export const MazeFragment: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fragments = Array.from({ length: 20 }, (_, i) => ({
    x: (i * 47.3) % 100, y: (i * 31.7) % 100,
    w: 8 + (i % 5) * 4, h: 8 + (i % 3) * 4,
    rot: (i * 17) % 45,
    opacity: 0.2 + (i % 5) * 0.15,
  }));
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      <svg width="100%" height="100%" viewBox="0 0 100 120">
        {fragments.map((f, i) => (
          <rect key={i} x={`${f.x}%`} y={`${f.y}%`} width={f.w} height={f.h} fill="none" stroke={primaryColor} strokeWidth="0.5" opacity={f.opacity} transform={`rotate(${f.rot + frame * 0.2}, ${f.x + f.w / 2}, ${f.y + f.h / 2})`} />
        ))}
        <text x="50" y="55" textAnchor="middle" fontFamily="Anton, sans-serif" fontSize="12" fill="white" letterSpacing="-0.3" textTransform="uppercase">LOST</text>
      </svg>
    </AbsoluteFill>
  );
};

// remotion/compositions/WaterFillScreen.tsx
export const WaterFillScreen: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number }> = ({ primaryColor, backgroundColor, intensity }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const fillLevel = interpolate(frame, [0, durationInFrames * 0.7], [120, 0], { extrapolateRight: "clamp" });
  const waveOffset = Math.sin(frame * 0.2) * 3 * intensity;
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      <svg width="100%" height="100%" viewBox="0 0 100 120" preserveAspectRatio="none">
        <path d={`M0 ${fillLevel + waveOffset} Q25 ${fillLevel - 3 + waveOffset} 50 ${fillLevel + waveOffset} Q75 ${fillLevel + 3 + waveOffset} 100 ${fillLevel + waveOffset} L100 120 L0 120 Z`} fill={primaryColor} opacity={0.7} />
        <path d={`M0 ${fillLevel + 5 - waveOffset} Q25 ${fillLevel + 2 - waveOffset} 50 ${fillLevel + 5 - waveOffset} Q75 ${fillLevel + 8 - waveOffset} 100 ${fillLevel + 5 - waveOffset} L100 120 L0 120 Z`} fill={primaryColor} opacity={0.4} />
        <text x="50" y="40" textAnchor="middle" fontFamily="Anton, sans-serif" fontSize="10" fill="white" opacity={Math.min(1, (120 - fillLevel) / 80)}>DROWNING</text>
      </svg>
    </AbsoluteFill>
  );
};

// remotion/compositions/MapZoom.tsx
export const MapZoom: React.FC<{ primaryColor: string; backgroundColor: string; intensity: number; label: string }> = ({ primaryColor, backgroundColor, intensity, label }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1, 1 + intensity * 0.8], { extrapolateRight: "clamp" });
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const gridLines = Array.from({ length: 10 }, (_, i) => i * 10);
  return (
    <AbsoluteFill style={{ backgroundColor, opacity }}>
      <div style={{ transform: `scale(${scale})`, width: "100%", height: "100%", position: "absolute" }}>
        <svg width="100%" height="100%" viewBox="0 0 100 120">
          {gridLines.map(l => (<>
            <line key={`h${l}`} x1="0" y1={`${l}%`} x2="100%" y2={`${l}%`} stroke={primaryColor} strokeWidth="0.3" opacity="0.3" />
            <line key={`v${l}`} x1={`${l}%`} y1="0" x2={`${l}%`} y2="100%" stroke={primaryColor} strokeWidth="0.3" opacity="0.3" />
          </>))}
          <circle cx="50" cy="50" r="3" fill={primaryColor} opacity="0.9" />
          <circle cx="50" cy="50" r={6 + Math.sin(frame * 0.3) * 2} fill="none" stroke={primaryColor} strokeWidth="0.5" opacity="0.6" />
          <circle cx="50" cy="50" r={10 + Math.sin(frame * 0.3) * 3} fill="none" stroke={primaryColor} strokeWidth="0.3" opacity="0.3" />
        </svg>
      </div>
      <div style={{ position: "absolute", bottom: "20%", width: "100%", textAlign: "center", fontFamily: "Anton, sans-serif", fontSize: 80, color: primaryColor, textTransform: "uppercase", letterSpacing: 8 }}>{label}</div>
    </AbsoluteFill>
  );
};

// remotion/compositions/TVIntro.tsx
export const TVIntro: React.FC<{ channelName: string; primaryColor: string; backgroundColor: string }> = ({ channelName, primaryColor, backgroundColor }) => {
  const frame = useCurrentFrame();
  const staticOpacity = Math.random() * 0.3;
  const textOpacity = interpolate(frame, [20, 50, 120, 140], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const scanline = (frame * 8) % 100;
  return (
    <AbsoluteFill style={{ backgroundColor, justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", inset: 0, background: `repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(255,255,255,0.03) 3px, rgba(255,255,255,0.03) 4px)` }} />
      <div style={{ position: "absolute", top: `${scanline}%`, left: 0, right: 0, height: "2%", backgroundColor: "rgba(255,255,255,0.05)", filter: "blur(2px)" }} />
      <div style={{ textAlign: "center", opacity: textOpacity }}>
        <div style={{ fontFamily: "'Share Tech Mono', 'Courier New', monospace", fontSize: 48, color: primaryColor, letterSpacing: 12, textTransform: "uppercase", marginBottom: 20 }}>[ CHANNEL ]</div>
        <div style={{ fontFamily: "Anton, sans-serif", fontSize: 140, color: "white", textTransform: "uppercase", letterSpacing: -4, lineHeight: 0.9, textShadow: `4px 0 0 #ff000040, -4px 0 0 #00ffff40` }}>{channelName}</div>
        <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: 36, color: primaryColor, letterSpacing: 20, marginTop: 20, opacity: 0.7 }}>EST. 2025</div>
      </div>
    </AbsoluteFill>
  );
};

// remotion/compositions/EndScreen.tsx
export const EndScreen: React.FC<{ channelName: string; primaryColor: string; backgroundColor: string; subscribeText: string }> = ({ channelName, primaryColor, backgroundColor, subscribeText }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pulseScale = 1 + Math.sin(frame * 0.15) * 0.04;
  const opacity = interpolate(frame, [0, 20, durationInFrames - 20, durationInFrames], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ backgroundColor, justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 60, opacity }}>
      <div style={{ fontFamily: "Anton, sans-serif", fontSize: 120, color: "white", textTransform: "uppercase", letterSpacing: -3 }}>{channelName}</div>
      <div style={{ transform: `scale(${pulseScale})`, backgroundColor: primaryColor, borderRadius: 8, padding: "40px 80px" }}>
        <div style={{ fontFamily: "Anton, sans-serif", fontSize: 90, color: backgroundColor, textTransform: "uppercase", letterSpacing: 4 }}>{subscribeText}</div>
      </div>
      <div style={{ fontFamily: "Anton, sans-serif", fontSize: 60, color: primaryColor, opacity: 0.7, textTransform: "uppercase", letterSpacing: 8 }}>NEW VIDEOS WEEKLY</div>
    </AbsoluteFill>
  );
};
