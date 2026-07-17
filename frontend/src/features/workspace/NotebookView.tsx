import React, { useState } from "react";
import { BookOpen, Bookmark, FileEdit, Plus, Trash2 } from "lucide-react";

interface NotebookViewProps {
  bookmarks: any[];
  onRemoveBookmark: (idx: number) => void;
  onSelectBookmark: (bookmark: any) => void;
}

export function NotebookView({ bookmarks, onRemoveBookmark, onSelectBookmark }: NotebookViewProps) {
  const [hypotheses, setHypotheses] = useState<string[]>([
    "Creatine safety levels correlate directly with pre-existing glomerular capacity.",
    "Muscular waste clearance byproducts create elevated creatinine biomarkers without GFR damage.",
  ]);
  const [newHypothesis, setNewHypothesis] = useState("");

  const [notes, setNotes] = useState(
    "### Initial Findings\n- Clinical studies indicate no GFR changes during creatine loading phases in healthy cohorts.\n- Contradictions are isolated to diabetic nephropathy and similar pre-existing renal disease histories."
  );

  const addHypothesis = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHypothesis.trim()) return;
    setHypotheses([...hypotheses, newHypothesis.trim()]);
    setNewHypothesis("");
  };

  const removeHypothesis = (idx: number) => {
    setHypotheses(hypotheses.filter((_, i) => i !== idx));
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto w-full grid md:grid-cols-3 gap-6 select-none">
      {/* Left Column: Hypotheses & Bookmarks */}
      <div className="md:col-span-1 space-y-6">
        {/* Hypotheses */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 border-b border-border pb-2">
            <BookOpen className="w-4 h-4 text-brand" />
            <span className="uppercase font-semibold tracking-wider">Hypotheses</span>
          </div>

          <form onSubmit={addHypothesis} className="flex space-x-2">
            <input
              type="text"
              value={newHypothesis}
              onChange={(e) => setNewHypothesis(e.target.value)}
              placeholder="Add hypothesis..."
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand"
            />
            <button
              type="submit"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-border transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="space-y-2">
            {hypotheses.map((hyp, i) => (
              <div
                key={i}
                className="p-3 rounded-lg border border-border bg-slate-900/30 flex items-start justify-between text-xs text-slate-300"
              >
                <span className="flex-1 pr-2 break-words leading-relaxed">{hyp}</span>
                <button
                  onClick={() => removeHypothesis(i)}
                  className="p-1 rounded text-slate-500 hover:text-danger hover:bg-danger/10 transition-all shrink-0"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Bookmarks */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 border-b border-border pb-2">
            <Bookmark className="w-4 h-4 text-warning" />
            <span className="uppercase font-semibold tracking-wider">Bookmarks</span>
          </div>

          {bookmarks.length === 0 ? (
            <p className="text-[10px] text-slate-500 text-center py-6 border border-dashed border-border rounded-lg">
              Drag snippets or click bookmark icons in the inspector to save clips.
            </p>
          ) : (
            <div className="space-y-2">
              {bookmarks.map((bookmark, idx) => (
                <div
                  key={idx}
                  onClick={() => onSelectBookmark(bookmark)}
                  className="p-3 rounded-lg border border-border bg-slate-900/30 hover:border-brand cursor-pointer flex items-start justify-between text-xs transition-all"
                >
                  <div className="space-y-1 flex-1 pr-2 min-w-0">
                    <p className="font-mono text-[9px] text-slate-500 truncate">
                      {bookmark.domain || bookmark.source || "Snippet"}
                    </p>
                    <p className="text-slate-300 line-clamp-2 italic leading-relaxed">
                      "{bookmark.content || bookmark.text}"
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveBookmark(idx);
                    }}
                    className="p-1 rounded text-slate-500 hover:text-danger hover:bg-danger/10 transition-all shrink-0"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Column: Markdown Editor */}
      <div className="md:col-span-2 space-y-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 border-b border-border pb-2">
          <FileEdit className="w-4 h-4 text-brand" />
          <span className="uppercase font-semibold tracking-wider">Notes & Observations</span>
        </div>

        <div className="flex flex-col h-[400px] border border-border rounded-xl bg-slate-900/20 overflow-hidden">
          <div className="px-4 py-2 border-b border-border bg-slate-900/40 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>Markdown Notepad</span>
            <span>Saved to local workspace</span>
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="flex-1 bg-transparent border-0 p-4 text-xs font-mono text-slate-300 placeholder-slate-650 leading-relaxed focus:ring-0 focus:outline-none resize-none overflow-y-auto"
          />
        </div>
      </div>
    </div>
  );
}
