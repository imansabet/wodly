import { Pressable, StyleSheet, Text, View } from "react-native";

import { SCORE_LABELS } from "./labels";
import { formatTime } from "./time";
import type { TrainingSession } from "./types";
import { Button, colors } from "./ui";

type Props = {
  session: TrainingSession;
  timeZone: string;
  busy: boolean;
  onOpen: () => void;
  onToggleBook: () => void;
};

export function SessionCard({
  session: s,
  timeZone,
  busy,
  onOpen,
  onToggleBook,
}: Props) {
  const endMs = new Date(s.starts_at).getTime() + s.duration_minutes * 60_000;
  const over = Date.now() >= endMs;
  const full = s.booked_count >= s.capacity;
  const range = `${formatTime(s.starts_at, timeZone)} – ${formatTime(
    new Date(endMs).toISOString(),
    timeZone,
  )}`;

  return (
    <Pressable
      onPress={onOpen}
      style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]}
    >
      <View style={styles.top}>
        <Text style={styles.time}>{range}</Text>
        <Text style={styles.count}>
          {s.booked_count}/{s.capacity}
        </Text>
      </View>
      <Text style={styles.title}>{s.title ?? "CrossFit"}</Text>
      <Text style={styles.meta}>Coach {s.coach_name ?? "—"}</Text>
      <Text style={s.workout ? styles.wod : styles.wodEmpty}>
        {s.workout
          ? `${s.workout.title} · ${SCORE_LABELS[s.workout.score_type]}`
          : "WOD not posted yet"}
      </Text>

      {s.canceled ? (
        <Text style={styles.badgeDanger}>CANCELED</Text>
      ) : over ? (
        <Text style={styles.badgeMuted}>FINISHED</Text>
      ) : (
        <Button
          label={s.booked_by_me ? "Cancel booking" : full ? "Full" : "Book"}
          onPress={onToggleBook}
          loading={busy}
          disabled={!s.booked_by_me && full}
          variant={s.booked_by_me ? "ghost" : "primary"}
        />
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 18,
    gap: 6,
  },
  top: { flexDirection: "row", justifyContent: "space-between" },
  time: { color: colors.accent, fontSize: 15, fontWeight: "800" },
  count: { color: colors.muted, fontSize: 14, fontWeight: "700" },
  title: { color: colors.text, fontSize: 22, fontWeight: "800" },
  meta: { color: colors.muted, fontSize: 14 },
  wod: { color: colors.text, fontSize: 15, fontWeight: "600", marginBottom: 6 },
  wodEmpty: { color: colors.muted, fontSize: 15, marginBottom: 6 },
  badgeDanger: { color: colors.danger, fontSize: 13, fontWeight: "800", letterSpacing: 1 },
  badgeMuted: { color: colors.muted, fontSize: 13, fontWeight: "800", letterSpacing: 1 },
});
