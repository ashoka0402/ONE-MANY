"use client";

import { useState } from "react";
import {
  ArrowRight, CheckCircle2, Clipboard, CreditCard, ExternalLink,
  LoaderCircle, RefreshCcw, ShieldAlert, Users,
} from "lucide-react";

type Need = {
  id: string;
  request_text: string;
  status: "open" | "archived";
  discoverable: boolean;
  needed_from: string | null;
  needed_until: string | null;
  location_label: string | null;
  intent: { asset_type: string; shareable: boolean } | null;
};
type Proposal = {
  id: string;
  product_title: string;
  price_display: string;
  prospective_members: number;
  quote_expires_at: string;
  status: string;
};
type Member = {
  slot: number;
  share_minor: number;
  share_display: string;
  payment_state: string;
  is_you: boolean;
};
type Group = {
  id: string;
  proposal_id: string;
  product_title: string;
  product_image_url: string | null;
  state: string;
  currency: string;
  total_display: string;
  captured_display: string;
  accepted_count: number;
  target_members: number;
  expires_at: string;
  members: Member[];
  disclaimer: string;
};
type Created = { group: Group; invite_code: string };
type Order = { approval_url: string; paypal_order_id: string; state: string };
type ErrorShape = { error?: { message?: string } };

const origin = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function call<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${origin}/api/v1${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  const body = (await response.json().catch(() => null)) as (T & ErrorShape) | null;
  if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`);
  return body as T;
}

function errorMessage(error: unknown): string {
  if (error instanceof TypeError) return "The API could not be reached.";
  return error instanceof Error ? error.message : "Request failed.";
}

export function FundingPanel({ token, needs }: { token: string; needs: Need[] }) {
  const [proposals, setProposals] = useState<Proposal[] | null>(null);
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [invite, setInvite] = useState("");
  const [selectedNeed, setSelectedNeed] = useState("");
  const [newInvitation, setNewInvitation] = useState("");

  async function refresh() {
    setBusy("refresh");
    setError("");
    try {
      const [a, b] = await Promise.all([
        call<{ proposals: Proposal[] }>("/proposals", token),
        call<{ groups: Group[] }>("/funding/groups", token),
      ]);
      setProposals(a.proposals);
      setGroups(b.groups);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function createGroup(proposalId: string) {
    setBusy("create");
    setError("");
    setNotice("");
    try {
      const result = await call<Created>(
        `/proposals/${proposalId}/funding-group`, token, { method: "POST" },
      );
      setNewInvitation(result.invite_code);
      setNotice("Funding group created. Share the invitation with eligible people, who must join explicitly.");
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function joinGroup() {
    if (!selectedNeed || !invite.trim()) {
      setError("Choose an eligible need and enter an invitation code.");
      return;
    }
    setBusy("join");
    setError("");
    setNotice("");
    try {
      await call<Group>("/funding/join", token, {
        method: "POST",
        body: JSON.stringify({ invite_code: invite.trim(), need_id: selectedNeed }),
      });
      setInvite("");
      setNotice("You've explicitly joined the group. No payment has been initiated.");
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function rotate(groupId: string) {
    setBusy("rotate");
    setError("");
    try {
      const result = await call<Created>(
        `/funding/groups/${groupId}/rotate-invite`, token, { method: "POST" },
      );
      setNewInvitation(result.invite_code);
      setNotice("Invitation code regenerated. The previous code no longer works.");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function createOrder(groupId: string) {
    setBusy("order");
    setError("");
    setNotice("");
    try {
      const order = await call<Order>(
        `/funding/groups/${groupId}/paypal-order`, token, { method: "POST" },
      );
      // PayPal's trusted approval URL has already been validated by FastAPI.
      window.location.assign(order.approval_url);
    } catch (err) {
      setError(errorMessage(err));
      setBusy("");
    }
  }

  async function capture(groupId: string) {
    setBusy("capture");
    setError("");
    setNotice("");
    try {
      const updated = await call<Group>(
        `/funding/groups/${groupId}/paypal-capture`, token, { method: "POST" },
      );
      setNotice(updated.state === "funded"
        ? "All Sandbox captures verified. The group is funded in the test ledger."
        : "PayPal status checked. Only verified completed captures count as contributions.");
      await refresh();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  function useInvitationFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const value = params.get("invite");
    if (value) setInvite(value);
    else setError("No invitation code was found in this page URL.");
  }

  function copyInvite() {
    const share = `${window.location.origin}/app?invite=${encodeURIComponent(newInvitation)}`;
    void navigator.clipboard.writeText(share).then(
      () => setNotice("Invitation URL copied. It does not automatically accept or charge anyone."),
      () => setNotice(`Invite code: ${newInvitation}`),
    );
  }

  const eligibleNeeds = needs.filter(
    n => n.status === "open" && n.discoverable && n.intent?.shareable &&
      n.needed_from && n.needed_until && n.location_label,
  );

  return (
    <section id="funding" className="funding-panel" aria-labelledby="funding-title">
      <div className="funding-heading">
        <div>
          <span className="work-kicker">04 / PAYPAL SANDBOX</span>
          <h2 id="funding-title">Fund a shared possibility.</h2>
          <p>Invite real participants in the demo, receive explicit acceptance, then authorize individual Sandbox payments.</p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={Boolean(busy)}>
          {busy === "refresh" ? <LoaderCircle size={15} className="work-spinner" /> : <RefreshCcw size={15} />}
          Load groups and drafts
        </button>
      </div>
      <p className="funding-warning"><ShieldAlert size={18} /> Sandbox only. Contributions go to the merchant's test account, not escrow. No physical item is purchased, and no automatic refunds are promised.</p>
      <p className="funding-helper">
        After PayPal redirects back, this prototype requires signing in again.
        Load your groups and click <strong>Verify / capture approved payment</strong>.
        A return URL alone never marks a payment complete.
      </p>
      {error && <p className="work-error" role="alert">{error}</p>}
      {notice && <p className="work-notice" role="status"><CheckCircle2 size={15} /> {notice}</p>}
      <div className="funding-columns">
        <div className="funding-box">
          <span className="work-kicker">CREATE</span>
          <h3>Turn a draft into an invitation</h3>
          <p>Only current, unchanged Channel3 quotes with compatible potential matches can start a group.</p>
          {proposals === null ? <small>Load your saved drafts above.</small> : proposals.length === 0
            ? <small>No drafts are available yet. Make one from a real product search.</small>
            : proposals.map(p => (
              <article className="funding-proposal" key={p.id}>
                <strong>{p.product_title}</strong>
                <span>{p.price_display} · {p.prospective_members} proposed shares</span>
                <button type="button" disabled={Boolean(busy)} onClick={() => void createGroup(p.id)}>
                  Create Sandbox group <ArrowRight size={13} />
                </button>
                <small>Snapshot expires {new Date(p.quote_expires_at).toLocaleString()}</small>
              </article>
            ))}
          {newInvitation && (
            <div className="funding-invite">
              <strong>Share this invitation securely</strong>
              <code>{newInvitation}</code>
              <button type="button" onClick={copyInvite}><Clipboard size={14} /> Copy invitation URL</button>
              <small>Only a signed-in, compatible account may join. The code is only shown when created or rotated.</small>
            </div>
          )}
        </div>
        <div className="funding-box">
          <span className="work-kicker">JOIN</span>
          <h3>Accept a shared purchase invitation</h3>
          <p>Joining signals interest, but does not charge your PayPal account.</p>
          <label>Invitation code
            <input value={invite} onChange={e => setInvite(e.target.value)} placeholder="Paste the secure group code" />
          </label>
          <button className="funding-secondary" type="button" onClick={useInvitationFromUrl}>
            Use code from invitation link
          </button>
          <label>Which need would you use it for?
            <select value={selectedNeed} onChange={e => setSelectedNeed(e.target.value)}>
              <option value="">Choose your own matching need</option>
              {eligibleNeeds.map(n => (
                <option value={n.id} key={n.id}>{n.request_text.slice(0, 95)}</option>
              ))}
            </select>
          </label>
          {eligibleNeeds.length === 0 && <small>Add and analyze a need, opt into discovery, and set non-overlapping usage dates first.</small>}
          <button className="funding-main" type="button" disabled={Boolean(busy) || !invite || !selectedNeed} onClick={() => void joinGroup()}>
            <Users size={15} /> Join without paying
          </button>
        </div>
      </div>
      {groups && (
        <section className="funding-group-list">
          <h3>Your accepted groups</h3>
          {groups.length === 0 && <p>No groups joined yet.</p>}
          {groups.map(group => {
            const mine = group.members.find(m => m.is_you);
            return (
              <article className="funding-group" key={group.id}>
                <div className="funding-group-title">
                  <div><span className="funding-state">{group.state.replace("_", " ")}</span><h4>{group.product_title}</h4></div>
                  <strong>{group.captured_display} <small>/ {group.total_display} verified</small></strong>
                </div>
                <p>{group.accepted_count} / {group.target_members} participants accepted · closes {new Date(group.expires_at).toLocaleString()}</p>
                <div className="funding-ledger" aria-label="Anonymized funding ledger">
                  {Array.from({ length: group.target_members }, (_, i) => {
                    const entry = group.members.find(m => m.slot === i + 1);
                    return (
                      <div key={i} className={entry?.payment_state === "completed" ? "paid" : ""}>
                        <span>{entry ? (entry.is_you ? "You" : `Member ${entry.slot}`) : `Open spot ${i + 1}`}</span>
                        <strong>{entry?.share_display || "Unassigned"}</strong>
                        <small>{entry?.payment_state.replace("_", " ") || "Not accepted"}</small>
                      </div>
                    );
                  })}
                </div>
                {group.state === "recruiting" && mine?.slot === 1 && (
                  <button type="button" className="funding-secondary" disabled={Boolean(busy)}
                    onClick={() => void rotate(group.id)}>
                    Regenerate invitation code
                  </button>
                )}
                {group.state === "funding" && mine && (
                  <div className="funding-group-ctas">
                    {["not_started", "creating", "awaiting_approval"].includes(mine.payment_state) && (
                      <button type="button" className="funding-main" disabled={Boolean(busy)}
                        onClick={() => void createOrder(group.id)}>
                        <CreditCard size={16} /> {mine.payment_state === "awaiting_approval" ? "Continue PayPal approval" : "Approve my share in PayPal Sandbox"}
                        <ExternalLink size={14} />
                      </button>
                    )}
                    {["awaiting_approval", "capture_pending"].includes(mine.payment_state) && (
                      <button type="button" className="funding-secondary" disabled={Boolean(busy)}
                        onClick={() => void capture(group.id)}>
                        <RefreshCcw size={14} /> Verify / capture approved payment
                      </button>
                    )}
                  </div>
                )}
                {group.state === "funded" && <p className="funding-success"><CheckCircle2 size={15} /> All captures independently verified in Sandbox. No physical fulfillment is implied.</p>}
                {group.state === "needs_review" && <p className="funding-warning">Payment or eligibility changed. Further charges are blocked pending manual review; no refunds are initiated automatically.</p>}
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
}
