import { GitCommit, Calendar, Info, Clock, AlertTriangle, ShieldCheck } from "lucide-react";
import type { TimelineEvent } from "../../core/api";

interface TimelineViewProps {
  events: TimelineEvent[];
  onSelectEvent: (event: TimelineEvent) => void;
}

export function TimelineView({ events, onSelectEvent }: TimelineViewProps) {
  // Status mapping colors & symbols
  const getEventMarker = (type: TimelineEvent["event_type"]) => {
    switch (type) {
      case "WORKFLOW_COMPLETED":
        return { color: "text-success bg-success/15 border-success/40", icon: ShieldCheck };
      case "WORKFLOW_FAILED":
        return { color: "text-danger bg-danger/15 border-danger/40", icon: AlertTriangle };
      case "CONTRADICTION_DETECTED":
        return { color: "text-danger bg-danger/15 border-danger/40", icon: AlertTriangle };
      default:
        return { color: "text-slate-400 bg-slate-800 border-slate-700", icon: GitCommit };
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto w-full select-none">
      <div className="flex items-center space-x-2 border-b border-border pb-3">
        <Calendar className="w-4 h-4 text-brand" />
        <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          Chronological Audit timeline Event Log
        </h2>
      </div>

      {events.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-border rounded-xl space-y-3">
          <Clock className="w-8 h-8 text-slate-500 mx-auto" />
          <p className="text-sm font-medium text-slate-350">No timeline events recorded</p>
          <p className="text-xs text-slate-500">Run the pipeline orchestrator to generate audit trails.</p>
        </div>
      ) : (
        <div className="relative pl-6 border-l border-slate-800 space-y-6">
          {events.map((event) => {
            const marker = getEventMarker(event.event_type);
            const Icon = marker.icon;

            return (
              <div
                key={event.id}
                onClick={() => onSelectEvent(event)}
                className="relative p-4 rounded-xl border border-border bg-slate-900/30 hover:border-brand hover:bg-slate-900/50 cursor-pointer transition-all space-y-2 group"
              >
                {/* Connecting Node on Line */}
                <div
                  className={`absolute -left-[33px] top-4 w-6 h-6 rounded-full border flex items-center justify-center ${marker.color} group-hover:scale-110 transition-transform`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-500">
                    {event.stage} stage
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(event.occurred_at).toLocaleTimeString()}</span>
                  </span>
                </div>

                <h3 className="text-sm font-semibold text-slate-200 group-hover:text-white transition-colors">
                  {event.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {event.description}
                </p>

                <div className="flex items-center space-x-1.5 text-[9px] font-mono text-slate-500 pt-1">
                  <Info className="w-3 h-3" />
                  <span>Click to view metadata details</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
