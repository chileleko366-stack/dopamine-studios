import React from "react";
import { Composition } from "remotion";

import { KineticQuote } from "./compositions/KineticQuote";
import { ParticlesAscending } from "./compositions/ParticlesAscending";
import { CelebrityCard } from "./compositions/CelebrityCard";

// AllComponents.tsx is a barrel that exports the remaining 10 compositions.
// This is intentional: keeping them in one file reduces clutter and makes it
// easy to compare/share visual logic across channels.
import {
  DataGraphRise,
  GlitchTransition,
  CRTTextOverlay,
  FireIgnite,
  ChainsBreak,
  ClockDissolve,
  MazeFragment,
  WaterFillScreen,
  MapZoom,
  TVIntro,
  EndScreen,
} from "./compositions/AllComponents";

// Default dimensions: 1920x1080 horizontal for long-form mograph clips.
// Vertical Shorts use 1080x1920 -- compositions handle both via CSS percentages.
const W = 1920;
const H = 1080;
const FPS = 30;
const DEFAULT_DURATION = 72; // 2.4 seconds at 30fps

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="kinetic_quote"
        component={KineticQuote}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          text: "OBSESSION",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.7,
        }}
      />

      <Composition
        id="particles_ascending"
        component={ParticlesAscending}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.7,
        }}
      />

      <Composition
        id="data_graph_rise"
        component={DataGraphRise}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.7,
          label: "RISE",
        }}
      />

      <Composition
        id="glitch_transition"
        component={GlitchTransition}
        durationInFrames={24}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.8,
        }}
      />

      <Composition
        id="crt_text_overlay"
        component={CRTTextOverlay}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          text: "REDACTED",
          primaryColor: "#ff3333",
          backgroundColor: "#0d0d0d",
          intensity: 0.7,
        }}
      />

      <Composition
        id="fire_ignite"
        component={FireIgnite}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#ff8c00",
          backgroundColor: "#0a0a0a",
          intensity: 0.8,
        }}
      />

      <Composition
        id="chains_break"
        component={ChainsBreak}
        durationInFrames={90}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 1.0,
        }}
      />

      <Composition
        id="clock_dissolve"
        component={ClockDissolve}
        durationInFrames={120}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.5,
        }}
      />

      <Composition
        id="maze_fragment"
        component={MazeFragment}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.6,
        }}
      />

      <Composition
        id="water_fill_screen"
        component={WaterFillScreen}
        durationInFrames={120}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#00d4aa",
          backgroundColor: "#0a0a1a",
          intensity: 0.7,
        }}
      />

      <Composition
        id="map_zoom"
        component={MapZoom}
        durationInFrames={DEFAULT_DURATION}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          primaryColor: "#c8a24b",
          backgroundColor: "#1a1008",
          intensity: 0.6,
          label: "PLACE",
        }}
      />

      <Composition
        id="tv_intro"
        component={TVIntro}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          channelName: "DOPAMINE",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
        }}
      />

      <Composition
        id="end_screen"
        component={EndScreen}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          channelName: "DOPAMINE",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          subscribeText: "SUBSCRIBE",
        }}
      />

      <Composition
        id="celebrity_card"
        component={CelebrityCard}
        durationInFrames={150}
        fps={FPS}
        width={W}
        height={H}
        defaultProps={{
          celebrityName: "STEVE JOBS",
          cutoutUrl: undefined,
          treatment: "cinematic_dark",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          context: "1955-2011",
          quote: "",
          intensity: 0.6,
        }}
      />
    </>
  );
};
