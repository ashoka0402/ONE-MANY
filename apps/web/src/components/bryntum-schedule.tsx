"use client";

import { BryntumScheduler } from "@bryntum/scheduler-react-community";

type Scheduled = {
  id: string;
  slot: number;
  start_date: string;
  end_date: string;
  is_you: boolean;
};

function localDay(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function nextCivilDay(value: string): Date {
  const date = localDay(value);
  date.setDate(date.getDate() + 1);
  return date;
}

export default function BryntumSharedSchedule({
  groupId,
  reservations,
  ownWindow,
}: {
  groupId: string;
  reservations: Scheduled[];
  ownWindow: { start_date: string; end_date: string } | null;
}) {
  // From real persisted rows only. No sample events or browser-side writes.
  const dates = [
    ...reservations.flatMap(r => [r.start_date, r.end_date]),
    ...(ownWindow ? [ownWindow.start_date, ownWindow.end_date] : []),
  ];
  const initial = dates.length ? dates.sort()[0] : new Date().toISOString().slice(0, 10);
  const last = dates.length ? dates.sort()[dates.length - 1] : initial;
  const start = localDay(initial);
  const end = nextCivilDay(last);
  start.setDate(start.getDate() - 2);
  end.setDate(end.getDate() + 4);

  const events = reservations.map(reservation => ({
    id: reservation.id,
    resourceId: groupId,
    name: reservation.is_you ? "Your booked days" : `Member ${reservation.slot} · booked days`,
    startDate: localDay(reservation.start_date),
    endDate: nextCivilDay(reservation.end_date),
  }));

  return (
    <div className="reservation-bryntum-host" role="region" aria-label="Shared asset booking timeline">
      <BryntumScheduler
        readOnly={true}
        resources={[{ id: groupId, name: "One shared asset" }]}
        events={events}
        startDate={start}
        endDate={end}
        viewPreset="dayAndWeek"
        columns={[{ text: "Shared asset", field: "name", width: 180 }]}
        rowHeight={70}
        barMargin={8}
        height={310}
      />
    </div>
  );
}
