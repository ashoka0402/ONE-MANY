"use client";

import { useMemo, useRef } from "react";
import {
  AllCommunityModule, themeQuartz,
  type ColDef,
} from "ag-grid-community";
import { AgGridProvider, AgGridReact } from "ag-grid-react";
import { Download, History, Users } from "lucide-react";

export type MemberRow = {
  slot: number;
  is_you: boolean;
  share_minor: number;
  share_display: string;
  captured_minor: number;
  captured_display: string;
  payment_state: string;
  last_updated_at: string | null;
};
export type AuditRow = {
  id: string;
  recorded_at: string;
  event_type: string;
  source: string;
  member_slot: number | null;
  amount_minor: number;
  amount_display: string;
};

const modules = [AllCommunityModule];

const ledgerTheme = themeQuartz.withParams({
  accentColor: "#87e8b5",
  backgroundColor: "#11251b",
  foregroundColor: "#e4f6e9",
  headerBackgroundColor: "#203a2b",
  borderColor: "#355340",
  rowHoverColor: "#294a36",
  fontFamily: "inherit",
  fontSize: 12,
});

const label = (word: string) => word.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());

function localTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const timestamp = new Date(value);
  return Number.isNaN(timestamp.getTime()) ? "—" : timestamp.toLocaleString();
}

export function AgLedgerGrid({ members, events, groupId, demo = false }: {
  members: MemberRow[];
  events: AuditRow[];
  groupId: string;
  /** Fictional client-only data. Never label it as verified PayPal records. */
  demo?: boolean;
}) {
  const membersRef = useRef<AgGridReact<MemberRow>>(null);
  const eventsRef = useRef<AgGridReact<AuditRow>>(null);
  const baseColumn = useMemo<ColDef>(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    minWidth: 116,
    flex: 1,
  }), []);
  const memberCols = useMemo<ColDef<MemberRow>[]>(() => [
    {
      headerName: "Participant",
      field: "slot",
      minWidth: 142,
      valueFormatter: ({ data }) =>
        data?.is_you ? "You · Member " + data.slot : "Member " + (data?.slot ?? "—"),
    },
    {
      headerName: "Payment state",
      field: "payment_state",
      minWidth: 150,
      valueFormatter: ({ value }) => label(String(value ?? "not_started")),
      cellClassRules: {
        "ledger-paid-cell": p => p.value === "completed",
        "ledger-review-cell": p => ["reversed", "needs_review"].includes(String(p.value)),
      },
    },
    {
      headerName: "Accepted share",
      field: "share_minor",
      minWidth: 148,
      type: "numericColumn",
      valueFormatter: ({ data }) => data?.share_display ?? "—",
    },
    {
      headerName: demo ? "Simulated captured" : "Verified capture",
      field: "captured_minor",
      minWidth: 158,
      type: "numericColumn",
      valueFormatter: ({ data }) => data?.captured_display ?? "—",
    },
    {
      headerName: "Last recorded update",
      field: "last_updated_at",
      minWidth: 188,
      valueFormatter: ({ value }) => localTimestamp(value as string | null),
    },
  ], [demo]);
  const eventCols = useMemo<ColDef<AuditRow>[]>(() => [
    {
      headerName: "Recorded at",
      field: "recorded_at",
      minWidth: 185,
      valueFormatter: ({ value }) => localTimestamp(value as string),
    },
    {
      headerName: "Event",
      field: "event_type",
      minWidth: 182,
      valueFormatter: ({ value }) => label(String(value ?? "")),
    },
    {
      headerName: "Participant",
      field: "member_slot",
      minWidth: 130,
      valueFormatter: ({ value }) => value == null ? "Group" : "Member " + value,
    },
    {
      headerName: "Recorded source",
      field: "source",
      minWidth: 164,
      valueFormatter: ({ value }) => demo || value === "demo_fictional"
        ? "Fictional demo — no API" : value === "paypal_verified"
        ? "Verified PayPal webhook" : "Backend",
    },
    {
      headerName: "Affected share",
      field: "amount_minor",
      minWidth: 136,
      type: "numericColumn",
      valueFormatter: ({ data }) => data?.amount_display ?? "—",
    },
  ], [demo]);
  return (
    <AgGridProvider modules={modules}>
      <div className="ledger-grid-block">
        <div className="ledger-grid-header">
          <div><Users size={16} /><strong>{demo ? "Fictional participant contributions" : "Participant contributions"}</strong><span>{members.length} participants</span></div>
          <button type="button" onClick={() =>
            membersRef.current?.api.exportDataAsCsv({
              fileName: `${demo ? "FICTIONAL-DEMO" : "one-many"}-members-${groupId.slice(0, 8)}.csv`,
            })
          }>
            <Download size={14} /> Export anonymous CSV
          </button>
        </div>
        <div className="ledger-ag-grid" aria-label="Anonymous participant contribution ledger">
          <AgGridReact<MemberRow>
            ref={membersRef}
            theme={ledgerTheme}
            columnDefs={memberCols}
            defaultColDef={baseColumn}
            rowData={members}
            getRowId={p => String(p.data.slot)}
            suppressMovableColumns={true}
            animateRows={false}
            pagination={true}
            paginationPageSize={10}
            paginationPageSizeSelector={[10, 20, 50]}
            domLayout="normal"
          />
        </div>
        <div className="ledger-grid-header ledger-grid-audit-title">
          <div><History size={16} /><strong>{demo ? "Fictional event history" : "Recorded audit events"}</strong><span>{events.length} shown</span></div>
          <button type="button" onClick={() =>
            eventsRef.current?.api.exportDataAsCsv({
              fileName: `${demo ? "FICTIONAL-DEMO" : "one-many"}-audit-${groupId.slice(0, 8)}.csv`,
            })
          }>
            <Download size={14} /> Export event CSV
          </button>
        </div>
        <div className="ledger-ag-grid ledger-ag-grid-history" aria-label="Recorded contribution event history">
          <AgGridReact<AuditRow>
            ref={eventsRef}
            theme={ledgerTheme}
            columnDefs={eventCols}
            defaultColDef={baseColumn}
            rowData={events}
            getRowId={p => p.data.id}
            suppressMovableColumns={true}
            animateRows={false}
            pagination={true}
            paginationPageSize={10}
            paginationPageSizeSelector={[10, 20, 50]}
          />
        </div>
      </div>
    </AgGridProvider>
  );
}
