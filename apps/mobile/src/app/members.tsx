import { useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { api, errorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ScrollScreen } from "../lib/scroll-screen";
import type { Member } from "../lib/types";
import { Button, ErrorText, Subtitle, Title, colors } from "../lib/ui";

export default function Members() {
  const router = useRouter();
  const { memberships } = useAuth();
  const active = memberships[0];
  const [members, setMembers] = useState<Member[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Member[]>(`/boxes/${active.box.id}/members`)
      .then(setMembers)
      .catch((e) => setError(errorMessage(e)));
  }, [active.box.id]);

  return (
    <ScrollScreen>
      <Title>Members</Title>
      <Subtitle>
        {active.box.name}
        {members ? ` · ${members.length}` : ""}
      </Subtitle>
      <ErrorText message={error} />
      {members === null && !error ? <ActivityIndicator color={colors.accent} /> : null}
      {members?.map((m) => (
        <View key={m.user_id} style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.name}>{m.full_name ?? "No name yet"}</Text>
            <Text style={styles.phone}>{m.phone}</Text>
          </View>
          <Text style={styles.role}>{m.role.toUpperCase()}</Text>
        </View>
      ))}
      <Button label="Back" variant="ghost" onPress={() => router.back()} />
    </ScrollScreen>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: 16,
  },
  name: { color: colors.text, fontSize: 17, fontWeight: "700" },
  phone: { color: colors.muted, fontSize: 14, marginTop: 2 },
  role: { color: colors.accent, fontSize: 12, fontWeight: "800", letterSpacing: 1 },
});
