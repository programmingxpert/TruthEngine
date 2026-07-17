import { ShieldCheck, ShieldAlert, Award, FileText, ArrowRight, Activity, Calendar, Loader2, CheckCircle2, Compass, Search, Database, Brain, Scale } from "lucide-react";
import type { EvidenceGraph, Investigation, InvestigationPlan, TimelineEvent } from "../../core/api";

interface VerdictSummaryProps {
  investigation: Investigation;
  plan?: InvestigationPlan;
  graph?: EvidenceGraph;
  events: TimelineEvent[];
  onInspect: () => void;
  isCompleted: boolean;
}

export function VerdictSummary({ investigation, plan, graph, events, onInspect }: VerdictSummaryProps) {
  const isFailed = investigation.status === "FAILED";
  const isCompleted = investigation.status === "COMPLETED";
  const isRunning = !isCompleted && !isFailed && investigation.status !== "CANCELLED";

  // Find verdict event if available
  const verdictEvent = [...events].reverse().find((evt) => evt.event_type === "VERDICT_GENERATED");
  const verdict = verdictEvent?.metadata?.verdict || (isFailed ? "FAILED" : "PENDING");
  const confidence = verdictEvent?.metadata?.confidence ?? 0;
  
  // Calculate source count from ingested events
  const ingestedEvents = events.filter((evt) => evt.event_type === "SOURCE_INGESTED");
  const sourceCount = ingestedEvents.length;

  const supporting = graph?.relations.filter((rel) => rel.relation_type === "SUPPORTS").length || 0;
  const contradicted = graph?.relations.filter((rel) => rel.relation_type === "CONTRADICTS").length || 0;
  const unverified = Math.max((graph?.claims.length || 0) - supporting - contradicted, 0);
  const total = Math.max(supporting + contradicted + unverified, 1);
  const supportedRatio = Math.round((supporting / total) * 100);
  const contradictedRatio = Math.round((contradicted / total) * 100);
  const unverifiedRatio = Math.max(0, 100 - supportedRatio - contradictedRatio);

  const explanation =
    verdictEvent?.metadata?.explanation ||
    (isFailed
      ? "The investigation did not complete. Inspect the timeline or logs for details."
      : "The investigation is still actively collecting and evaluating evidence.");

  const verdictBg =
    verdict === "FALSE" || isFailed
      ? "bg-red-500/10 border-red-500/30 text-red-400"
      : verdict === "TRUE"
      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
      : "bg-amber-500/10 border-amber-500/30 text-amber-400";

  // -------------------------------------------------------------
  // Live Pipeline Stage calculation
  // -------------------------------------------------------------
  const hasPlan = !!plan || events.some((e) => e.event_type === "PLAN_GENERATED");
  const hasSearch = events.some((e) => e.event_type === "SEARCH_COMPLETED");
  const hasIngest = events.some((e) => e.event_type === "INGESTION_COMPLETED");
  const hasPassages = events.some((e) => e.event_type === "PASSAGES_SELECTED");
  const hasAnalysis = events.some((e) => e.event_type === "ANALYSIS_COMPLETED");
  const hasVerdict = events.some((e) => e.event_type === "VERDICT_GENERATED");

  // Calculate source count from ingested events
  const ingestedEvents = events.filter((evt) => evt.event_type === "SOURCE_INGESTED");
  const sourceCount = ingestedEvents.length;
  const ingestedDomains = ingestedEvents
    .map((e) => e.metadata?.domain || e.metadata?.publisher || "unknown")
    .filter((d, i, arr) => arr.indexOf(d) === i);

  const steps = [
    {
      id: "plan",
      label: "Strategic Planning",
      desc: "Detect domain & outline objectives",
      icon: Compass,
      status: hasPlan ? "completed" : isRunning && !hasPlan ? "active" : "pending",
      detail: plan ? `Domain: ${plan.detected_domain}` : "Planner initializing...",
    },
    {
      id: "search",
      label: "Source Discovery",
      desc: "Search web query constraints",
      icon: Search,
      status: hasSearch ? "completed" : isRunning && hasPlan && !hasSearch ? "active" : "pending",
      detail: hasSearch
        ? `Found ${events.find((e) => e.event_type === "SEARCH_COMPLETED")?.metadata?.count || 0} candidate URLs`
        : "Waiting for plan...",
    },
    {
      id: "ingest",
      label: "Source Ingestion",
      desc: "Fetch & scrape discovered pages",
      icon: Database,
      status: hasIngest ? "completed" : isRunning && hasSearch && !hasIngest ? "active" : "pending",
      detail: sourceCount > 0 
        ? `Ingested ${sourceCount} domains: ${ingestedDomains.join(", ")}` 
        : "Searching...",
    },
    {
      id: "passages",
      label: "Passage Selection",
      desc: "Segment text & rank relevance",
      icon: FileText,
      status: hasPassages ? "completed" : isRunning && hasIngest && !hasPassages ? "active" : "pending",
      detail: hasPassages
        ? `Selected ${events.find((e) => e.event_type === "PASSAGES_SELECTED")?.metadata?.passage_count || 0} passages`
        : "Waiting for scraping...",
    },
    {
      id: "analyze",
      label: "AI Reasoning & Mapping",
      desc: "Extract claims & analyze relations",
      icon: Brain,
      status: hasAnalysis ? "completed" : isRunning && hasPassages && !hasAnalysis ? "active" : "pending",
      detail: hasAnalysis
        ? `Extracted ${graph?.claims.length || 0} claims, ${graph?.relations.length || 0} mappings`
        : "Extracting atomic facts...",
    },
    {
      id: "verdict",
      label: "Verdict Calibration",
      desc: "Score confidence & draft summary",
      icon: Scale,
      status: hasVerdict ? "completed" : isRunning && hasAnalysis && !hasVerdict ? "active" : "pending",
      detail: hasVerdict ? `${verdict} (${confidence}% confidence)` : "Calibrating...",
    },
  ];

  const currentActiveStep = steps.find((s) => s.status === "active") || steps.find((s) => s.status === "pending") || steps[steps.length - 1];

  // Render processing/live board if the query is still running
  if (isRunning) {
    return (
      <div className="max-w-4xl mx-auto w-full px-6 py-10 space-y-8 select-none">
        {/* Active Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-805 pb-6">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping" />
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-blue-400">
                AI Reasoning Engine Active
              </span>
            </div>
            <h1 className="text-xl font-extrabold tracking-tight text-white leading-normal">
              "{investigation.query}"
            </h1>
          </div>
          <div className="shrink-0 flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-xs text-slate-350">
            <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
            <span className="font-mono text-slate-400">Status: {investigation.status}</span>
          </div>
        </div>

        {/* Live Grid layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Steps Timeline (Left 2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-500">
              Orchestration Stages
            </h3>
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 divide-y divide-slate-800/60">
              {steps.map((step) => {
                const Icon = step.icon;
                const isActive = step.status === "active";
                const isCompleted = step.status === "completed";

                return (
                  <div
                    key={step.id}
                    className={`py-4 first:pt-0 last:pb-0 flex items-start space-x-4 transition-all duration-300 ${
                      isActive ? "bg-blue-500/5 -mx-4 px-4 rounded-lg" : ""
                    }`}
                  >
                    <div className="mt-0.5 shrink-0">
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      ) : isActive ? (
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      ) : (
                        <Icon className="w-5 h-5 text-slate-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className={`text-xs font-bold ${isActive ? "text-blue-400" : isCompleted ? "text-slate-300" : "text-slate-500"}`}>
                          {step.label}
                        </p>
                        <span className={`text-[10px] font-mono ${isActive ? "text-blue-500 animate-pulse font-bold" : isCompleted ? "text-emerald-500" : "text-slate-600"}`}>
                          {step.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{step.desc}</p>
                      <p className={`text-[10px] font-mono mt-1.5 p-1 rounded bg-slate-950/60 inline-block border border-slate-850 px-2 ${
                        isActive ? "text-blue-400 border-blue-900/30" : "text-slate-400"
                      }`}>
                        {step.detail}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Side Panels (Live logs & sources) */}
          <div className="space-y-6">
            {/* Active Task Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <h4 className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-500 animate-pulse" />
                <span>Active Process</span>
              </h4>
              <div className="space-y-2">
                <p className="text-xs text-white font-medium">
                  {currentActiveStep.label}
                </p>
                <p className="text-[10px] text-slate-400 leading-normal">
                  {currentActiveStep.desc}
                </p>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 animate-pulse" style={{ width: "66%" }} />
                </div>
              </div>
            </div>

            {/* Ingested sources live list */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 space-y-3 flex-1 flex flex-col h-[280px]">
              <h4 className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5 shrink-0">
                <FileText className="w-3.5 h-3.5 text-emerald-500" />
                <span>Ingested Sources ({sourceCount})</span>
              </h4>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-mono text-[9px] text-slate-400">
                {ingestedEvents.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-600 italic">
                    Waiting for web search results...
                  </div>
                ) : (
                  ingestedEvents.map((evt) => (
                    <div key={evt.id} className="p-2 rounded bg-slate-950/60 border border-slate-850 truncate flex items-center justify-between">
                      <span className="truncate pr-2">{evt.metadata?.domain || evt.metadata?.url || evt.title}</span>
                      <span className="text-emerald-500 font-bold shrink-0">OK</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Live Console Event Logs */}
        <div className="bg-slate-950 border border-slate-850 rounded-xl p-5 flex flex-col h-[180px]">
          <div className="flex items-center justify-between border-b border-slate-850 pb-2.5 mb-2.5 shrink-0">
            <h4 className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-ping" />
              <span>Pipeline Event Console</span>
            </h4>
            <span className="text-[8px] font-mono text-slate-500">Live WebSockets Active</span>
          </div>
          <div className="flex-1 overflow-y-auto font-mono text-[10px] text-slate-400 space-y-1.5 pr-1">
            {events.length === 0 ? (
              <p className="text-slate-600 italic">Initialising environment...</p>
            ) : (
              [...events].reverse().map((evt) => (
                <p key={evt.id} className="leading-relaxed">
                  <span className="text-slate-600">[{new Date(evt.occurred_at).toLocaleTimeString()}]</span>{" "}
                  <span className="text-blue-400 font-bold">{evt.event_type}</span>:{" "}
                  <span className="text-slate-300">{evt.description}</span>
                </p>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // Render completed or failed state
  return (
    <div className="max-w-2xl mx-auto w-full px-6 py-10 space-y-8 select-none">
      {/* Target Question */}
      <div className="space-y-1 border-b border-slate-800 pb-5">
        <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500">
          Fact-checking Query
        </div>
        <h1 className="text-2xl font-extrabold tracking-tight text-white leading-normal">
          {investigation.query}
        </h1>
      </div>

      {/* Verdict Card */}
      <div className="space-y-4">
        <div className={`p-6 rounded-xl border ${verdictBg} space-y-5 shadow-lg`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3.5">
              {verdict === "MIXED" || isFailed ? (
                <ShieldAlert className="w-10 h-10 shrink-0" />
              ) : (
                <ShieldCheck className="w-10 h-10 shrink-0" />
              )}
              <div className="space-y-0.5">
                <h2 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                  Current Assessment Verdict
                </h2>
                <p className="text-2xl font-extrabold tracking-tight text-white uppercase">
                  {verdict}
                </p>
              </div>
            </div>
            {!isFailed && (
              <div className="text-right">
                <p className="text-[10px] font-mono text-slate-400">Reasoning Confidence</p>
                <p className="text-2xl font-extrabold text-white flex items-center justify-end space-x-1">
                  <Award className="w-5 h-5 text-amber-500" />
                  <span>{confidence}%</span>
                </p>
              </div>
            )}
          </div>

          {/* Proportional Confidence Segments bar */}
          {!isFailed && (
            <div className="space-y-2.5">
              <div className="h-3 w-full rounded-full bg-slate-800 overflow-hidden flex">
                <div
                  className="h-full bg-emerald-500 transition-all duration-300"
                  style={{ width: `${supportedRatio}%` }}
                  title={`Supported: ${supportedRatio}%`}
                />
                <div
                  style={{ width: `${contradictedRatio}%` }}
                  className="h-full bg-red-500 transition-all duration-300"
                  title={`Contradicted: ${contradictedRatio}%`}
                />
                <div
                  style={{ width: `${unverifiedRatio}%` }}
                  className="h-full bg-amber-500 transition-all duration-300"
                  title={`Unverified: ${unverifiedRatio}%`}
                />
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>Supported ({supportedRatio}%)</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <span>Contradicted ({contradictedRatio}%)</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span>Unverified ({unverifiedRatio}%)</span>
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Primary explanation summary */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          Executive Summary
        </h3>
        <div className="bg-slate-900 border border-slate-850 p-5 rounded-xl text-slate-300 leading-relaxed font-sans text-sm">
          {explanation}
        </div>
      </div>

      {/* Target parameters summary */}
      {!isFailed && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 border-t border-b border-slate-850 py-6 text-center">
          <div className="space-y-1">
            <p className="text-[10px] font-mono text-slate-500 uppercase">Independent Sources</p>
            <p className="text-sm font-semibold text-white">
              {sourceCount} domains
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-[10px] font-mono text-slate-500 uppercase">Supporting Claims</p>
            <p className="text-sm font-semibold text-emerald-400">
              {supporting} confirmed
            </p>
          </div>
          <div className="col-span-2 md:col-span-1 space-y-1">
            <p className="text-[10px] font-mono text-slate-500 uppercase">Contradictions</p>
            <p className="text-sm font-semibold text-red-400">
              {contradicted} flagged
            </p>
          </div>
        </div>
      )}

      {/* Top cited domains */}
      {!isFailed && plan && (
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
            Top Cited Sources
          </h3>
          <div className="grid gap-2">
            {plan.preferred_source_categories.slice(0, 2).map((cat, idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg border border-slate-850 bg-slate-900/40 flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-2.5">
                  <FileText className="w-4 h-4 text-blue-500" />
                  <span className="font-medium text-slate-350">{cat}</span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">Source category preferred</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Progressive disclosure toggle */}
      <div className="pt-6">
        <button
          onClick={onInspect}
          className="w-full py-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-blue-500/40 hover:bg-slate-850/60 flex items-center justify-center space-x-2 text-sm font-semibold text-slate-200 hover:text-white shadow-lg transition-all"
        >
          <Activity className="w-4 h-4 text-blue-500 animate-pulse" />
          <span>Inspect Investigation & Evidence Workspace</span>
          <ArrowRight className="w-4 h-4 text-slate-500" />
        </button>
      </div>

      {/* Time & metadata footer */}
      <div className="flex items-center justify-center space-x-4 text-[10px] font-mono text-slate-500 pt-4">
        <span className="flex items-center space-x-1">
          <Calendar className="w-3.5 h-3.5" />
          <span>Last Audited: {new Date(investigation.updated_at).toLocaleDateString()}</span>
        </span>
        <span>•</span>
        <span>Engine: v1.0.0</span>
      </div>
    </div>
  );
}
