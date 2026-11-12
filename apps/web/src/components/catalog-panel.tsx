"use client";

import { useState } from "react";
import { ArrowUpRight, CheckCircle2, LoaderCircle, Search, ShoppingBasket, ShieldAlert } from "lucide-react";

type Offer = {
  domain: string;
  url: string;
  currency: string;
  price_minor: number;
  price_display: string;
};
type Product = {
  id: string;
  title: string;
  brand: string | null;
  image_url: string | null;
  description: string | null;
  offers: Offer[];
  required_features_unverified: string[];
  excluded_features_detected: string[];
  suitability: "candidate" | "manual_review" | "blocked";
};
type ProductResults = { provider: string; query: string; currency: string; country: string; notice: string; checked_at: string; products: Product[] };
type Draft = {
  id: string;
  product_title: string;
  product_image_url: string | null;
  merchant_domain: string;
  merchant_url: string;
  price_display: string;
  currency: string;
  prospective_members: number;
  member_shares_display: string[];
  hypothetical_savings_display: string;
  quote_expires_at: string;
  disclaimer: string;
};
type ErrorData = { error?: { message?: string } };

const origin = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function authenticated<T>(path: string, token: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${origin}/api/v1${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  const body = (await response.json().catch(() => null)) as (T & ErrorData) | null;
  if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status})`);
  return body as T;
}

export function CatalogPanel({ needId, token, potentialMembers }: {
  needId: string;
  token: string;
  potentialMembers: number | null;
}) {
  const [loading, setLoading] = useState(false);
  const [quoting, setQuoting] = useState(false);
  const [results, setResults] = useState<ProductResults | null>(null);
  const [offerUrls, setOfferUrls] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState("");

  async function discover() {
    setLoading(true);
    setError("");
    setDraft(null);
    try {
      const data = await authenticated<ProductResults>(
        `/needs/${needId}/products/search`,
        token,
        { method: "POST" },
      );
      setResults(data);
      setOfferUrls({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to retrieve Channel3 products.");
    } finally {
      setLoading(false);
    }
  }

  async function draftProposal(product: Product) {
    const offerUrl = offerUrls[product.id] || product.offers[0]?.url;
    if (!offerUrl) return;
    setQuoting(true);
    setError("");
    setDraft(null);
    try {
      const data = await authenticated<Draft>(
        `/needs/${needId}/proposals`,
        token,
        { method: "POST", body: JSON.stringify({ product_id: product.id, offer_url: offerUrl }) },
      );
      setDraft(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create a verified draft quote.");
    } finally {
      setQuoting(false);
    }
  }

  return (
    <section className="catalog-panel" aria-label="Real product discovery">
      <div className="catalog-heading">
        <div><strong><ShoppingBasket size={15} /> Real catalog discovery</strong><p>Channel3 · actual product and merchant offers</p></div>
        <button className="catalog-discover-button" type="button" disabled={loading || quoting} onClick={() => void discover()}>
          {loading ? <LoaderCircle className="work-spinner" size={15} /> : <Search size={15} />}
          {loading ? "Searching..." : "Find products"}
        </button>
      </div>
      {error && <p className="work-error" role="alert">{error} {error.includes("503") ? "Check CHANNEL3_API_KEY on the backend." : ""}</p>}
      {results && (
        <div className="catalog-results">
          <p className="catalog-context">
            Channel3 results for <strong>{results.query}</strong> · {results.country} / {results.currency}
          </p>
          <p className="catalog-disclaimer"><ShieldAlert size={14} /> {results.notice}</p>
          {results.products.length === 0 ? (
            <p className="catalog-none">No in-stock, correctly priced merchant offers were returned. No substitute items have been invented.</p>
          ) : (
            results.products.map(product => (
              <article className="catalog-product" key={product.id}>
                {product.image_url && (
                  // The merchant image domain is supplied by Channel3 and is not known at build time.
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image_url} alt={product.title} width="72" height="72" loading="lazy" />
                )}
                <div className="catalog-product-body">
                  <strong>{product.title}</strong>
                  <span>{product.brand || "Brand unavailable"} · {product.offers.length} in-stock {product.offers.length === 1 ? "offer" : "offers"}</span>
                  {product.required_features_unverified.length > 0 && (
                    <p className="catalog-warning">Unverified requirements: {product.required_features_unverified.join(", ")}</p>
                  )}
                  {product.excluded_features_detected.length > 0 && (
                    <p className="catalog-warning">Possible exclusion: {product.excluded_features_detected.join(", ")}</p>
                  )}
                  <label className="catalog-offer-label">Merchant offer
                    <select
                      value={offerUrls[product.id] || product.offers[0]?.url || ""}
                      onChange={event => setOfferUrls(current => ({ ...current, [product.id]: event.target.value }))}
                    >
                      {product.offers.map(offer => (
                        <option key={offer.url} value={offer.url}>{offer.domain} · {offer.price_display}</option>
                      ))}
                    </select>
                  </label>
                  <div className="catalog-cta">
                    <a href={offerUrls[product.id] || product.offers[0]?.url} target="_blank" rel="noopener noreferrer">
                      View retailer <ArrowUpRight size={13} />
                    </a>
                    <button
                      type="button"
                      disabled={quoting || product.suitability !== "candidate" || potentialMembers === null || potentialMembers < 1}
                      onClick={() => void draftProposal(product)}
                      title={potentialMembers === null || potentialMembers < 1 ? "Find another opted-in member before making a draft" : "Create an unapproved quote"}
                    >
                      {quoting ? <LoaderCircle className="work-spinner" size={13} /> : <CheckCircle2 size={13} />}
                      Save draft quote
                    </button>
                  </div>
                  {product.suitability === "candidate" && (
                    <small>Candidate based on catalog text; physical specifications require buyer verification.</small>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      )}
      {potentialMembers === null && <p className="catalog-tip">Run Find potential matches first to enable a draft cost-sharing quote.</p>}
      {potentialMembers === 0 && <p className="catalog-tip">No matched member yet, so draft cost-sharing is disabled.</p>}
      {draft && (
        <article className="catalog-draft" role="status">
          <span className="work-kicker">SAVED · UNAPPROVED DRAFT</span>
          <h4>{draft.product_title}</h4>
          <div className="catalog-draft-metrics">
            <div><span>Merchant quote</span><strong>{draft.price_display}</strong></div>
            <div><span>Potential people</span><strong>{draft.prospective_members}</strong></div>
            <div><span>Hypothetical savings</span><strong>{draft.hypothetical_savings_display}</strong></div>
          </div>
          <p>Proposed shares: {draft.member_shares_display.join(" + ")} = {draft.price_display}</p>
          <p className="catalog-disclaimer">{draft.disclaimer}</p>
          <small>Quote snapshot expires {new Date(draft.quote_expires_at).toLocaleString()}.</small>
        </article>
      )}
    </section>
  );
}

export function ProposalHistory({ token }: { token: string }) {
  const [list, setList] = useState<Draft[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    setBusy(true);
    setError("");
    try {
      const data = await authenticated<{ proposals: Draft[] }>("/proposals", token, {});
      setList(data.proposals);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retrieve proposals.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="catalog-history" aria-label="Saved draft quotes">
      <div className="catalog-history-top">
        <div><span className="work-kicker">02 / COST SHARING</span><h2>Saved draft quotes</h2></div>
        <button type="button" disabled={busy} onClick={() => void refresh()}>
          {busy ? <LoaderCircle className="work-spinner" size={14} /> : <Search size={14} />} Load saved drafts
        </button>
      </div>
      <p>These are persisted Channel3 price snapshots, not payments, reservations, or agreements.</p>
      {error && <p className="work-error" role="alert">{error}</p>}
      {list && (list.length ? (
        <div className="catalog-history-list">
          {list.map(item => (
            <article key={item.id}>
              <strong>{item.product_title}</strong>
              <span>{item.merchant_domain} · {item.price_display} · {item.prospective_members} prospective people</span>
              <small>Shares: {item.member_shares_display.join(" + ")} · Expires {new Date(item.quote_expires_at).toLocaleString()}</small>
            </article>
          ))}
        </div>
      ) : <p>No draft quotes saved yet.</p>)}
    </section>
  );
}
