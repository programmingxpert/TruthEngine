import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, ShieldAlert, ArrowRight, Activity, RefreshCw, FolderOpen, Trash2 } from "lucide-react";
import { api, type Investigation } from "../../core/api";
import { AppShell } from "../../components/AppShell";

export function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch audits
  const {
    data: investigations = [],
    isLoading,
    isError,
    refetch,
  } = useQuery<Investigation[]>({
    queryKey: ["investigations"],
    queryFn: api.getInvestigations,
  });

  // Create investigation mutation
  const createMutation = useMutation({
    mutationFn: api.createInvestigation,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
      // Redirect to the newly created investigation workspace page
      navigate(`/investigations/${data.id}`);
    },
  });

  // Delete investigation mutation
  const deleteMutation = useMutation({
    mutationFn: api.deleteInvestigation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["investigations"] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    createMutation.mutate(searchQuery.trim());
  };

  const handleExampleClick = (query: string) => {
    setSearchQuery(query);
    createMutation.mutate(query);
  };

  // Status mapping colors & labels
  const getStatusBadge = (status: Investigation["status"]) => {
    switch (status) {
      case "COMPLETED":
        return { color: "bg-success/10 text-success border-success/30", label: "Completed" };
      case "FAILED":
        return { color: "bg-danger/10 text-danger border-danger/30", label: "Failed" };
      case "CREATED":
        return { color: "bg-slate-800 text-slate-400 border-slate-700", label: "Created" };
      default:
        return { color: "bg-brand/10 text-brand border-brand/30 animate-pulse", label: "Running" };
    }
  };

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto w-full px-6 py-12 flex-1 flex flex-col justify-center">
        {/* Hero Branding */}
        <div className="text-center mb-10 space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/20 text-xs font-mono text-brand">
            <Activity className="w-3.5 h-3.5" />
            <span>AI Reasoning Registry</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            TRUTHENGINE
          </h1>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Audit assertions and inspect supporting evidence through a transparent, versioned graph model.
          </p>
        </div>

        {/* Claim Validation Query Input */}
        <form onSubmit={handleSubmit} className="mb-12">
          <div className="relative group">
            <div className="absolute inset-0 bg-brand/10 rounded-xl blur-md group-focus-within:bg-brand/20 transition duration-200" />
            <div className="relative flex items-center bg-slate-900 border border-slate-700 group-focus-within:border-brand rounded-xl overflow-hidden shadow-xl transition-all">
              <Search className="w-5 h-5 text-slate-500 ml-4 shrink-0" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter a claim or query to investigate..."
                disabled={createMutation.isPending}
                className="w-full bg-transparent border-0 px-4 py-4 text-sm text-slate-100 placeholder-slate-500 focus:ring-0 focus:outline-none"
              />
              <button
                type="submit"
                disabled={createMutation.isPending || !searchQuery.trim()}
                className="px-5 py-2.5 mr-2 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-medium flex items-center space-x-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              >
                {createMutation.isPending ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <span>Verify</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Example Suggestions */}
          <div className="mt-4 flex flex-wrap gap-2 items-center justify-center text-xs text-slate-400">
            <span>Try:</span>
            <button
              type="button"
              onClick={() => handleExampleClick("Explain student learning curves in school.")}
              className="px-2.5 py-1 rounded bg-slate-900 border border-border hover:border-brand hover:text-white transition-colors"
            >
              "Explain student learning curves..."
            </button>
            <button
              type="button"
              onClick={() => handleExampleClick("Is Rust replacing C++?")}
              className="px-2.5 py-1 rounded bg-slate-900 border border-border hover:border-brand hover:text-white transition-colors"
            >
              "Is Rust replacing C++?"
            </button>
          </div>
        </form>

        {/* Dashboard Lists: Investigations */}
        <div className="space-y-6">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
              Active Investigations
            </h2>
            <button
              onClick={() => refetch()}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Refresh Audits"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <RefreshCw className="w-8 h-8 text-brand animate-spin" />
              <span className="text-xs text-slate-500 font-mono">Loading investigation list...</span>
            </div>
          )}

          {isError && (
            <div className="flex flex-col items-center justify-center py-12 px-6 rounded-lg border border-danger/20 bg-danger/5 text-center space-y-4">
              <ShieldAlert className="w-8 h-8 text-danger" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200">Failed to fetch audits</p>
                <p className="text-xs text-slate-500">Ensure the TruthEngine backend API server is running.</p>
              </div>
              <button
                onClick={() => refetch()}
                className="px-3.5 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-medium flex items-center space-x-1.5 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Connection</span>
              </button>
            </div>
          )}

          {!isLoading && !isError && investigations.length === 0 && (
            <div className="text-center py-16 border border-dashed border-border rounded-xl space-y-4">
              <div className="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mx-auto">
                <FolderOpen className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-slate-200">No active audits</p>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  Type a query in the validation input above to launch your first claim investigation.
                </p>
              </div>
            </div>
          )}

          {!isLoading && !isError && investigations.length > 0 && (
            <div className="grid gap-3">
              {investigations.map((inv) => {
                const badge = getStatusBadge(inv.status);
                return (
                  <div
                    key={inv.id}
                    onClick={() => navigate(`/investigations/${inv.id}`)}
                    className="p-4 rounded-xl border border-border bg-slate-900/60 hover:bg-slate-850 hover:border-slate-700 hover:scale-[1.005] transition-all cursor-pointer flex items-center justify-between group"
                  >
                    <div className="space-y-1.5 pr-4 flex-1 min-w-0">
                      <div className="flex items-center space-x-2.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono border ${badge.color}`}
                        >
                          {badge.label}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(inv.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-slate-200 truncate">{inv.query}</p>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm("Are you sure you want to delete this investigation?")) {
                            deleteMutation.mutate(inv.id);
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="p-2 rounded bg-slate-950/40 hover:bg-red-500/10 border border-slate-800 hover:border-red-500/30 text-slate-550 hover:text-red-400 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-all"
                        title="Delete Investigation"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      <ArrowRight className="w-4 h-4 text-slate-505 group-hover:text-white transition-colors" />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
