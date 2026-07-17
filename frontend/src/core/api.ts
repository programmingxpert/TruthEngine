/**
 * TruthEngine API client.
 *
 * Backend schemas stay domain-oriented. This client normalizes them into the
 * shape expected by the existing frontend components without changing the UI.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type InvestigationStatus =
  | "CREATED"
  | "QUEUED"
  | "RUNNING"
  | "COLLECTING_SOURCES"
  | "ANALYZING"
  | "GENERATING_REPORT"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface Investigation {
  id: string;
  investigation_id: string;
  query: string;
  status: InvestigationStatus;
  created_at: string;
  updated_at: string;
}

export interface InvestigationPlan {
  investigation_id: string;
  detected_domain: string;
  objective: string;
  assumptions: string[];
  required_evidence_categories: string[];
  preferred_source_categories: string[];
  excluded_source_categories: string[];
  retrieval_strategy: string;
  success_criteria: string[];
  limitations: string[];
  planning_timestamp: string;
  planner_version: string;
}

export interface TimelineEvent {
  id: string;
  investigation_id: string;
  stage: string;
  event_type: string;
  title: string;
  description: string;
  occurred_at: string;
  metadata: Record<string, any>;
}

export interface CandidatePassage {
  passage_id: string;
  investigation_id: string;
  segment_id: string;
  snapshot_version: number;
  algorithm_version: string;
  paragraph_order: number;
  selection_explanation: {
    lexical_score: number;
    selection_algorithm_version: string;
    matched_query_terms: string[];
    matched_heading: string | null;
    matched_domain_rules: string[];
  };
  selected_at: string;
  content?: string;
  heading?: string;
  snapshot_title?: string;
}

export interface Claim {
  id: string;
  claim_text: string;
  claim_type: string;
  status: "UNVERIFIED" | "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT_EVIDENCE";
  extracted_at: string;
}

export interface EvidenceItem {
  id: string;
  snapshot_id: string | null;
  passage_text: string;
  url: string;
  title: string;
  source_category: string;
  publisher: string;
  extracted_at: string;
}

export interface EvidenceRelation {
  id: string;
  claim_id: string;
  evidence_item_id: string;
  relation_type: "SUPPORTS" | "CONTRADICTS" | "NEUTRAL";
  analysis_reasoning: string;
  confidence_score: number;
  mapped_at: string;
}

export interface EvidenceGraph {
  id: string;
  investigation_id: string;
  version: number;
  created_at: string;
  claims: Claim[];
  evidence_items: EvidenceItem[];
  relations: EvidenceRelation[];
}

export interface FetchResult {
  url: string;
  fetched_at: string;
  success: boolean;
  http_status: number | null;
  content_type: string;
  title: string;
  extracted_text: string;
  content_length: number | null;
  fetch_duration_ms: number;
  etag: string | null;
  last_modified: string | null;
  encoding: string | null;
  error_type: string | null;
  error_message: string | null;
  snapshot_version: number;
}

async function requestRaw<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData?.error?.message || errorData?.message;
    throw new Error(message || `API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

function normalizeInvestigation(raw: any): Investigation {
  const id = raw.investigation_id || raw.id;
  return {
    ...raw,
    id,
    investigation_id: id,
  };
}

function deriveStage(eventType: string): string {
  if (eventType.includes("PLAN")) return "planner";
  if (eventType.includes("SEARCH") || eventType.includes("SOURCE")) return "search";
  if (eventType.includes("INGESTION")) return "crawler";
  if (eventType.includes("PASSAGE")) return "segmentation";
  if (eventType.includes("ANALYSIS") || eventType.includes("CLAIM") || eventType.includes("EVIDENCE")) {
    return "analysis";
  }
  if (eventType.includes("VERDICT")) return "verdict";
  if (eventType.includes("WORKFLOW")) return "workflow";
  return "system";
}

function normalizeTimelineEvent(raw: any): TimelineEvent {
  return {
    id: raw.id,
    investigation_id: raw.investigation_id,
    stage: raw.stage || deriveStage(raw.event_type || ""),
    event_type: raw.event_type,
    title: raw.title || raw.event_type,
    description: raw.description || raw.message || "",
    occurred_at: raw.occurred_at || raw.created_at,
    metadata: raw.metadata || {},
  };
}

function normalizeClaim(raw: any): Claim {
  const statusMap: Record<string, Claim["status"]> = {
    VERIFIED: "SUPPORTED",
    REFUTED: "CONTRADICTED",
    UNVERIFIED: "UNVERIFIED",
  };
  return {
    id: raw.id,
    claim_text: raw.claim_text || raw.text,
    claim_type: raw.claim_type,
    status: statusMap[raw.status] || "UNVERIFIED",
    extracted_at: raw.extracted_at || new Date().toISOString(),
  };
}

function normalizeEvidenceItem(raw: any): EvidenceItem {
  let publisher = "source";
  try {
    publisher = new URL(raw.location || raw.url).hostname;
  } catch {
    publisher = raw.location || "source";
  }
  return {
    id: raw.id,
    snapshot_id: raw.snapshot_id || raw.source_snapshot_id || null,
    passage_text: raw.passage_text || raw.quote,
    url: raw.url || raw.location,
    title: raw.title || publisher,
    source_category: raw.source_category || "GENERAL",
    publisher,
    extracted_at: raw.extracted_at,
  };
}

function normalizeRelation(raw: any): EvidenceRelation {
  return {
    id: raw.id,
    claim_id: raw.claim_id,
    evidence_item_id: raw.evidence_item_id,
    relation_type:
      raw.relation_type === "SUPPORTS" || raw.relation_type === "CONTRADICTS"
        ? raw.relation_type
        : "NEUTRAL",
    analysis_reasoning: raw.analysis_reasoning || "",
    confidence_score: raw.confidence_score || 0,
    mapped_at: raw.mapped_at || new Date().toISOString(),
  };
}

function normalizeGraph(raw: any): EvidenceGraph {
  const relations = (raw.relations || []).map(normalizeRelation);
  const claims = (raw.claims || []).map(normalizeClaim).map((claim: Claim) => {
    const claimRelations = relations.filter((relation: EvidenceRelation) => relation.claim_id === claim.id);
    if (claimRelations.some((relation: EvidenceRelation) => relation.relation_type === "CONTRADICTS")) {
      return { ...claim, status: "CONTRADICTED" as const };
    }
    if (claimRelations.some((relation: EvidenceRelation) => relation.relation_type === "SUPPORTS")) {
      return { ...claim, status: "SUPPORTED" as const };
    }
    return claim;
  });

  return {
    id: raw.id || raw.graph_id,
    investigation_id: raw.investigation_id,
    version: raw.version,
    created_at: raw.created_at,
    claims,
    evidence_items: (raw.evidence_items || []).map(normalizeEvidenceItem),
    relations,
  };
}

export const api = {
  getInvestigations: async () => {
    const data = await requestRaw<any[]>("/investigations");
    return data.map(normalizeInvestigation);
  },
  getInvestigation: async (id: string) => {
    const data = await requestRaw<any>(`/investigations/${id}`);
    return normalizeInvestigation(data);
  },
  createInvestigation: async (query: string) => {
    const data = await requestRaw<any>("/investigations", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
    return normalizeInvestigation(data);
  },
  runInvestigation: async (id: string) => {
    const data = await requestRaw<any>(`/investigations/${id}/run`, {
      method: "POST",
    });
    return normalizeInvestigation(data);
  },
  deleteInvestigation: (id: string) =>
    requestRaw<void>(`/investigations/${id}`, {
      method: "DELETE",
    }),
  getPlan: (id: string) => requestRaw<InvestigationPlan>(`/investigations/${id}/plan`),
  generatePlan: (id: string) =>
    requestRaw<InvestigationPlan>(`/investigations/${id}/plan`, {
      method: "POST",
    }),
  getTimeline: async (id: string) => {
    const data = await requestRaw<any[]>(`/investigations/${id}/timeline`);
    return data.map(normalizeTimelineEvent);
  },
  getCandidates: (id: string) =>
    requestRaw<CandidatePassage[]>(`/investigations/${id}/candidates`),
  selectCandidates: (id: string) =>
    requestRaw<CandidatePassage[]>(`/investigations/${id}/candidates`, {
      method: "POST",
    }),
  ingestUrl: (url: string) =>
    requestRaw<FetchResult>("/sources/ingest", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  getLatestGraph: async (id: string) => {
    const data = await requestRaw<any>(`/investigations/${id}/graphs/latest`);
    return normalizeGraph(data);
  },
  getGraph: async (graphId: string) => {
    const data = await requestRaw<any>(`/graphs/${graphId}`);
    return normalizeGraph(data);
  },
};
