import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import ChatWidget from "@/components/chat/ChatWidget";

const playfairDisplay = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ChronoCanvasAI — AI Portrait Studio",
  description:
    "Describe a historical figure, pick an artistic style, and watch AI render them in seconds.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${playfairDisplay.variable} ${inter.variable}`}
    >
      <body className="font-sans bg-cream text-dark antialiased">
        <Navbar />
        <main>{children}</main>
        <Footer />
        <ChatWidget />
      </body>
    </html>
  );
}
