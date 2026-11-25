import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { api, errorMessage } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { SCORE_LABELS } from "../../lib/labels";
import { ScrollScreen } from "../../lib/scroll-screen";
import { dayOf, formatDay, formatTime, todayIn } from "../../lib/time";
import type { Attendee, TrainingSession } from "../../lib/types";
import { Button, ErrorText, Subtitle, Title, colors } from "../../lib/ui";

export default function SessionDetail() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { me, memberships } = useAuth();
  const active = memberships[0];
  const box = active.box;
  const isStaff = active.role !== "athlete";

  const [s, setS] = useState<TrainingSession | null>(null);
  const [attendees, setAttendees] = useState<Attendee[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<TrainingSession>(`/boxes/${box.id}/sessions/${id}`)
      .then(setS)
      .catch((e) => setError(errorMessage(e)));
  }, [box.id, id]);

  const bookedCount = s?.booked_count;
  useEffect(() => {
    if (!isStaff) return;
    api<Attendee[]>(`/boxes/${box.id}/sessions/${id}/attendees`)
      .then(setAttendees)
      .catch((e) => setError(errorMessage(e)));
  }, [box.id, id, isStaff, bookedCount]);

  async function run(request: () => Promise<TrainingSession>) {
    setBusy(true);
    setError(null);
    try {
      setS(await request());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  if (!s) {
    return (
      <ScrollScreen>
        <ErrorText message={error} />
        {error ? null : <ActivityIndicator color={colors.accent} />}
        <Button label="Back" variant="ghost" onPress={() => router.back()} />
      </ScrollScreen>
    );
  }

  const endMs = new Date(s.starts_at).getTime() + s.duration_minutes * 60_000;
  const over = Date.now() >= endMs;
  const full = s.booked_count >= s.capacity;
  const canManage = isStaff && (active.role === "owner" || s.coach_id === me?.id);
  const when = `${formatDay(dayOf(s.starts_at, box.timezone), todayIn(box.timezone))} · ${formatTime(
    s.starts_at,
    box.timezone,
  )} – ${formatTime(new Date(endMs).toISOString(), box.timezone)}`;

  return (
    <ScrollScreen>
      <Subtitle>{when}</Subtitle>
      <Title>{s.title ?? "CrossFit"}</Title>
      <Subtitle>
        Coach {s.coach_name ?? "—"} · {s.booked_count}/{s.capacity} booked
      </Subtitle>
      {s.canceled ? <Text style={styles.canceled}>THIS SESSION IS CANCELED</Text> : null}

      {s.workout ? (
        <View style={styles.wod}>
          <Text style={styles.wodTitle}>{s.workout.title}</Text>
          <Text style={styles.wodMeta}>
            {SCORE_LABELS[s.workout.score_type]}
            {s.workout.time_cap_seconds
              ? ` · cap ${Math.round(s.workout.time_cap_seconds / 60)} min`
              : ""}
          </Text>
          <Text style={styles.wodText} selectable>
            {s.workout.description}
          </Text>
        </View>
      ) : (
        <Subtitle>WOD not posted yet.</Subtitle>
      )}

      <ErrorText message={error} />

      {!s.canceled && !over ? (
        <Button
          label={s.booked_by_me ? "Cancel booking" : full ? "Full" : "Book"}
          loading={busy}
          disabled={!s.booked_by_me && full}
          variant={s.booked_by_me ? "ghost" : "primary"}
          onPress={() =>
            run(() =>
              api<TrainingSession>(`/boxes/${box.id}/sessions/${s.id}/book`, {
                method: s.booked_by_me ? "DELETE" : "POST",
              }),
            )
          }
        />
      ) : null}

      {isStaff ? (
        <View style={{ gap: 8 }}>
          <Text style={styles.section}>Attendees</Text>
          {attendees === null ? <ActivityIndicator color={colors.accent} /> : null}
          {attendees?.length === 0 ? <Subtitle>Nobody booked yet.</Subtitle> : null}
          {attendees?.map((a) => (
            <View key={a.user_id} style={styles.attendee}>
              <Text style={styles.attendeeName}>{a.full_name ?? "No name yet"}</Text>
              <Text style={styles.attendeePhone}>{a.phone}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {canManage ? (
        <Button
          label={s.canceled ? "Restore session" : "Cancel session"}
          variant="ghost"
          loading={busy}
          onPress={() =>
            run(() =>
              api<TrainingSession>(`/boxes/${box.id}/sessions/${s.id}`, {
                method: "PATCH",
                body: { canceled: !s.canceled },
              }),
            )
          }
        />
      ) : null}
      <Button label="Back" variant="ghost" onPress={() => router.back()} />
    </ScrollScreen>
  );
}

const styles = StyleSheet.create({
  canceled: { color: colors.danger, fontSize: 14, fontWeight: "800", letterSpacing: 1 },
  wod: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 20,
    gap: 8,
  },
  wodTitle: { color: colors.text, fontSize: 24, fontWeight: "800" },
  wodMeta: { color: colors.accent, fontSize: 13, fontWeight: "800", letterSpacing: 0.5 },
  wodText: { color: colors.text, fontSize: 17, lineHeight: 26 },
  section: { color: colors.text, fontSize: 18, fontWeight: "700", marginTop: 8 },
  attendee: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
  },
  attendeeName: { color: colors.text, fontSize: 16, fontWeight: "600" },
  attendeePhone: { color: colors.muted, fontSize: 14 },
});
