import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const KEY = "wodly_token";

export async function getToken(): Promise<string | null> {
  if (Platform.OS === "web") return localStorage.getItem(KEY);
  return SecureStore.getItemAsync(KEY);
}

export async function saveToken(token: string): Promise<void> {
  if (Platform.OS === "web") return localStorage.setItem(KEY, token);
  await SecureStore.setItemAsync(KEY, token);
}

export async function clearToken(): Promise<void> {
  if (Platform.OS === "web") return localStorage.removeItem(KEY);
  await SecureStore.deleteItemAsync(KEY);
}
