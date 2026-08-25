import type { Metadata } from "next";

import "./globals.css";

import { StoreHeader } from "@/components/StoreHeader";
import { StoreProvider } from "@/components/StoreProvider";

export const metadata: Metadata = {
  title: "NOVA Marketplace",
  description: "متجر عربي للويب وAndroid وiOS مبني بـ Next.js وDjango REST Framework.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl" data-scroll-behavior="smooth">
      <body>
        <StoreProvider>
          <StoreHeader />
          {children}
        </StoreProvider>
      </body>
    </html>
  );
}
