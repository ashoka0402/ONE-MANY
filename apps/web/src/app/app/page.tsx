import type { Metadata } from "next";
import { Workspace } from "@/components/workspace";
import "./workspace.css";
import "./demo-tour.css";
import "./emerald-live.css";

export const metadata: Metadata = {
  title: "Your shared workspace — ONE / MANY",
  description: "Private shared-needs workspace with Sandbox funding and provisional scheduling.",
  robots: { index: false, follow: false },
};

export default function AppPage() {
  return <Workspace />;
}
