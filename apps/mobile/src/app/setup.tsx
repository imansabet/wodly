import { useState } from "react";

import { api, errorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Button, ErrorText, Input, Screen, Subtitle, Title } from "../lib/ui";

export default function Setup() {
  const { me, pendingRole, reload, signOut } = useAuth();
  const [mode, setMode] = useState<"create" | "join">(
    pendingRole === "owner" ? "create" : "join",
  );
  const [name, setName] = useState("");
  const [boxName, setBoxName] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needName = !me?.full_name;
  const ready =
    (!needName || name.trim().length >= 2) &&
    (mode === "create" ? boxName.trim().length >= 2 : code.trim().length > 0);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      if (needName) {
        await api("/me", { method: "PATCH", body: { full_name: name.trim() } });
      }
      if (mode === "create") {
        await api("/boxes", { method: "POST", body: { name: boxName.trim() } });
      } else {
        await api("/invites/redeem", { method: "POST", body: { code: code.trim() } });
      }
      await reload(); // memberships become non-empty, so the router moves to home
    } catch (e) {
      setError(errorMessage(e));
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Title>{mode === "create" ? "Create your box" : "Join your box"}</Title>
      <Subtitle>
        {mode === "create"
          ? "Your coaches and athletes will see this name everywhere."
          : "Ask your box for an invite code."}
      </Subtitle>

      {needName ? (
        <Input value={name} onChangeText={setName} placeholder="Your name" />
      ) : null}

      {mode === "create" ? (
        <Input value={boxName} onChangeText={setBoxName} placeholder="Box name" />
      ) : (
        <Input
          value={code}
          onChangeText={(t) => setCode(t.toUpperCase())}
          placeholder="Invite code"
          autoCapitalize="characters"
        />
      )}

      <ErrorText message={error} />
      <Button
        label={mode === "create" ? "Create box" : "Join box"}
        onPress={submit}
        loading={loading}
        disabled={!ready}
      />
      <Button
        label={mode === "create" ? "I have an invite code" : "I own a box"}
        variant="ghost"
        onPress={() => {
          setError(null);
          setMode(mode === "create" ? "join" : "create");
        }}
      />
      <Button label="Sign out" variant="ghost" onPress={signOut} />
    </Screen>
  );
}
