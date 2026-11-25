import type { ScoreType } from "./types";

export const SCORE_LABELS: Record<ScoreType, string> = {
  for_time: "For time",
  amrap: "AMRAP",
  max_load: "Max load",
  max_reps: "Max reps",
  calories: "Calories",
  not_scored: "Not scored",
};

export const SCORE_TYPES = Object.keys(SCORE_LABELS) as ScoreType[];
