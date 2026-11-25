import { useRouter } from "expo-router";
import { useState } from "react";

import { ApiError, api, errorMessage } from "../lib/api";
import { Button, ErrorText, Input, Screen, Subtitle, Title } from "../lib/ui";

export default function Phone() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      await api("/auth/otp/request", { method: "POST", body: { phone } });
      router.push({ pathname: "/otp", params: { phone } });
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 422
          ? "Enter a valid phone number, e.g. 09121234567"
          : errorMessage(e),
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Title>Your phone number</Title>
      <Subtitle>We'll send you a 6-digit code.</Subtitle>
      <Input
        value={phone}
        onChangeText={setPhone}
        placeholder="09121234567"
        keyboardType="phone-pad"
        autoFocus
      />
      <ErrorText message={error} />
      <Button label="Send code" onPress={submit} loading={loading} disabled={phone.trim().length < 8} />
      <Button label="Back" variant="ghost" onPress={() => router.back()} />
    </Screen>
  );
}
