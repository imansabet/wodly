export type Role = "owner" | "coach" | "athlete";

export type Box = { id: string; name: string; slug: string; timezone: string };
export type Membership = { box: Box; role: Role };
export type Me = { id: string; phone: string; full_name: string | null };

export type Invite = {
  code: string;
  role: Role;
  label: string | null;
  expires_at: string;
  max_uses: number;
  uses: number;
};

export type Member = {
  user_id: string;
  full_name: string | null;
  phone: string;
  role: Role;
};

export type ScoreType =
  | "for_time"
  | "amrap"
  | "max_load"
  | "max_reps"
  | "calories"
  | "not_scored";

export type Workout = {
  id: string;
  title: string;
  description: string;
  score_type: ScoreType;
  time_cap_seconds: number | null;
};

export type TrainingSession = {
  id: string;
  title: string | null;
  starts_at: string;
  duration_minutes: number;
  capacity: number;
  booked_count: number;
  booked_by_me: boolean;
  canceled: boolean;
  coach_id: string;
  coach_name: string | null;
  workout: Workout | null;
};

export type Attendee = {
  user_id: string;
  full_name: string | null;
  phone: string;
};
