"use client";

import { useMemo } from "react";
import type { TaPart } from "@/lib/data";
import { shortDate } from "@/lib/format";
import { isId, t } from "@/lib/i18n";
import ContributionSkyline from "./ui/contribution-skyline";

/** GitHub-style calendar: one square per day from today to the turnaround, darker when more orders fall due. */
export function OrderCalendar({ parts, asOf, taDate, title }: { parts: TaPart[]; asOf: string; taDate: string; title?: string }) {
  const data = useMemo(() => {
    const m = new Map<string, number>();
    for (const p of parts) {
      if (p.status === "READY" || p.status === "TOO_LATE") continue;
      m.set(p.order_by, (m.get(p.order_by) ?? 0) + 1);
    }
    return Array.from(m, ([date, count]) => ({ date, count }));
  }, [parts]);
  const blocks = useMemo(() => {
    const due = data.reduce((a, d) => a + d.count, 0);
    const late = parts.filter((p) => p.status === "TOO_LATE").length;
    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
    const busiest = [...data].sort((a, b) => b.count - a.count)[0];
    const next = sorted[0];
    const parts_ = (n: number) => t(n === 1 ? "part" : "parts", "suku cadang");
    return [
      { label: t("Orders still on time", "Pesanan yang masih tepat waktu"), value: String(due), unit: parts_(due), sub: t(`To place before ${shortDate(taDate, true)}`, `Harus dipesan sebelum ${shortDate(taDate, true)}`) },
      { label: t("Already too late", "Sudah terlambat"), value: String(late), unit: parts_(late), sub: t("Not on the calendar: rush them or use a duplicate", "Tidak ada di kalender: percepat pesanannya atau pakai suku cadang kembar") },
      { label: t("Next deadline", "Tenggat berikutnya"), value: next ? shortDate(next.date) : t("None", "Tidak ada"), unit: "", sub: next ? t(`${next.count} ${next.count === 1 ? "part" : "parts"} to order by then`, `${next.count} suku cadang harus dipesan sebelum itu`) : t("Nothing is due", "Tidak ada yang jatuh tempo") },
      { label: t("Busiest deadline", "Tenggat terpadat"), value: busiest ? String(busiest.count) : "0", unit: busiest ? parts_(busiest.count) : parts_(2), sub: busiest ? t(`All due by ${shortDate(busiest.date)}`, `Semuanya jatuh tempo ${shortDate(busiest.date)}`) : t("No orders", "Tidak ada pesanan") },
    ];
  }, [data, parts, taDate]);
  return (
    <ContributionSkyline
      data={data}
      startDate={asOf}
      endDate={taDate}
      defaultView="2d"
      palette="ember"
      unit={t("order", "pesanan")}
      unitPlural={t("orders", "pesanan")}
      locale={isId() ? "id-ID" : "en-US"}
      weekStart={1}
      heightScale={0.8}
      blocks={blocks}
      title={title ?? t("Last safe day to order each part", "Batas aman pemesanan tiap suku cadang")}
      hints={t(
        ["Each square is one day. The darker it is, the more parts must be ordered by that day. Last safe day = turnaround start − slow-case delivery time − 14 days of buffer.", "Each block is one day. The taller it is, the more parts must be ordered by that day. Drag to turn, double-click to reset."],
        ["Setiap kotak mewakili satu hari. Makin gelap warnanya, makin banyak suku cadang yang harus dipesan paling lambat pada hari itu. Batas aman = awal turnaround − waktu kirim skenario lambat − 14 hari cadangan.", "Setiap balok mewakili satu hari. Makin tinggi baloknya, makin banyak suku cadang yang harus dipesan paling lambat pada hari itu. Seret untuk memutar, klik dua kali untuk mengembalikan."],
      )}
    />
  );
}
