import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { ApiError, api, setAuthToken } from "./api";
import * as storage from "./storage";
import type { Me, Membership, Role } from "./types";

type AuthState = {
  ready: boolean;
  signedIn: boolean;
  me: Me | null;
  memberships: Membership[];
  pendingRole: Role;
  setPendingRole: (role: Role) => void;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
  reload: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [pendingRole, setPendingRole] = useState<Role>("athlete");

  const reload = useCallback(async () => {
    const [meData, boxes] = await Promise.all([
      api<Me>("/me"),
      api<Membership[]>("/boxes/mine"),
    ]);
    setMe(meData);
    setMemberships(boxes);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const token = await storage.getToken();
        if (token) {
          setAuthToken(token);
          await reload();
          setSignedIn(true);
        }
      } catch (error) {
        setAuthToken(null);
        if (error instanceof ApiError && error.status === 401) {
          await storage.clearToken();
        }
      } finally {
        setReady(true);
      }
    })();
  }, [reload]);

  const signIn = useCallback(
    async (token: string) => {
      setAuthToken(token);
      await reload();
      await storage.saveToken(token);
      setSignedIn(true);
    },
    [reload],
  );

  const signOut = useCallback(async () => {
    await storage.clearToken();
    setAuthToken(null);
    setMe(null);
    setMemberships([]);
    setSignedIn(false);
  }, []);

  const value = useMemo(
    () => ({
      ready,
      signedIn,
      me,
      memberships,
      pendingRole,
      setPendingRole,
      signIn,
      signOut,
      reload,
    }),
    [ready, signedIn, me, memberships, pendingRole, signIn, signOut, reload],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
