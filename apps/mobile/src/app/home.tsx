import {
  useFocusEffect,
  useLocalSearchParams,
  useRouter,
} from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { api, errorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ScrollScreen } from "../lib/scroll-screen";
import { SessionCard } from "../lib/session-card";
import { addDays, formatDay, todayIn } from "../lib/time";
import type { TrainingSession } from "../lib/types";
import { Button, ErrorText, Subtitle, colors } from "../lib/ui";

export default function Home() {
  const router = useRouter();
  const { date } = useLocalSearchParams<{ date?: string }>();
  const { me, memberships, signOut } = useAuth();
  const active = memberships[0];
  const box = active.box;
  const canManage = active.role !== "athlete";
  const today = todayIn(box.timezone);

  const [day, setDay] = useState(date ?? today);
  const [sessions, setSessions] = useState<TrainingSession[] | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (date) setDay(date);
  }, [date]);

  useFocusEffect(
    useCallback(() => {
      let current = true;
      setError(null);
      api<TrainingSession[]>(`/boxes/${box.id}/sessions?date=${day}`)
        .then((data) => current && setSessions(data))
        .catch((e) => current && setError(errorMessage(e)));
      return () => {
        current = false;
      };
    }, [box.id, day]),
  );

  function go(day_: string) {
    setSessions(null);
    setDay(day_);
  }

  async function toggleBook(s: TrainingSession) {
    setBusyId(s.id);
    setError(null);
    try {
      const updated = await api<TrainingSession>(
        `/boxes/${box.id}/sessions/${s.id}/book`,
        { method: s.booked_by_me ? "DELETE" : "POST" },
      );
      setSessions((list) =>
        list ? list.map((x) => (x.id === updated.id ? updated : x)) : list,
      );
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <ScrollScreen>
      <Subtitle>Welcome{me?.full_name ? `, ${me.full_name}` : ""}</Subtitle>
      <Text style={styles.boxName}>{box.name}</Text>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{active.role.toUpperCase()}</Text>
      </View>

      <View style={styles.dayRow}>
        <Pressable onPress={() => go(addDays(day, -1))} hitSlop={14}>
          <Text style={styles.arrow}>‹</Text>
        </Pressable>
        <Pressable onPress={() => go(today)}>
          <Text style={styles.dayLabel}>{formatDay(day, today)}</Text>
        </Pressable>
        <Pressable onPress={() => go(addDays(day, 1))} hitSlop={14}>
          <Text style={styles.arrow}>›</Text>
        </Pressable>
      </View>

      <ErrorText message={error} />
      {sessions === null && !error ? (
        <ActivityIndicator color={colors.accent} />
      ) : null}
      {sessions?.length === 0 ? <Subtitle>No sessions this day.</Subtitle> : null}
      {sessions?.map((s) => (
        <SessionCard
          key={s.id}
          session={s}
          timeZone={box.timezone}
          busy={busyId === s.id}
          onOpen={() =>
            router.push({ pathname: "/session/[id]", params: { id: s.id } })
          }
          onToggleBook={() => toggleBook(s)}
        />
      ))}

      {canManage ? (
        <>
          <Button label="New session" onPress={() => router.push("/new-session")} />
          <Button label="Members" variant="ghost" onPress={() => router.push("/members")} />
          <Button label="Invite someone" variant="ghost" onPress={() => router.push("/invite")} />
        </>
      ) : null}
      <Button label="Sign out" variant="ghost" onPress={signOut} />
    </ScrollScreen>
  );
}

const styles = StyleSheet.create({
  boxName: { color: colors.text, fontSize: 38, fontWeight: "800" },
  badge: {
    alignSelf: "flex-start",
    backgroundColor: colors.accent,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  badgeText: { color: colors.text, fontSize: 12, fontWeight: "800", letterSpacing: 1 },
  dayRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 12,
  },
  arrow: { color: colors.text, fontSize: 34, paddingHorizontal: 12 },
  dayLabel: { color: colors.text, fontSize: 20, fontWeight: "800" },
});
