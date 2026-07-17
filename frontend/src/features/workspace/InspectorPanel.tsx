import { useState } from "react";
import { X, Clipboard, Bookmark, Info, ChevronDown, ChevronRight, FileText, CheckCircle2 } from "lucide-react";

interface InspectorPanelProps {
  selectedItem: {
    type: "claim" | "passage" | "source" | "relation" | "event" | "artifact";
    data: any;
  } | null;
  onClose: () => void;
  onAddBookmark: (bookmark: any) => void;
}

export function InspectorPanel({ selectedItem, onClose, onAddBookmark }: InspectorPanelProps) {
  const [showTechnical, setShowTechnical] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!selectedItem) {
    return (
      <div className="p-6 h-full flex flex-col justify-center text-center space-y-3 text-slate-500 select-none">
        <Info className="w-8 h-8 mx-auto text-slate-650" />
        <p className="text-xs font-mono">No element selected</p>
        <p className="text-[10px] text-slate-600 max-w-[200px] mx-auto leading-relaxed">
          Click on any node in the graph, timeline event, or claim in the dossier to inspect provenance data.
        </p>
      </div>
    );
  }

  const { type, data } = selectedItem;

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900/60 border-l border-border select-none">
      {/* Panel Header */}
      <div className="h-14 border-b border-border px-4 flex items-center justify-between bg-slate-900/80 shrink-0">
        <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider">
          <FileText className="w-3.5 h-3.5 text-brand" />
          <span>{type} Inspector</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Panel Content (Scroll container) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Layout: CLAIM */}
        {type === "claim" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Statement</h3>
              <p className="text-sm font-medium text-white leading-relaxed">{data.claim_text || data.text}</p>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Assessment Status</h3>
              <div className="flex items-center space-x-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    data.status === "SUPPORTED"
                      ? "bg-success"
                      : data.status === "CONTRADICTED"
                      ? "bg-danger"
                      : "bg-warning"
                  }`}
                />
                <span className="text-xs font-semibold text-slate-200">{data.status || "UNVERIFIED"}</span>
              </div>
            </div>

            {Array.isArray(data.evidence) && data.evidence.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">
                  Evidence Trail
                </h3>
                {data.evidence.map((bundle: any) => (
                  <div
                    key={bundle.relation?.id || bundle.evidence?.id}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2 text-[10px] font-mono">
                      <span className="text-slate-400 truncate">
                        {bundle.evidence?.publisher || "source"}
                      </span>
                      <span className="text-slate-500 uppercase">
                        {bundle.relation?.relation_type || "RELATION"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      "{bundle.evidence?.passage_text}"
                    </p>
                    <p className="text-[10px] font-mono text-slate-600 break-all">
                      {bundle.evidence?.url}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => onAddBookmark({ content: data.claim_text || data.text, source: "Claim Node" })}
                className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-border text-xs text-slate-350 hover:text-white flex items-center justify-center space-x-1.5 transition-colors"
              >
                <Bookmark className="w-3.5 h-3.5" />
                <span>Bookmark Claim</span>
              </button>
            </div>
          </div>
        )}

        {/* Layout: PASSAGE */}
        {type === "passage" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Text Snippet</h3>
              <p className="text-xs text-slate-200 bg-slate-950 p-3 rounded-lg border border-slate-900 leading-relaxed italic">
                "{data.passage_text || data.content || data.text}"
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Metadata</h3>
              <div className="font-mono text-[10px] text-slate-400 space-y-1">
                <p>Publisher: {data.publisher || data.source || "Unknown"}</p>
                <p>Location URL: {data.url || "https://..."}</p>
                <p>Paragraph Index: #{data.paragraph_order || 1}</p>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Selection Explanation</h3>
              <div className="space-y-1.5 text-xs text-slate-300">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span>✓ Matched query keywords</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span>✓ Preceding heading relevance</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                  <span>✓ Matches active Domain Profile criteria</span>
                </div>
              </div>
            </div>

            <div className="flex space-x-2 pt-2">
              <button
                onClick={() => onAddBookmark({ content: data.passage_text || data.content || data.text, source: data.publisher })}
                className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-border text-xs text-slate-350 hover:text-white flex items-center justify-center space-x-1.5 transition-colors"
              >
                <Bookmark className="w-3.5 h-3.5" />
                <span>Bookmark Clip</span>
              </button>
            </div>
          </div>
        )}

        {/* Layout: SOURCE */}
        {type === "source" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Publisher Domain</h3>
              <p className="text-sm font-semibold text-white">{data.source || data.title}</p>
              <p className="text-xs text-slate-400 truncate">{data.domain || data.url}</p>
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Crawl Log</h3>
              <div className="font-mono text-[10px] text-slate-400 space-y-1.5">
                <p>Status: {data.http_status || "Unknown"}</p>
                <p>Fetch latency: {data.fetch_duration_ms ? `${data.fetch_duration_ms}ms` : "Unknown"}</p>
                <p className="truncate">Content hash: {data.hash || data.content_hash || "Unknown"}</p>
              </div>
            </div>
          </div>
        )}

        {/* Layout: EVENT */}
        {type === "event" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Timeline Event</h3>
              <p className="text-sm font-semibold text-white">{data.title}</p>
              <p className="text-xs text-slate-400">{data.description}</p>
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Audit Parameters</h3>
              <div className="font-mono text-[10px] text-slate-400 space-y-1">
                <p>Stage: {data.stage}</p>
                <p>Type: {data.event_type}</p>
                <p>Time: {new Date(data.occurred_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        {/* Layout: ARTIFACT */}
        {type === "artifact" && (
          <div className="space-y-4">
            <div className="space-y-1">
              <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase">Stage Output Artifact</h3>
              <p className="text-sm font-semibold text-white">{data.title}</p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-900 font-mono text-[10px] text-slate-300 leading-relaxed overflow-x-auto max-h-[300px]">
              <pre>{JSON.stringify(data.payload, null, 2)}</pre>
            </div>
          </div>
        )}

        {/* Layered Disclosure: Advanced Technical Drawer */}
        {type !== "artifact" && (
          <div className="border-t border-border pt-4 space-y-2">
            <button
              onClick={() => setShowTechnical(!showTechnical)}
              className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white font-mono transition-colors"
            >
              {showTechnical ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              <span>Technical Details</span>
            </button>

            {showTechnical && (
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-900 font-mono text-[9px] text-slate-400 space-y-2 relative">
                <button
                  onClick={() => handleCopy(JSON.stringify(data, null, 2))}
                  className="absolute top-2 right-2 p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
                  title="Copy JSON Payload"
                >
                  <Clipboard className="w-3.5 h-3.5" />
                </button>
                <pre className="overflow-x-auto whitespace-pre-wrap leading-relaxed max-w-[260px]">
                  {JSON.stringify(data, null, 2)}
                </pre>
                {copied && (
                  <span className="absolute bottom-2 right-2 text-[8px] text-success font-semibold">
                    Copied!
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
