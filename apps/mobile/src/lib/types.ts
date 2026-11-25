export type Role = "owner" | "coach" | "athlete";

export type Box = { id: string; name: string; slug: string };
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
