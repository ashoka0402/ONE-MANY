"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import {
  CalendarDays, CheckCircle2, Clock3, LoaderCircle, RefreshCw, ShieldCheck,
  Trash2, Users,
} from "lucide-react";

const BryntumSharedSchedule = dynamic(() => import("@/components/bryntum-schedule"), {
  ssr: false,
  loading: () => <div className="reservation-timeline-loading">Loading the shared timeline...</div>,
});

type Group = {
  id: string;
  product_title: string;
  state: string;
  target_members: number;
  accepted_count: number;
  captured_display: string;
  total_display: string;
};
type Reserved = {
  id: string;
  slot: number;
  start_date: string;
  end_date: string;
  is_you: boolean;
  version: number;
};
type Board = {
  group_id: string;
  product_title: string;
  group_state: string;
  bookable: boolean;
  own_version: number;
  own_window: { start_date: string; end_date: string } | null;
  reservations: Reserved[];
  notice: string;
};
type ErrorResponse = { error?: { message?: string } };

const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function call<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}/api/v1${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  const result = (await response.json().catch(() => null)) as (T & ErrorResponse) | null;
  if (!response.ok) throw new Error(result?.error?.message || `Request failed (${response.status})`);
  return result as T;
}

function messageFrom(err: unknown): string {
  if (err instanceof TypeError) return "Cannot reach the API. Check your backend connection.";
  return err instanceof Error ? err.message : "The scheduling request failed.";
}

export function ReservationPanel({ token }: { token: string }) {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [board, setBoard] = useState<Board | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadGroups() {
    setBusy("groups");
    setError("");
    try {
      const result = await call<{ groups: Group[] }>("/funding/groups", token);
      setGroups(result.groups);
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setBusy("");
    }
  }

  async function loadBoard(groupId: string) {
    setBusy("board");
    setError("");
    setNotice("");
    try {
      const data = await call<Board>(`/funding/groups/${groupId}/reservations`, token);
      const own = data.reservations.find(item => item.is_you);
      setSelectedId(groupId);
      setBoard(data);
      setStartDate(own?.start_date || data.own_window?.start_date || "");
      setEndDate(own?.end_date || data.own_window?.end_date || "");
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setBusy("");
    }
  }

  async function reserve() {
    if (!selectedId || !board) return;
    if (!startDate || !endDate || endDate < startDate) {
      setError("Choose a valid start and end calendar date.");
      return;
    }
    setBusy("reserve");
    setError("");
    setNotice("");
    try {
      const data = await call<Board>(
        `/funding/groups/${selectedId}/reservation`,
        token,
        {
          method: "PUT",
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
            expected_version: board.own_version,
          }),
        },
      );
      setBoard(data);
      setNotice("Your provisional booking was saved. The database checks all other active reservations.");
    } catch (err) {
      setError(messageFrom(err) + " Refresh the calendar if another member changed a booking.");
    } finally {
      setBusy("");
    }
  }

  async function cancel() {
    if (!selectedId) return;
    setBusy("cancel");
    setError("");
    setNotice("");
    try {
      const data = await call<Board>(
        `/funding/groups/${selectedId}/reservation`,
        token,
        { method: "DELETE" },
      );
      setBoard(data);
      setNotice("Your active booking was cancelled. The previous slot is now available.");
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setBusy("");
    }
  }

  const ownReservation = board?.reservations.find(item => item.is_you);
  const selectedGroup = groups?.find(group => group.id === selectedId);
  const timelineKey = board
    ? board.group_id + ":" + board.reservations.map(
      r => `${r.id}:${r.start_date}:${r.end_date}:${r.version}`,
    ).join(";")
    : "";

  return (
    <section className="reservation-section" id="scheduling" aria-labelledby="reservation-heading">
      <div className="reservation-head">
        <div>
          <span className="work-kicker">05 / SHARED SCHEDULING · BRYNTUM</span>
          <h2 id="reservation-heading">One asset. Everyone&apos;s turn.</h2>
          <p>See agreed usage windows on one timeline. Each member manages only their own dates.</p>
        </div>
        <button
          type="button"
          disabled={Boolean(busy)}
          onClick={() => void loadGroups()}
          className="reservation-outline"
        >
          {busy === "groups"
            ? <LoaderCircle size={15} className="work-spinner" />
            : <RefreshCw size={15} />}
          Load my groups
        </button>
      </div>
      <div className="reservation-terms">
        <ShieldCheck size={17} />
        <p>Bookings become editable only after every Sandbox contribution is verified. These are <strong>provisional whole-day plans</strong>, not evidence of product delivery. Dates are civil calendar days, with no assumed time zone or handover time.</p>
      </div>

      {error && <p className="work-error" role="alert">{error}</p>}
      {notice && <p className="work-notice" role="status"><CheckCircle2 size={16} /> {notice}</p>}

      {groups === null ? (
        <div className="reservation-empty">
          <CalendarDays size={34} strokeWidth={1.3} />
          <strong>Your shared-use calendar</strong>
          <p>Load your accepted funding groups to view real reservations.</p>
        </div>
      ) : groups.length === 0 ? (
        <div className="reservation-empty">
          <Users size={32} strokeWidth={1.3} />
          <strong>No accepted groups yet</strong>
          <p>Join or create a Sandbox funding group in the contribution section first.</p>
        </div>
      ) : (
        <>
          <div className="reservation-group-picker">
            {groups.map(group => (
              <button
                type="button"
                key={group.id}
                disabled={Boolean(busy)}
                className={selectedId === group.id ? "is-selected" : ""}
                onClick={() => void loadBoard(group.id)}
              >
                <span>{group.product_title}</span>
                <small>
                  {group.state.replaceAll("_", " ")} · {group.accepted_count}/{group.target_members} members
                </small>
              </button>
            ))}
          </div>

          {board && selectedGroup && (
            <div className="reservation-board">
              <div className="reservation-board-heading">
                <div>
                  <span className="work-kicker">{board.bookable ? "AVAILABLE TO SCHEDULE" : "VIEW ONLY"}</span>
                  <h3>{board.product_title}</h3>
                  <p>{board.reservations.length} active {board.reservations.length === 1 ? "booking" : "bookings"} · {selectedGroup.captured_display} of {selectedGroup.total_display} verified in Sandbox</p>
                </div>
                <button
                  type="button"
                  className="reservation-outline"
                  disabled={Boolean(busy)}
                  onClick={() => void loadBoard(board.group_id)}
                >
                  <RefreshCw size={14} /> Refresh calendar
                </button>
              </div>
              <div className="reservation-calendar-caption">
                <CalendarDays size={16} />
                <span>Real PostgreSQL reservations · Bryntum Scheduler Community (read-only view)</span>
              </div>
              <BryntumSharedSchedule
                key={timelineKey}
                groupId={board.group_id}
                ownWindow={board.own_window}
                reservations={board.reservations}
              />
              {board.reservations.length === 0 && (
                <p className="reservation-no-events">No booked dates yet. The calendar will populate from saved member bookings.</p>
              )}

              <div className="reservation-form">
                <div>
                  <h4><Clock3 size={16} /> Reserve your own days</h4>
                  <p>{board.own_window
                    ? `Your allowed window: ${board.own_window.start_date} to ${board.own_window.end_date} (inclusive).`
                    : "Your original request must include both dates before booking."}</p>
                </div>
                <div className="reservation-fields">
                  <label>
                    Start date
                    <input type="date" value={startDate}
                      min={board.own_window?.start_date}
                      max={board.own_window?.end_date}
                      onChange={event => setStartDate(event.target.value)}
                      disabled={!board.bookable || Boolean(busy)} />
                  </label>
                  <label>
                    End date (inclusive)
                    <input type="date" value={endDate}
                      min={startDate || board.own_window?.start_date}
                      max={board.own_window?.end_date}
                      onChange={event => setEndDate(event.target.value)}
                      disabled={!board.bookable || Boolean(busy)} />
                  </label>
                </div>
                <div className="reservation-buttons">
                  <button type="button" className="reservation-primary"
                    disabled={!board.bookable || Boolean(busy) || !startDate || !endDate}
                    onClick={() => void reserve()}>
                    {busy === "reserve" ? <LoaderCircle size={15} className="work-spinner" /> : <CheckCircle2 size={15} />}
                    {ownReservation ? "Save new dates" : "Confirm provisional booking"}
                  </button>
                  {ownReservation && (
                    <button type="button" className="reservation-danger" disabled={Boolean(busy)}
                      onClick={() => void cancel()}>
                      <Trash2 size={14} /> Cancel my booking
                    </button>
                  )}
                </div>
                {!board.bookable && (
                  <p className="reservation-locked">Scheduling is paused until the funding state is fully verified. Existing bookings remain visible to accepted members.</p>
                )}
              </div>
              <p className="reservation-notice">{board.notice}</p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
