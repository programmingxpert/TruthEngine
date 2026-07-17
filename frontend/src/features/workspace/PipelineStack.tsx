import { Terminal, Download, Play, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import type { EvidenceGraph, Investigation, InvestigationPlan, TimelineEvent } from "../../core/api";

interface PipelineStackProps {
  investigation: Investigation;
  plan?: InvestigationPlan;
  events: TimelineEvent[];
  graph?: EvidenceGraph;
  onInspectArtifact: (title: string, data: any) => void;
}

interface AgentWorker {
  id: string;
  name: string;
  description: string;
  status: "COMPLETED" | "ACTIVE" | "QUEUED" | "FAILED";
  duration: string;
  artifactName?: string;
  artifactData?: any;
  logs: string[];
}

export function PipelineStack({
  investigation,
  plan,
  events,
  graph,
  onInspectArtifact,
}: PipelineStackProps) {
  // Construct agent status mapping based on current workflow status
  const currentStatus = investigation.status;

  const getStatus = (stage: string): AgentWorker["status"] => {
    if (currentStatus === "COMPLETED") return "COMPLETED";
    if (currentStatus === "FAILED") return "FAILED";

    switch (stage) {
      case "planner":
        return currentStatus === "CREATED" ? "ACTIVE" : "COMPLETED";
      case "research":
        return currentStatus === "COLLECTING_SOURCES" ? "ACTIVE" : currentStatus === "CREATED" ? "QUEUED" : "COMPLETED";
      case "segmenter":
        return currentStatus === "COLLECTING_SOURCES" ? "ACTIVE" : currentStatus === "CREATED" ? "QUEUED" : "COMPLETED";
      case "extractor":
        return currentStatus === "ANALYZING" ? "ACTIVE" : ["CREATED", "COLLECTING_SOURCES"].includes(currentStatus) ? "QUEUED" : "COMPLETED";
      case "matcher":
        return currentStatus === "ANALYZING" ? "ACTIVE" : ["CREATED", "COLLECTING_SOURCES"].includes(currentStatus) ? "QUEUED" : "COMPLETED";
      case "contradiction":
        return currentStatus === "ANALYZING" ? "ACTIVE" : ["CREATED", "COLLECTING_SOURCES"].includes(currentStatus) ? "QUEUED" : "COMPLETED";
      case "calibration":
        return currentStatus === "GENERATING_REPORT" ? "ACTIVE" : ["CREATED", "COLLECTING_SOURCES", "ANALYZING"].includes(currentStatus) ? "QUEUED" : "COMPLETED";
      case "dossier":
        return currentStatus === "GENERATING_REPORT" ? "ACTIVE" : ["CREATED", "COLLECTING_SOURCES", "ANALYZING"].includes(currentStatus) ? "QUEUED" : "COMPLETED";
      default:
        return "QUEUED";
    }
  };

  const eventMessages = (types: string[]) =>
    events
      .filter((evt) => types.some((type) => evt.event_type.includes(type)))
      .map((evt) => evt.description);

  const sourceEvents = events.filter((evt) => evt.event_type === "SOURCE_INGESTED");
  const passageEvent = [...events].reverse().find((evt) => evt.event_type === "PASSAGES_SELECTED");
  const analysisEvent = [...events].reverse().find((evt) => evt.event_type === "ANALYSIS_COMPLETED");
  const verdictEvent = [...events].reverse().find((evt) => evt.event_type === "VERDICT_GENERATED");

  const agents: AgentWorker[] = [
    {
      id: "planner",
      name: "1. Investigation Planner",
      description: "Generates investigation plans, required proof indices, and search categories.",
      status: getStatus("planner"),
      duration: "120ms",
      artifactName: "investigation_plan.json",
      artifactData: plan || { message: "No plan generated yet" },
      logs: eventMessages(["PLAN"]).length
        ? eventMessages(["PLAN"])
        : ["Waiting for plan generation."],
    },
    {
      id: "research",
      name: "2. Research & Discovery Agent",
      description: "Discovers and crawls target URLs securely guarding against SSRF.",
      status: getStatus("research"),
      duration: "1.2s",
      artifactName: "coverage_report.json",
      artifactData: {
        crawled_domains: sourceEvents.map((evt) => evt.metadata?.domain).filter(Boolean),
        source_count: sourceEvents.length,
      },
      logs: eventMessages(["SEARCH", "SOURCE", "INGESTION"]).length
        ? eventMessages(["SEARCH", "SOURCE", "INGESTION"])
        : ["Waiting for search and crawl results."],
    },
    {
      id: "segmenter",
      name: "3. Document Segmenter",
      description: "Normalizes snapshots and parses layout paragraphs mapping active headers.",
      status: getStatus("segmenter"),
      duration: "340ms",
      artifactName: "document_segments.json",
      artifactData: passageEvent?.metadata || { message: "No segment artifacts yet" },
      logs: eventMessages(["PASSAGE"]).length
        ? eventMessages(["PASSAGE"])
        : ["Waiting for segmentation and candidate selection."],
    },
    {
      id: "extractor",
      name: "4. Claim Extractor",
      description: "Scans segments to parse clean factual claims.",
      status: getStatus("extractor"),
      duration: "650ms",
      artifactName: "extracted_claims.json",
      artifactData: { claims_parsed: graph?.claims.length || 0, claims: graph?.claims || [] },
      logs: analysisEvent
        ? [analysisEvent.description]
        : eventMessages(["ANALYSIS", "BLOCKED", "SKIPPED"]),
    },
    {
      id: "matcher",
      name: "5. Evidence Matcher",
      description: "Compares claims against passages executing lexical ranking matching.",
      status: getStatus("matcher"),
      duration: "450ms",
      artifactName: "evidence_mapping.json",
      artifactData: { relations_linked: graph?.relations.length || 0, relations: graph?.relations || [] },
      logs: analysisEvent ? [analysisEvent.description] : ["Waiting for evidence mapping."],
    },
    {
      id: "contradiction",
      name: "6. Contradiction Agent",
      description: "Identifies conflicts and opposing arguments between independent citations.",
      status: getStatus("contradiction"),
      duration: "210ms",
      artifactName: "contradiction_report.json",
      artifactData: {
        contradictions_found: graph?.relations.filter((rel) => rel.relation_type === "CONTRADICTS").length || 0,
      },
      logs: graph
        ? [`Contradicting relations: ${graph.relations.filter((rel) => rel.relation_type === "CONTRADICTS").length}`]
        : ["Waiting for contradiction detection."],
    },
    {
      id: "calibration",
      name: "7. Confidence Calibration Agent",
      description: "Calculates support ratios and outputs confidence values.",
      status: getStatus("calibration"),
      duration: "80ms",
      artifactName: "confidence_log.json",
      artifactData: verdictEvent?.metadata || { message: "No confidence calculation yet" },
      logs: verdictEvent ? [verdictEvent.description] : ["Waiting for algorithmic confidence calculation."],
    },
  ];

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto w-full">
      <div className="flex items-center space-x-2 border-b border-border pb-3">
        <Terminal className="w-4 h-4 text-brand" />
        <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          Agent Reasoning Pipeline Execution Stack
        </h2>
      </div>

      <div className="space-y-4">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className={`p-5 rounded-xl border transition-all ${
              agent.status === "ACTIVE"
                ? "border-brand bg-brand/5 shadow-md shadow-brand/5"
                : agent.status === "COMPLETED"
                ? "border-slate-800 bg-slate-900/30"
                : agent.status === "FAILED"
                ? "border-danger/30 bg-danger/5"
                : "border-slate-800/40 bg-slate-950/10 opacity-60"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                {agent.status === "COMPLETED" && (
                  <CheckCircle2 className="w-5 h-5 text-success shrink-0" />
                )}
                {agent.status === "ACTIVE" && (
                  <Loader2 className="w-5 h-5 text-brand animate-spin shrink-0" />
                )}
                {agent.status === "FAILED" && (
                  <AlertCircle className="w-5 h-5 text-danger shrink-0" />
                )}
                {agent.status === "QUEUED" && (
                  <Play className="w-5 h-5 text-slate-650 shrink-0" />
                )}
                <div>
                  <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{agent.description}</p>
                </div>
              </div>

              {agent.status === "COMPLETED" && agent.artifactName && (
                <button
                  onClick={() => onInspectArtifact(agent.artifactName!, agent.artifactData)}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-border text-[10px] font-mono text-slate-300 hover:text-white flex items-center space-x-1 transition-colors"
                >
                  <Download className="w-3 h-3" />
                  <span>Inspect Artifact</span>
                </button>
              )}
            </div>

            {/* Monospace log ticker */}
            {["ACTIVE", "COMPLETED", "FAILED"].includes(agent.status) && (
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-900 font-mono text-[10px] leading-relaxed text-slate-400 space-y-1 overflow-x-auto">
                {agent.logs.map((log, idx) => (
                  <div key={idx} className="flex space-x-2">
                    <span className="text-slate-600 shrink-0 select-none">[{idx + 1}]</span>
                    <span className="break-all">{log}</span>
                  </div>
                ))}
                {agent.status === "ACTIVE" && (
                  <div className="flex items-center space-x-1.5 text-brand animate-pulse mt-1 select-none">
                    <span>█</span>
                    <span>Agent working...</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
