import type { Metadata } from "next";
import "@bryntum/scheduler-community/scheduler.css";
import "@bryntum/scheduler-community/svalbard-light.css";
import "./globals.css";
import "./brand.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "ONE / MANY — A smarter way to share",
  description:
    "Discover compatible needs and explore consent-based shared asset purchases with a PayPal Sandbox demonstration.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body>
        <a className="skip-link" href="#main">Skip to content</a>
        {children}
      </body>
    </html>
  );
}
