"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { apiRequest } from "@/lib/client-api";
import type { Cart, Product, User } from "@/lib/types";

type StoreContextValue = {
  user: User | null;
  cart: Cart | null;
  favorites: Map<number, number>;
  sessionLoading: boolean;
  language: "ar" | "en";
  currency: "SAR" | "USD" | "AED";
  login: (username: string, password: string) => Promise<void>;
  register: (data: Record<string, string>) => Promise<void>;
  logout: () => Promise<void>;
  refreshCart: () => Promise<void>;
  addToCart: (product: Product, quantity?: number, variantId?: number | null) => Promise<void>;
  updateCartItem: (itemId: number, quantity: number) => Promise<void>;
  removeCartItem: (itemId: number) => Promise<void>;
  applyCoupon: (code: string) => Promise<void>;
  removeCoupon: () => Promise<void>;
  toggleFavorite: (product: Product) => Promise<void>;
  setLanguage: (language: "ar" | "en") => void;
  setCurrency: (currency: "SAR" | "USD" | "AED") => void;
};

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [favorites, setFavorites] = useState(new Map<number, number>());
  const [sessionLoading, setSessionLoading] = useState(true);
  const [language, updateLanguage] = useState<"ar" | "en">("ar");
  const [currency, updateCurrency] = useState<"SAR" | "USD" | "AED">("SAR");

  const refreshCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    setCart(await apiRequest<Cart>("/cart/"));
  }, [user]);

  const refreshFavorites = useCallback(async () => {
    if (!user) {
      setFavorites(new Map());
      return;
    }
    const payload = await apiRequest<Array<{ id: number; product: Product }> | { results: Array<{ id: number; product: Product }> }>("/favorites/");
    const items = Array.isArray(payload) ? payload : payload.results;
    setFavorites(new Map(items.map((item) => [item.product.id, item.id])));
  }, [user]);

  useEffect(() => {
    const savedLanguage = localStorage.getItem("nova_language");
    const savedCurrency = localStorage.getItem("nova_currency");
    if (savedLanguage === "ar" || savedLanguage === "en") updateLanguage(savedLanguage);
    if (savedCurrency === "SAR" || savedCurrency === "USD" || savedCurrency === "AED") updateCurrency(savedCurrency);
    fetch("/api/auth/session")
      .then((response) => response.json())
      .then((payload) => setUser(payload.user))
      .finally(() => setSessionLoading(false));
  }, []);

  useEffect(() => {
    if (user) void Promise.all([refreshCart(), refreshFavorites()]);
    else {
      setCart(null);
      setFavorites(new Map());
    }
  }, [user, refreshCart, refreshFavorites]);

  async function login(username: string, password: string) {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail ?? "تعذر تسجيل الدخول");
    setUser(payload.user);
  }

  async function register(data: Record<string, string>) {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(Object.values(payload).flat().join(" "));
    setUser(payload.user);
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    setUser(null);
  }

  async function addToCart(product: Product, quantity = 1, variantId?: number | null) {
    if (!user) throw new Error("سجّل الدخول لإضافة المنتجات إلى السلة.");
    const payload: Record<string, number> = { product_id: product.id, quantity };
    if (variantId) payload.variant_id = variantId;
    setCart(await apiRequest<Cart>("/cart/items/", { method: "POST", body: JSON.stringify(payload) }));
  }

  async function updateCartItem(itemId: number, quantity: number) {
    setCart(await apiRequest<Cart>(`/cart/items/${itemId}/`, { method: "PATCH", body: JSON.stringify({ quantity }) }));
  }

  async function removeCartItem(itemId: number) {
    await apiRequest(`/cart/items/${itemId}/`, { method: "DELETE" });
    await refreshCart();
  }

  async function applyCoupon(code: string) {
    setCart(await apiRequest<Cart>("/cart/coupon/", { method: "POST", body: JSON.stringify({ code }) }));
  }

  async function removeCoupon() {
    setCart(await apiRequest<Cart>("/cart/coupon/", { method: "DELETE" }));
  }

  async function toggleFavorite(product: Product) {
    if (!user) throw new Error("سجّل الدخول لاستخدام المفضلة.");
    const favoriteId = favorites.get(product.id);
    if (favoriteId) {
      await apiRequest(`/favorites/${favoriteId}/`, { method: "DELETE" });
    } else {
      await apiRequest("/favorites/", { method: "POST", body: JSON.stringify({ product_id: product.id }) });
    }
    await refreshFavorites();
  }

  const setLanguage = (value: "ar" | "en") => {
    updateLanguage(value);
    localStorage.setItem("nova_language", value);
    document.documentElement.lang = value;
    document.documentElement.dir = value === "ar" ? "rtl" : "ltr";
  };
  const setCurrency = (value: "SAR" | "USD" | "AED") => {
    updateCurrency(value);
    localStorage.setItem("nova_currency", value);
  };

  const value = {
    user, cart, favorites, sessionLoading, language, currency, login, register, logout,
    refreshCart, addToCart, updateCartItem, removeCartItem, applyCoupon, removeCoupon,
    toggleFavorite, setLanguage, setCurrency,
  };

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const context = useContext(StoreContext);
  if (!context) throw new Error("useStore must be used inside StoreProvider");
  return context;
}
