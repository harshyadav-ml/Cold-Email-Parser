import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SystemProvider } from "../components/SystemContext";
import { Navbar } from "../components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "THE CLOSER — Outreach Engine",
  description: "Agent Meets Gmail — Human-in-the-Loop Review & Dispatch Stream",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">

      <body
        className={`${geistSans.variable} ${geistMono.variable} bg-black font-sans text-sm text-neutral-200 antialiased selection:bg-white selection:text-black min-h-screen flex flex-col`}
      >
        <SystemProvider>
          <Navbar />
          <div className="flex-1 w-full">{children}</div>
        </SystemProvider>
      </body>
    </html>
  );
}
