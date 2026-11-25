import { useRouter } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { Pressable, Share, StyleSheet, Text, View } from "react-native";

import { api, errorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { ScrollScreen } from "../lib/scroll-screen";
import type { Invite, Role } from "../lib/types";
import { Button, ErrorText, Input, Subtitle, Title, colors } from "../lib/ui";

function Chip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected && styles.chipSelected]}
    >
      <Text style={[styles.chipText, selected && { color: colors.text }]}>
        {label}
      </Text>
    </Pressable>
  );
}

export default function InviteScreen() {
  const router = useRouter();
  const { memberships } = useAuth();
  const active = memberships[0];
  const boxId = active.box.id;
  const isOwner = active.role === "owner";

  const [role, setRole] = useState<Role>("athlete");
  const [label, setLabel] = useState("");
  const [invites, setInvites] = useState<Invite[]>([]);
  const [created, setCreated] = useState<Invite | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setInvites(await api<Invite[]>(`/boxes/${boxId}/invites`));
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [boxId]);

  useEffect(() => {
    load();
  }, [load]);

  async function create() {
    setError(null);
    setLoading(true);
    try {
      const invite = await api<Invite>(`/boxes/${boxId}/invites`, {
        method: "POST",
        body: { role, label: label.trim() || null },
      });
      setCreated(invite);
      setLabel("");
      await load();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  async function share(invite: Invite) {
    try {
      await Share.share({
        message: `Join ${active.box.name} on Wodly. Invite code: ${invite.code}`,
      });
    } catch {
      // user dismissed the share sheet, or sharing is unavailable
    }
  }

  async function revoke(code: string) {
    setError(null);
    try {
      await api(`/boxes/${boxId}/invites/${code}`, { method: "DELETE" });
      if (created?.code === code) setCreated(null);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  return (
    <ScrollScreen>
      <Title>Invite</Title>
      <Subtitle>Create a code for someone to join {active.box.name}.</Subtitle>

      <View style={styles.chips}>
        <Chip label="Athlete" selected={role === "athlete"} onPress={() => setRole("athlete")} />
        {isOwner ? (
          <Chip label="Coach" selected={role === "coach"} onPress={() => setRole("coach")} />
        ) : null}
      </View>
      <Input
        value={label}
        onChangeText={setLabel}
        placeholder="Name (optional, only you see it)"
        maxLength={80}
      />
      <ErrorText message={error} />
      <Button label="Create invite" onPress={create} loading={loading} />

      {created ? (
        <View style={styles.created}>
          <Text style={styles.createdHint}>
            {created.label ? `For ${created.label} · ` : ""}
            {created.role.toUpperCase()}
          </Text>
          <Text style={styles.code} selectable>
            {created.code}
          </Text>
          <Button label="Share code" onPress={() => share(created)} />
        </View>
      ) : null}

      <Text style={styles.section}>Active invites</Text>
      {invites.length === 0 ? <Subtitle>No active invites.</Subtitle> : null}
      {invites.map((invite) => (
        <View key={invite.code} style={styles.row}>
          <View style={{ flex: 1 }}>
            <Text style={styles.rowTitle}>{invite.label ?? "No name"}</Text>
            <Text style={styles.rowMeta}>
              {invite.code} · {invite.role} · used {invite.uses}/{invite.max_uses} · until{" "}
              {new Date(invite.expires_at).toLocaleDateString()}
            </Text>
          </View>
          <Pressable onPress={() => share(invite)}>
            <Text style={styles.action}>Share</Text>
          </Pressable>
          <Pressable onPress={() => revoke(invite.code)}>
            <Text style={[styles.action, { color: colors.danger }]}>Revoke</Text>
          </Pressable>
        </View>
      ))}

      <Button label="Back" variant="ghost" onPress={() => router.back()} />
    </ScrollScreen>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", gap: 8 },
  chip: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 18,
    paddingVertical: 10,
  },
  chipSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { color: colors.muted, fontSize: 15, fontWeight: "700" },
  created: {
    backgroundColor: colors.card,
    borderColor: colors.accent,
    borderWidth: 1,
    borderRadius: 16,
    padding: 20,
    gap: 12,
    alignItems: "center",
  },
  createdHint: { color: colors.muted, fontSize: 13, fontWeight: "700" },
  code: { color: colors.text, fontSize: 36, fontWeight: "800", letterSpacing: 4 },
  section: { color: colors.text, fontSize: 18, fontWeight: "700", marginTop: 8 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: 16,
  },
  rowTitle: { color: colors.text, fontSize: 16, fontWeight: "700" },
  rowMeta: { color: colors.muted, fontSize: 12, marginTop: 4 },
  action: { color: colors.accent, fontSize: 14, fontWeight: "700" },
});
