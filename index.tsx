// remotion/index.tsx
// Entry point for all DopamineStudios mograph compositions
// Runs inside GitHub Actions via: npx remotion render

import { registerRoot } from "remotion";
import { RemotionRoot } from "./Root";

registerRoot(RemotionRoot);
