"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/new", label: "New Process" },
  { href: "/jobs", label: "History" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 shrink-0 border-r bg-muted/40 p-4 flex flex-col gap-1">
      <Link href="/new" className="font-semibold text-lg mb-4 px-2">
        ProcessFlow AI
      </Link>
      {NAV.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "rounded-md px-3 py-2 text-sm transition-colors hover:bg-accent",
            pathname.startsWith(item.href) && "bg-accent font-medium"
          )}
        >
          {item.label}
        </Link>
      ))}
    </aside>
  );
}
