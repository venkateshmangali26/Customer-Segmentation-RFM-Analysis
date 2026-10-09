import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RFM Analysis — Customer Segmentation",
  description:
    "Interactive customer segmentation dashboard using Recency, Frequency, Monetary (RFM) scoring with quantile-based 1–5 scoring and 11 standard marketing segments.",
  keywords: [
    "RFM analysis",
    "customer segmentation",
    "marketing analytics",
    "Next.js",
    "TypeScript",
  ],
  authors: [{ name: "RFM Dashboard" }],
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  openGraph: {
    title: "RFM Analysis — Customer Segmentation",
    description: "Interactive RFM customer segmentation dashboard",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "RFM Analysis — Customer Segmentation",
    description: "Interactive RFM customer segmentation dashboard",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
        <SonnerToaster richColors closeButton position="top-right" />
      </body>
    </html>
  );
}
