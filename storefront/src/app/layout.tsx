import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "The Daily Print — Premium AI‑Designed Apparel",
  description:
    "Discover unique print‑on‑demand t‑shirts, hoodies, and mugs crafted by AI creativity. Fresh designs added daily — wear your vibe.",
  keywords: [
    "print on demand",
    "ai design",
    "unique t-shirts",
    "custom apparel",
    "ai generated",
    "hoodies",
    "mugs",
    "the daily print",
  ],
  openGraph: {
    title: "The Daily Print — Premium AI‑Designed Apparel",
    description:
      "Unique AI‑generated designs printed on premium apparel. New drops daily.",
    siteName: "The Daily Print",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "The Daily Print — Premium AI‑Designed Apparel",
    description:
      "Unique AI‑generated designs printed on premium apparel. New drops daily.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={outfit.variable}>
      <body className={outfit.className}>{children}</body>
    </html>
  );
}
