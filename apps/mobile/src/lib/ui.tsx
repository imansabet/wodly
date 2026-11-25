import type { ReactNode } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

export const colors = {
  bg: "#0B0B0F",
  card: "#16161D",
  border: "#2A2A35",
  text: "#F4F4F6",
  muted: "#9A9AAA",
  accent: "#FF4D2E",
  danger: "#FF6B6B",
};

export function Screen({ children }: { children: ReactNode }) {
  return (
    <SafeAreaView style={styles.screen}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={styles.content}>{children}</View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

export function Title({ children }: { children: ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function Subtitle({ children }: { children: ReactNode }) {
  return <Text style={styles.subtitle}>{children}</Text>;
}

export function ErrorText({ message }: { message: string | null }) {
  return message ? <Text style={styles.error}>{message}</Text> : null;
}

export function Input(props: TextInputProps) {
  return (
    <TextInput
      placeholderTextColor={colors.muted}
      autoCorrect={false}
      {...props}
      style={[styles.input, props.style]}
    />
  );
}

type ButtonProps = {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "ghost";
};

export function Button({
  label,
  onPress,
  loading = false,
  disabled = false,
  variant = "primary",
}: ButtonProps) {
  const ghost = variant === "ghost";
  const inactive = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={inactive}
      style={({ pressed }) => [
        styles.button,
        ghost ? styles.buttonGhost : styles.buttonPrimary,
        (pressed || inactive) && { opacity: 0.6 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors.text} />
      ) : (
        <Text style={[styles.buttonText, ghost && { color: colors.muted }]}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { flex: 1, padding: 24, justifyContent: "center", gap: 16 },
  title: { color: colors.text, fontSize: 32, fontWeight: "800" },
  subtitle: { color: colors.muted, fontSize: 16, lineHeight: 22 },
  error: { color: colors.danger, fontSize: 14 },
  input: {
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    color: colors.text,
    fontSize: 18,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  buttonPrimary: { backgroundColor: colors.accent },
  buttonGhost: { backgroundColor: "transparent" },
  buttonText: { color: colors.text, fontSize: 17, fontWeight: "700" },
});
