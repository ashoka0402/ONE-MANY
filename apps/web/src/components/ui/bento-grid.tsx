import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

// Adapted from the Aceternity UI Bento Grid (https://ui.aceternity.com/components/bento-grid).
// The public component source is used as a styling primitive; Stage 0 does not imply live data.
export function BentoGrid({ className, children }: { className?: string; children?: ReactNode }) {
  return (
    <div className={cn("mx-auto grid max-w-7xl grid-cols-1 gap-4 md:grid-cols-3", className)}>
      {children}
    </div>
  );
}

export function BentoGridItem({
  className,
  title,
  description,
  header,
  icon,
}: {
  className?: string;
  title?: ReactNode;
  description?: ReactNode;
  header?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div
      className={cn(
        "group/bento row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-neutral-200 bg-white p-4 transition duration-200 hover:shadow-xl",
        className,
      )}
    >
      {header}
      <div className="transition-transform duration-200 group-hover/bento:translate-x-2">
        {icon}
        <div className="mt-2 mb-2 font-sans font-bold">{title}</div>
        <div className="font-sans text-xs">{description}</div>
      </div>
    </div>
  );
}
