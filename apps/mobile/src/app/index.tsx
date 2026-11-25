import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useAuth } from "../lib/auth";
import type { Role } from "../lib/types";
import { Screen, Subtitle, Title, colors } from "../lib/ui";

const ROLES: { role: Role; title: string; hint: string }[] = [
  { role: "owner", title: "I own a box", hint: "Create your box and invite your team" },
  { role: "coach", title: "I'm a coach", hint: "Join your box with an invite code" },
  { role: "athlete", title: "I'm an athlete", hint: "Join your box and track your progress" },
];

export default function Welcome() {
  const router = useRouter();
  const { setPendingRole } = useAuth();

  return (
    <Screen>
      <Title>Wodly</Title>
      <Subtitle>Who are you?</Subtitle>
      <View style={styles.list}>
        {ROLES.map(({ role, title, hint }) => (
          <Pressable
            key={role}
            style={({ pressed }) => [styles.card, pressed && { opacity: 0.7 }]}
            onPress={() => {
              setPendingRole(role);
              router.push("/phone");
            }}
          >
            <Text style={styles.cardTitle}>{title}</Text>
            <Text style={styles.cardHint}>{hint}</Text>
          </Pressable>
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { gap: 12, marginTop: 8 },
  card: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    padding: 20,
    gap: 4,
  },
  cardTitle: { color: colors.text, fontSize: 20, fontWeight: "700" },
  cardHint: { color: colors.muted, fontSize: 14 },
});
