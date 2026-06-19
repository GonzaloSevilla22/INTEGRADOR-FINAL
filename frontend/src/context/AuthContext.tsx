import { createContext, useContext, useMemo, useState, useEffect, useCallback } from "react";
import { loginRequest, api } from "../services/api";

const TOKEN_KEY = "food_store_token";

export interface User {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  celular?: string;
  activo: boolean;
}

interface AuthContextValue {
  token: string | null;
  user: User | null;
  roles: string[];
  isAuthenticated: boolean;
  authLoading: boolean;
  isAdmin: boolean;
  isClient: boolean;
  isStock: boolean;
  isPedidos: boolean;
  hasRole: (role: string) => boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  verifySession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

function normalizeRole(role: string): string {
  return (role || "").trim().toUpperCase();
}

function hasAnyRole(roles: string[], target: string): boolean {
  const normalized = normalizeRole(target);
  if (normalized === "CLIENT") {
    return roles.some((r) => ["CLIENT", "CLIENTE"].includes(normalizeRole(r)));
  }
  return roles.some((r) => normalizeRole(r) === normalized);
}

export function AuthProvider({ children }: AuthProviderProps): JSX.Element {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [authLoading, setAuthLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)));

  const verifySession = useCallback(async () => {
    try {
      const me = await api.get("/auth/me");
      const data = me.data;
      const normalizedRoles = (data.roles || []).map((r: string) => normalizeRole(r));
      setUser({
        id: data.id,
        nombre: data.nombre,
        apellido: data.apellido,
        email: data.email,
        celular: data.celular,
        activo: data.activo,
      });
      setRoles(normalizedRoles);
    } catch {
      setUser(null);
      setRoles([]);
      setToken(null);
      localStorage.removeItem(TOKEN_KEY);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  // On mount, verify session using httpOnly cookie (sent automatically with withCredentials)
  useEffect(() => {
    if (token) {
      verifySession();
    } else {
      setAuthLoading(false);
    }
  }, []); // only on mount

  const login = async (email: string, password: string): Promise<void> => {
    if (!email.trim() || !password.trim()) {
      throw new Error("Email y clave son obligatorios.");
    }
    try {
      const response = await loginRequest({ email, password });
      const normalizedRoles = (response.roles || []).map((r) => normalizeRole(r));

      localStorage.setItem(TOKEN_KEY, response.access_token);
      setToken(response.access_token);
      setUser(response.usuario);
      setRoles(normalizedRoles);
    } catch (error) {
      throw error;
    }
  };

  const logout = (): void => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    setRoles([]);
  };

  const isAdmin = hasAnyRole(roles, "ADMIN");
  const isClient = hasAnyRole(roles, "CLIENT");
  const isStock = hasAnyRole(roles, "STOCK");
  const isPedidos = hasAnyRole(roles, "PEDIDOS");

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      roles,
      isAuthenticated: Boolean(token) && Boolean(user),
      authLoading,
      isAdmin,
      isClient,
      isStock,
      isPedidos,
      hasRole: (role: string) => hasAnyRole(roles, role),
      login,
      logout,
      verifySession,
    }),
    [token, user, roles, authLoading, isAdmin, isClient, isStock, isPedidos]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}
