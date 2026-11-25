import { useRouter } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "../lib/auth";
import { Button, Screen, Subtitle, colors } from "../lib/ui";

export default function Home() {
  const router = useRouter();
  const { me, memberships, signOut } = useAuth();
  const active = memberships[0];
  const canManage = active.role !== "athlete";

  return (
    <Screen>
      <Subtitle>Welcome{me?.full_name ? `, ${me.full_name}` : ""}</Subtitle>
      <Text style={styles.boxName}>{active.box.name}</Text>
      <View style={styles.badge}>
        <Text style={styles.badgeText}>{active.role.toUpperCase()}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Today's WOD</Text>
        <Text style={styles.cardHint}>Coming soon</Text>
      </View>

      {canManage ? (
        <>
          <Button label="Members" onPress={() => router.push("/members")} />
          <Button label="Invite someone" onPress={() => router.push("/invite")} />
        </>
      ) : null}

      <Button label="Sign out" variant="ghost" onPress={signOut} />
    </Screen>
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
  card: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 20,
    gap: 4,
    marginTop: 16,
  },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "700" },
  cardHint: { color: colors.muted, fontSize: 14 },
});
