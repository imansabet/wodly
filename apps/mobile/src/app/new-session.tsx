import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { api, errorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Chip, Label, Stepper } from "../lib/form";
import { SCORE_LABELS, SCORE_TYPES } from "../lib/labels";
import { ScrollScreen } from "../lib/scroll-screen";
import { addDays, formatDay, todayIn, zonedToIso } from "../lib/time";
import type { ScoreType, Workout } from "../lib/types";
import { Button, ErrorText, Input, Subtitle, Title, colors } from "../lib/ui";

type WodMode = "new" | "existing" | "none";

const pad = (n: number) => String(n).padStart(2, "0");
const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n));

export default function NewSession() {
  const router = useRouter();
  const { memberships } = useAuth();
  const box = memberships[0].box;
  const today = todayIn(box.timezone);

  const [title, setTitle] = useState("");
  const [day, setDay] = useState(today);
  const [hour, setHour] = useState(6);
  const [minute, setMinute] = useState(0);
  const [duration, setDuration] = useState(60);
  const [capacity, setCapacity] = useState(20);

  const [mode, setMode] = useState<WodMode>("new");
  const [wodTitle, setWodTitle] = useState("");
  const [wodText, setWodText] = useState("");
  const [scoreType, setScoreType] = useState<ScoreType>("for_time");
  const [capMinutes, setCapMinutes] = useState("");
  const [recent, setRecent] = useState<Workout[] | null>(null);
  const [picked, setPicked] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "existing" || recent !== null) return;
    api<Workout[]>(`/boxes/${box.id}/workouts`)
      .then(setRecent)
      .catch((e) => setError(errorMessage(e)));
  }, [mode, recent, box.id]);

  const days = Array.from({ length: 14 }, (_, i) => addDays(today, i));
  const capSeconds = capMinutes ? Number(capMinutes) * 60 : null;
  const capValid = capSeconds === null || (capSeconds >= 60 && capSeconds <= 7200);
  const wodValid =
    mode === "none" ||
    (mode === "existing" && picked !== null) ||
    (mode === "new" &&
      wodTitle.trim().length >= 2 &&
      wodText.trim().length > 0 &&
      capValid);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        title: title.trim() || null,
        starts_at: zonedToIso(day, hour, minute, box.timezone),
        duration_minutes: duration,
        capacity,
      };
      if (mode === "new") {
        body.workout = {
          title: wodTitle.trim(),
          description: wodText.trim(),
          score_type: scoreType,
          time_cap_seconds: capSeconds,
        };
      } else if (mode === "existing") {
        body.workout_id = picked;
      }
      await api(`/boxes/${box.id}/sessions`, { method: "POST", body });
      router.dismissTo({ pathname: "/home", params: { date: day } });
    } catch (e) {
      setError(errorMessage(e));
      setLoading(false);
    }
  }

  return (
    <ScrollScreen>
      <Title>New session</Title>
      <Subtitle>Times are in the box timezone ({box.timezone}).</Subtitle>

      <Input
        value={title}
        onChangeText={setTitle}
        placeholder="Name (optional), e.g. 6 AM class"
        maxLength={120}
      />

      <Label>DAY</Label>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
        {days.map((d) => (
          <Chip key={d} label={formatDay(d, today)} selected={d === day} onPress={() => setDay(d)} />
        ))}
      </ScrollView>

      <Label>TIME</Label>
      <Stepper label="Hour" display={pad(hour)} onStep={(dir) => setHour((h) => (h + dir + 24) % 24)} />
      <Stepper label="Minute" display={pad(minute)} onStep={(dir) => setMinute((m) => (m + dir * 5 + 60) % 60)} />
      <Stepper
        label="Duration"
        display={`${duration} min`}
        onStep={(dir) => setDuration((v) => clamp(v + dir * 15, 15, 240))}
      />
      <Stepper
        label="Capacity"
        display={String(capacity)}
        onStep={(dir) => setCapacity((v) => clamp(v + dir, 1, 200))}
      />

      <Label>WOD</Label>
      <View style={styles.row}>
        <Chip label="Write new" selected={mode === "new"} onPress={() => setMode("new")} />
        <Chip label="Use existing" selected={mode === "existing"} onPress={() => setMode("existing")} />
        <Chip label="Later" selected={mode === "none"} onPress={() => setMode("none")} />
      </View>

      {mode === "new" ? (
        <>
          <Input value={wodTitle} onChangeText={setWodTitle} placeholder="WOD title, e.g. Fran" maxLength={120} />
          <Input
            value={wodText}
            onChangeText={setWodText}
            placeholder={"21-15-9\nThrusters (43 kg)\nPull-ups"}
            multiline
            autoCorrect
            style={{ minHeight: 150, textAlignVertical: "top" }}
          />
          <View style={styles.rowWrap}>
            {SCORE_TYPES.map((t) => (
              <Chip key={t} label={SCORE_LABELS[t]} selected={scoreType === t} onPress={() => setScoreType(t)} />
            ))}
          </View>
          <Input
            value={capMinutes}
            onChangeText={(t) => setCapMinutes(t.replace(/\D/g, "").slice(0, 3))}
            placeholder="Time cap in minutes (optional)"
            keyboardType="number-pad"
          />
          {!capValid ? <ErrorText message="Time cap must be between 1 and 120 minutes." /> : null}
        </>
      ) : null}

      {mode === "existing" ? (
        <View style={{ gap: 8 }}>
          {recent?.length === 0 ? <Subtitle>No WODs yet. Write a new one first.</Subtitle> : null}
          {recent?.map((w) => (
            <Pressable
              key={w.id}
              onPress={() => setPicked(w.id)}
              style={[styles.pick, picked === w.id && styles.pickSelected]}
            >
              <Text style={styles.pickTitle}>{w.title}</Text>
              <Text style={styles.pickMeta} numberOfLines={2}>
                {SCORE_LABELS[w.score_type]} · {w.description}
              </Text>
            </Pressable>
          ))}
        </View>
      ) : null}

      <ErrorText message={error} />
      <Button label="Create session" onPress={submit} loading={loading} disabled={!wodValid} />
      <Button label="Cancel" variant="ghost" onPress={() => router.back()} />
    </ScrollScreen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  rowWrap: { flexDirection: "row", gap: 8, flexWrap: "wrap" },
  pick: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    padding: 14,
    gap: 4,
  },
  pickSelected: { borderColor: colors.accent },
  pickTitle: { color: colors.text, fontSize: 16, fontWeight: "700" },
  pickMeta: { color: colors.muted, fontSize: 13 },
});
