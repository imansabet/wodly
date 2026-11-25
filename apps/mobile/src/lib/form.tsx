import type { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors } from "./ui";

export function Label({ children }: { children: ReactNode }) {
  return <Text style={styles.label}>{children}</Text>;
}

export function Chip({
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

export function Stepper({
  label,
  display,
  onStep,
}: {
  label: string;
  display: string;
  onStep: (direction: 1 | -1) => void;
}) {
  return (
    <View style={styles.stepper}>
      <Text style={styles.stepperLabel}>{label}</Text>
      <View style={styles.controls}>
        <Pressable onPress={() => onStep(-1)} style={styles.stepBtn} hitSlop={8}>
          <Text style={styles.stepBtnText}>−</Text>
        </Pressable>
        <Text style={styles.value}>{display}</Text>
        <Pressable onPress={() => onStep(1)} style={styles.stepBtn} hitSlop={8}>
          <Text style={styles.stepBtnText}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  label: { color: colors.muted, fontSize: 13, fontWeight: "700", marginTop: 4 },
  chip: {
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 9,
  },
  chipSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  chipText: { color: colors.muted, fontSize: 14, fontWeight: "700" },
  stepper: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.card,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  stepperLabel: { color: colors.text, fontSize: 16 },
  controls: { flexDirection: "row", alignItems: "center", gap: 14 },
  stepBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  stepBtnText: { color: colors.text, fontSize: 20, fontWeight: "700" },
  value: {
    color: colors.text,
    fontSize: 18,
    fontWeight: "700",
    minWidth: 56,
    textAlign: "center",
  },
});
