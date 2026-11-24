import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { BRAND } from "@/lib/brand";
import { PwaRegister } from "@/components/pwa";
import { Suspense, type ReactNode } from "react";
import { LangProvider } from "@/components/lang";
import { getLang } from "@/lib/i18n-server";

const ui = Geist({ variable: "--font-ui", subsets: ["latin"], weight: ["400", "500", "600", "700"] });

export const metadata: Metadata = {
  title: { default: BRAND, template: `%s · ${BRAND}` },
  description: "Spare-part readiness, forecasts and stock decisions for plant maintenance.",
  applicationName: BRAND,
  appleWebApp: { capable: true, title: BRAND, statusBarStyle: "default" },
};

export const viewport: Viewport = {
  themeColor: "#f1eee9",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

/** Reads the language cookie once per request; every page below renders in it. */
async function LangRoot({ children }: { children: ReactNode }) {
  const lang = await getLang();
  return <LangProvider lang={lang}>{children}</LangProvider>;
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={ui.variable}>
      <body>
        <Suspense>
          <LangRoot>{children}</LangRoot>
        </Suspense>
        <PwaRegister />
      </body>
    </html>
  );
}
