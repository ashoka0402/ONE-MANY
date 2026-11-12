"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import {
  AlertTriangle, ArrowRight, CheckCircle2, Clock3, CreditCard,
  LoaderCircle, RefreshCw, ShieldCheck, Users,
} from "lucide-react";
import type { AuditRow, MemberRow } from "@/components/ag-ledger-grid";

const AgLedgerGrid = dynamic(
  () => import("@/components/ag-ledger-grid").then(mod => mod.AgLedgerGrid),
  { ssr: false, loading: () => <div className="ledger-grid-loading">Opening contribution ledger...</div> },
);

type FundingGroup = {
  id: string;
  product_title: string;
  state: string;
  currency: string;
  captured_display: string;
  total_display: string;
  accepted_count: number;
  target_members: number;
};
type Ledger = {
  group_id: string;
  product_title: string;
  group_state: string;
  currency: string;
  total_minor: number;
  total_display: string;
  captured_minor: number;
  captured_display: string;
  outstanding_minor: number;
  outstanding_display: string;
  verified_members: number;
  accepted_members: number;
  target_members: number;
  progress_percent: number;
  reconciliation: "in_progress" | "reconciled" | "requires_review";
  as_of: string;
  members: MemberRow[];
  events: AuditRow[];
  has_more_events: boolean;
  notice: string;
};
type ApiError = { error?: { message?: string } };
const apiOrigin = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, token: string): Promise<T> {
  const response = await fetch(`${apiOrigin}/api/v1${path}`, {
    method: "GET",
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = (await response.json().catch(() => null)) as (T & ApiError) | null;
  if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`);
  return body as T;
}

function userError(reason: unknown) {
  if (reason instanceof TypeError) return "Cannot reach the API. Check that FastAPI is running.";
  return reason instanceof Error ? reason.message : "Ledger could not be loaded.";
}

export function LedgerPanel({ token }: { token: string }) {
  const [groups, setGroups] = useState<FundingGroup[] | null>(null);
  const [active, setActive] = useState<string | null>(null);
  const [ledger, setLedger] = useState<Ledger | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function loadGroups() {
    setBusy("groups");
    setError("");
    try {
      const result = await request<{ groups: FundingGroup[] }>("/funding/groups", token);
      setGroups(result.groups);
      if (active && !result.groups.some(group => group.id === active)) {
        setActive(null);
        setLedger(null);
      }
    } catch (reason) {
      setError(userError(reason));
    } finally {
      setBusy("");
    }
  }
  async function loadLedger(groupId: string) {
    setBusy("ledger");
    setError("");
    setActive(groupId);
    setLedger(null);
    try {
      const result = await request<Ledger>(
        `/funding/groups/${groupId}/ledger`, token,
      );
      setLedger(result);
    } catch (reason) {
      setError(userError(reason));
    } finally {
      setBusy("");
    }
  }
  const hasGroups = groups !== null && groups.length > 0;

  return (
    <section id="ledger" className="ledger-panel" aria-labelledby="ledger-heading">
      <div className="ledger-head">
        <div>
          <span className="work-kicker">06 / AG GRID · CONTRIBUTION INTELLIGENCE</span>
          <h2 id="ledger-heading">Every contribution. Accounted for.</h2>
          <p>Read-only PayPal Sandbox payment records with clear member approval, verified capture, and reversal states.</p>
        </div>
        <button className="ledger-button" type="button" disabled={Boolean(busy)}
          onClick={() => void loadGroups()}>
          {busy === "groups" ? <LoaderCircle className="work-spinner" size={15} /> : <RefreshCw size={15} />}
          Load my ledgers
        </button>
      </div>
      <div className="ledger-terms">
        <ShieldCheck size={17} />
        <span>These are <strong>Sandbox merchant test payments</strong>, not bank-settled funds, escrow, actual purchases or automatic refunds. Only server-recorded verified completed captures count toward the total.</span>
      </div>
      {error && <p className="work-error" role="alert">{error}</p>}
      {groups === null ? (
        <div className="ledger-empty"><CreditCard size={30} strokeWidth={1.3} />
          <strong>Nothing to inspect yet</strong>
          <p>Load your accepted groups to inspect their actual contributions.</p>
        </div>
      ) : !hasGroups ? (
        <div className="ledger-empty"><Users size={30} strokeWidth={1.3} />
          <strong>No joined funding groups</strong>
          <p>Create or join a funding group first. An AI match does not count as a contributor.</p>
        </div>
      ) : (
        <>
          <div className="ledger-group-picker" aria-label="Your funding ledgers">
            {groups.map(group => (
              <button
                key={group.id}
                type="button"
                disabled={Boolean(busy)}
                className={active === group.id ? "selected" : ""}
                onClick={() => void loadLedger(group.id)}
              >
                <span>{group.product_title}</span>
                <small>{group.captured_display} / {group.total_display} · {group.state.replaceAll("_", " ")}</small>
                <ArrowRight size={15} />
              </button>
            ))}
          </div>
          {busy === "ledger" && <div className="ledger-grid-loading"><LoaderCircle size={16} className="work-spinner" /> Rechecking saved records...</div>}
          {ledger && (
            <div className="ledger-details">
              <div className="ledger-detail-heading">
                <div>
                  <span className="work-kicker">GROUP PAYMENT SNAPSHOT</span>
                  <h3>{ledger.product_title}</h3>
                  <p><Clock3 size={13} /> Recorded as of {new Date(ledger.as_of).toLocaleString()}</p>
                </div>
                <button className="ledger-button" type="button" disabled={Boolean(busy)}
                  onClick={() => void loadLedger(ledger.group_id)}>
                  <RefreshCw size={14} /> Refresh records
                </button>
              </div>
              <div className="ledger-metrics">
                <article><span>Accepted total</span><strong>{ledger.total_display}</strong><small>{ledger.currency} · group target</small></article>
                <article><span>Verified captured</span><strong>{ledger.captured_display}</strong><small>Completed Sandbox captures</small></article>
                <article><span>Still outstanding</span><strong>{ledger.outstanding_display}</strong><small>Not yet verified</small></article>
                <article><span>Verified members</span><strong>{ledger.verified_members} / {ledger.target_members}</strong><small>{ledger.accepted_members} explicitly joined</small></article>
              </div>
              <div className="ledger-progress">
                <div>
                  <span>Capture progress</span><strong>{ledger.progress_percent}%</strong>
                </div>
                <div className="ledger-progress-rail" role="progressbar"
                  aria-label="Verified Sandbox funding progress"
                  aria-valuemin={0} aria-valuemax={100} aria-valuenow={ledger.progress_percent}>
                  <div style={{ width: `${ledger.progress_percent}%` }} />
                </div>
              </div>
              {ledger.reconciliation === "reconciled"
                ? <p className="ledger-state ledger-state-success"><CheckCircle2 size={16} /> All shares reconcile with stored verified Sandbox capture records.</p>
                : ledger.reconciliation === "requires_review"
                ? <p className="ledger-state ledger-state-warning"><AlertTriangle size={16} /> Payment or record mismatch: this group requires review. Do not assume the displayed amount is fully funded.</p>
                : <p className="ledger-state ledger-state-pending"><Clock3 size={15} /> Awaiting remaining acceptances or completed verified Sandbox captures.</p>}
              <AgLedgerGrid
                groupId={ledger.group_id}
                members={ledger.members}
                events={ledger.events}
              />
              {ledger.has_more_events && <p className="ledger-history-note">Showing the latest 200 audit entries; older events are not included in this view.</p>}
              <p className="ledger-history-note">{ledger.notice}</p>
            </div>
          )}
        </>
      )}
    </section>
  );
}
