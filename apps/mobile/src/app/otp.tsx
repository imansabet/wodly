import { useLocalSearchParams, useRouter } from "expo-router";
import { useState } from "react";

import { useAuth } from "../lib/auth";
import { api, errorMessage } from "../lib/api";
import { Button, ErrorText, Input, Screen, Subtitle, Title } from "../lib/ui";

export default function Otp() {
  const router = useRouter();
  const { phone } = useLocalSearchParams<{ phone: string }>();
  const { signIn } = useAuth();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function verify() {
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await api<{ access_token: string }>(
        "/auth/otp/verify",
        { method: "POST", body: { phone, code } },
      );
      await signIn(access_token);
    } catch (e) {
      setError(errorMessage(e));
      setLoading(false);
    }
  }

  async function resend() {
    setError(null);
    setInfo(null);
    try {
      await api("/auth/otp/request", { method: "POST", body: { phone } });
      setInfo("A new code was sent.");
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  return (
    <Screen>
      <Title>Enter the code</Title>
      <Subtitle>
        Sent to {phone}.
        {__DEV__ ? " (Dev mode: the code is printed in the API server log.)" : ""}
      </Subtitle>
      <Input
        value={code}
        onChangeText={(text) => setCode(text.replace(/\D/g, "").slice(0, 6))}
        placeholder="123456"
        keyboardType="number-pad"
        maxLength={6}
        autoFocus
      />
      <ErrorText message={error} />
      {info ? <Subtitle>{info}</Subtitle> : null}
      <Button label="Verify" onPress={verify} loading={loading} disabled={code.length !== 6} />
      <Button label="Resend code" variant="ghost" onPress={resend} />
      <Button label="Back" variant="ghost" onPress={() => router.back()} />
    </Screen>
  );
}
