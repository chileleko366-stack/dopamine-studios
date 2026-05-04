// remotion/Root.tsx
// Registers every mograph composition for all 5 channels

import React from "react";
import { Composition } from "remotion";

import { KineticQuote } from "./compositions/KineticQuote";
import { ParticlesAscending } from "./compositions/ParticlesAscending";
import { DataGraphRise } from "./compositions/DataGraphRise";
import { GlitchTransition } from "./compositions/GlitchTransition";
import { CRTTextOverlay } from "./compositions/CRTTextOverlay";
import { FireIgnite } from "./compositions/FireIgnite";
import { ChainsBreak } from "./compositions/ChainsBreak";
import { ClockDissolve } from "./compositions/ClockDissolve";
import { MazeFragment } from "./compositions/MazeFragment";
import { WaterFillScreen } from "./compositions/WaterFillScreen";
import { MapZoom } from "./compositions/MapZoom";
import { TVIntro } from "./compositions/TVIntro";
import { EndScreen } from "./compositions/EndScreen";

// All compositions are 1080x1920 (vertical) at 24fps
// Duration: 72 frames = 3 seconds (except TVIntro and EndScreen)

const BASE_PROPS = {
  fps: 24,
  width: 1080,
  height: 1920,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="kinetic_quote"
        component={KineticQuote}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          text: "PLACEHOLDER TEXT",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.6,
        }}
      />
      <Composition
        id="particles_ascending"
        component={ParticlesAscending}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.6,
        }}
      />
      <Composition
        id="data_graph_rise"
        component={DataGraphRise}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#00d4aa",
          backgroundColor: "#0d1117",
          intensity: 0.6,
          label: "GROWTH",
        }}
      />
      <Composition
        id="glitch_transition"
        component={GlitchTransition}
        durationInFrames={24}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 1.0,
        }}
      />
      <Composition
        id="crt_text_overlay"
        component={CRTTextOverlay}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          text: "PLACEHOLDER",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.6,
        }}
      />
      <Composition
        id="fire_ignite"
        component={FireIgnite}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#ff4400",
          backgroundColor: "#0a0a0a",
          intensity: 0.8,
        }}
      />
      <Composition
        id="chains_break"
        component={ChainsBreak}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          intensity: 0.7,
        }}
      />
      <Composition
        id="clock_dissolve"
        component={ClockDissolve}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#c8a24b",
          backgroundColor: "#1a1008",
          intensity: 0.5,
        }}
      />
      <Composition
        id="maze_fragment"
        component={MazeFragment}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#7b61ff",
          backgroundColor: "#0a0a1a",
          intensity: 0.5,
        }}
      />
      <Composition
        id="water_fill_screen"
        component={WaterFillScreen}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#0066ff",
          backgroundColor: "#0a0a1a",
          intensity: 0.6,
        }}
      />
      <Composition
        id="map_zoom"
        component={MapZoom}
        durationInFrames={72}
        {...BASE_PROPS}
        defaultProps={{
          primaryColor: "#c8a24b",
          backgroundColor: "#1a1008",
          intensity: 0.5,
          label: "LOCATION",
        }}
      />
      <Composition
        id="tv_intro"
        component={TVIntro}
        durationInFrames={144}
        {...BASE_PROPS}
        defaultProps={{
          channelName: "DOPAMINE LOOP",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
        }}
      />
      <Composition
        id="end_screen"
        component={EndScreen}
        durationInFrames={192}
        {...BASE_PROPS}
        defaultProps={{
          channelName: "DOPAMINE LOOP",
          primaryColor: "#e8ff47",
          backgroundColor: "#0a0a0a",
          subscribeText: "SUBSCRIBE",
        }}
      />
    </>
  );
};
