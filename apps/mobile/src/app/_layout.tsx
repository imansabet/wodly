import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, View } from "react-native";

import { AuthProvider, useAuth } from "../lib/auth";
import { colors } from "../lib/ui";

function RootNavigator() {
  const { ready, signedIn, memberships } = useAuth();

  if (!ready) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: colors.bg,
        }}
      >
        <ActivityIndicator color={colors.accent} />
      </View>
    );
  }

  const hasBox = memberships.length > 0;

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.bg },
      }}
    >
      <Stack.Protected guard={!signedIn}>
        <Stack.Screen name="index" />
        <Stack.Screen name="phone" />
        <Stack.Screen name="otp" />
      </Stack.Protected>
      <Stack.Protected guard={signedIn && !hasBox}>
        <Stack.Screen name="setup" />
      </Stack.Protected>
      <Stack.Protected guard={signedIn && hasBox}>
        <Stack.Screen name="home" />
        <Stack.Screen name="members" />
        <Stack.Screen name="invite" />
      </Stack.Protected>
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <RootNavigator />
    </AuthProvider>
  );
}
