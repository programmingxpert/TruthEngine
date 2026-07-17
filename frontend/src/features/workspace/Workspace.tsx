import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, RefreshCw, FileText, CheckSquare, Terminal, Eye, Bookmark, Timeline } from "lucide-react";
import { api } from "../../core/api";
import type { Investigation, InvestigationPlan, TimelineEvent, EvidenceGraph } from "../../core/api";
import { AppShell } from "../../components/AppShell";
import { VerdictSummary } from "./VerdictSummary";
import { PipelineStack } from "./PipelineStack";
import { DossierView } from "./DossierView";
import { NotebookView } from "./NotebookView";
import { TimelineView } from "./TimelineView";
import { GraphView } from "./GraphView";
import { InspectorPanel } from "./InspectorPanel";

export function Workspace() {
  const { id = "" } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  // Mode states: Layer 1 (Fast Answer) vs Layer 2 (Deep Investigation Workspace)
  const [isInspectMode, setIsInspectMode] = useState(false);

  // Tab navigation: dossier, pipeline, graph, notebook, timeline
  const [activeTab, setActiveTab] = useState<"dossier" | "pipeline" | "graph" | "notebook" | "timeline">("dossier");

  // Selection states for Right Contextual Inspector
  const [selectedElement, setSelectedElement] = useState<{
    type: "claim" | "passage" | "source" | "relation" | "event" | "artifact";
    data: any;
  } | null>(null);

  // Notebook states
  const [notebookBookmarks, setNotebookBookmarks] = useState<any[]>([]);

  // Fetch core investigation
  const { data: inv, isLoading: isInvLoading, refetch: refetchInv } = useQuery<Investigation>({
    queryKey: ["investigation", id],
    queryFn: () => api.getInvestigation(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && !["COMPLETED", "FAILED", "CANCELLED"].includes(status) ? 2000 : false;
    },
  });

  // Fetch plan
  const { data: plan } = useQuery<InvestigationPlan>({
    queryKey: ["plan", id],
    queryFn: () => api.getPlan(id),
    enabled: !!id,
    retry: false,
  });

  // Fetch timeline events
  const { data: events = [] } = useQuery<TimelineEvent[]>({
    queryKey: ["timeline", id],
    queryFn: () => api.getTimeline(id),
    enabled: !!id,
    refetchInterval:
      inv && !["COMPLETED", "FAILED", "CANCELLED"].includes(inv.status) ? 2500 : false,
  });

  // Fetch graph details
  const { data: graph } = useQuery<EvidenceGraph>({
    queryKey: ["graph", id],
    queryFn: () => api.getLatestGraph(id),
    enabled: !!id && (isInspectMode || inv?.status === "COMPLETED"),
    refetchInterval:
      inv && !["COMPLETED", "FAILED", "CANCELLED"].includes(inv.status) ? 3000 : false,
    retry: false,
  });

  // Trigger Run Mutation if investigation is newly created
  const runMutation = useMutation({
    mutationFn: () => api.runInvestigation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigation", id] });
      queryClient.invalidateQueries({ queryKey: ["timeline", id] });
      queryClient.invalidateQueries({ queryKey: ["graph", id] });
    },
  });

  // Auto run newly created investigations
  useEffect(() => {
    if (inv && inv.status === "CREATED" && !runMutation.isPending && !runMutation.isSuccess) {
      runMutation.mutate();
    }
  }, [inv]);

  // Handle adding bookmarks
  const addBookmark = (bookmark: any) => {
    setNotebookBookmarks((prev) => [...prev, bookmark]);
  };

  const removeBookmark = (idx: number) => {
    setNotebookBookmarks((prev) => prev.filter((_, i) => i !== idx));
  };

  // Inspect artifact callback
  const handleInspectArtifact = (title: string, payload: any) => {
    setSelectedElement({
      type: "artifact",
      data: { title, payload },
    });
  };

  // Scroll back navigation callback on select bookmark
  const handleSelectBookmark = (bookmark: any) => {
    setSelectedElement({
      type: "passage",
      data: {
        text: bookmark.content,
        publisher: bookmark.source,
      },
    });
  };

  if (isInvLoading) {
    return (
      <AppShell>
        <div className="flex-1 flex flex-col items-center justify-center space-y-4">
          <RefreshCw className="w-8 h-8 text-brand animate-spin" />
          <p className="text-xs font-mono text-slate-500">Loading workspace configs...</p>
        </div>
      </AppShell>
    );
  }

  if (!inv) {
    return (
      <AppShell>
        <div className="flex-1 flex flex-col items-center justify-center space-y-4 text-center">
          <p className="text-sm font-semibold text-slate-200">Investigation not found</p>
          <Link to="/" className="text-xs text-brand hover:underline">
            Back to Dashboard
          </Link>
        </div>
      </AppShell>
    );
  }

  const isCompleted = inv.status === "COMPLETED";

  // Sidebar contents for Layer 2
  const leftSidebarContent = (
    <div className="flex flex-col h-full overflow-hidden select-none">
      {/* 1. Ingested Files list */}
      <div className="p-4 border-b border-border space-y-3 shrink-0">
        <h3 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
          <FileText className="w-3.5 h-3.5 text-brand" />
          <span>Ingested Sources</span>
        </h3>
        <div className="space-y-1.5 text-xs text-slate-350 max-h-[140px] overflow-y-auto pr-1">
          {events.filter((evt) => evt.event_type === "SOURCE_INGESTED").length === 0 ? (
            <div className="p-2 rounded bg-slate-900/60 border border-slate-800 truncate text-slate-500">
              No sources ingested yet
            </div>
          ) : (
            events
              .filter((evt) => evt.event_type === "SOURCE_INGESTED")
              .map((evt) => (
                <div key={evt.id} className="p-2 rounded bg-slate-900/60 border border-slate-800 truncate">
                  {evt.metadata?.domain || evt.metadata?.url || evt.title}
                </div>
              ))
          )}
        </div>
      </div>

      {/* 2. Objectives checklist */}
      <div className="p-4 border-b border-border flex-1 overflow-y-auto space-y-3">
        <h3 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
          <CheckSquare className="w-3.5 h-3.5 text-success" />
          <span>Investigation Plan Objectives</span>
        </h3>
        {plan ? (
          <div className="space-y-2">
            {plan.success_criteria.slice(0, 5).map((criterion) => (
              <div key={criterion} className="flex items-start space-x-2 text-xs text-slate-400 leading-normal">
                <span className="text-success select-none">✓</span>
                <span>{criterion}</span>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-[10px] text-slate-500 font-mono italic">Planner working...</span>
        )}
      </div>

      {/* 3. Live Logs ticker */}
      <div className="p-4 bg-slate-950/40 border-t border-border space-y-2 shrink-0 h-[150px] overflow-hidden flex flex-col">
        <h3 className="text-[9px] font-mono font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
          <Terminal className="w-3 h-3 text-brand" />
          <span>Live Pipeline Logs</span>
        </h3>
        <div className="flex-1 font-mono text-[9px] text-slate-500 space-y-1 overflow-y-auto pr-1 select-none">
          {events.length === 0 ? (
            <p>No pipeline events yet.</p>
          ) : (
            events.slice(-8).map((evt) => (
              <p key={evt.id}>
                [{new Date(evt.occurred_at).toLocaleTimeString()}] {evt.event_type}: {evt.description}
              </p>
            ))
          )}
        </div>
      </div>
    </div>
  );

  const rightSidebarContent = (
    <InspectorPanel
      selectedItem={selectedElement}
      onClose={() => setSelectedElement(null)}
      onAddBookmark={addBookmark}
    />
  );

  // Switch rendering layout dynamically based on Mode
  if (!isInspectMode) {
    return (
      <AppShell>
        <div className="border-b border-border bg-slate-900/40 h-12 px-6 flex items-center justify-between">
          <Link to="/" className="text-xs text-slate-400 hover:text-white flex items-center space-x-1.5">
            <ChevronLeft className="w-4 h-4" />
            <span>Back to Dashboard</span>
          </Link>
          <button
            onClick={() => refetchInv()}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex-1 flex items-center overflow-y-auto">
          <VerdictSummary
            investigation={inv}
            plan={plan}
            graph={graph}
            events={events}
            onInspect={() => setIsInspectMode(true)}
            isCompleted={isCompleted}
          />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      showLeftSidebar={true}
      showRightSidebar={true}
      leftSidebarContent={leftSidebarContent}
      rightSidebarContent={rightSidebarContent}
    >
      {/* Tab Navigation header */}
      <div className="h-12 border-b border-border bg-slate-900/20 px-6 flex items-center justify-between shrink-0 select-none">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab("dossier")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              activeTab === "dossier" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Dossier</span>
          </button>
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              activeTab === "pipeline" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Pipeline</span>
          </button>
          <button
            onClick={() => setActiveTab("graph")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              activeTab === "graph" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Graph</span>
          </button>
          <button
            onClick={() => setActiveTab("notebook")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              activeTab === "notebook" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" />
            <span>Notebook</span>
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-colors ${
              activeTab === "timeline" ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            <Timeline className="w-3.5 h-3.5" />
            <span>Timeline</span>
          </button>
        </div>

        <button
          onClick={() => setIsInspectMode(false)}
          className="text-xs text-brand hover:underline font-semibold"
        >
          Close Investigation Workspace
        </button>
      </div>

      {/* Main Tab Canvas Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === "dossier" && (
          <DossierView
            investigation={inv}
            plan={plan}
            graph={graph}
            events={events}
            onSelectClaim={(claimData) => setSelectedElement({ type: "claim", data: claimData })}
            onSelectSource={(title, domain) => setSelectedElement({ type: "source", data: { title, domain } })}
          />
        )}
        {activeTab === "pipeline" && (
          <PipelineStack
            investigation={inv}
            plan={plan}
            events={events}
            graph={graph}
            onInspectArtifact={handleInspectArtifact}
          />
        )}
        {activeTab === "graph" && (
          <GraphView
            claims={graph?.claims || []}
            evidenceItems={graph?.evidence_items || []}
            relations={graph?.relations || []}
            onSelectNode={(type, node) => setSelectedElement({ type, data: node })}
          />
        )}
        {activeTab === "notebook" && (
          <NotebookView
            bookmarks={notebookBookmarks}
            onRemoveBookmark={removeBookmark}
            onSelectBookmark={handleSelectBookmark}
          />
        )}
        {activeTab === "timeline" && (
          <TimelineView
            events={events}
            onSelectEvent={(evt) => setSelectedElement({ type: "event", data: evt })}
          />
        )}
      </div>
    </AppShell>
  );
}
