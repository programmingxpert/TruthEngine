import React, { useState } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import type { Claim, EvidenceItem, EvidenceRelation } from "../../core/api";

interface GraphViewProps {
  claims: Claim[];
  evidenceItems: EvidenceItem[];
  relations: EvidenceRelation[];
  onSelectNode: (type: "claim" | "passage" | "relation", data: any) => void;
}

export function GraphView({ claims, evidenceItems, relations, onSelectNode }: GraphViewProps) {
  // Navigation transformation states
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Hover state for path highlighting
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Collapse states for claims
  const [collapsedClaims, setCollapsedClaims] = useState<Record<string, boolean>>({});

  // Background Grid Mouse Drag panning
  const handleMouseDown = (e: React.MouseEvent) => {
    // Left click only
    if (e.button !== 0) return;
    setIsPanning(true);
    setPanStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setOffset({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleZoom = (factor: number) => {
    setScale((prev) => Math.max(0.5, Math.min(1.5, prev * factor)));
  };

  const handleReset = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  };

  const toggleClaimCollapse = (claimId: string) => {
    setCollapsedClaims((prev) => ({
      ...prev,
      [claimId]: !prev[claimId],
    }));
  };

  // Helper check to verify if a node is dimmed during hover path highlights
  const isDimmed = (nodeId: string, type: "claim" | "passage") => {
    if (!hoveredNodeId) return false;
    if (hoveredNodeId === nodeId) return false;

    // Check if there is a relation linking the hovered node to this node
    if (type === "claim") {
      // hovered node is a passage
      return !relations.some(
        (rel) => rel.claim_id === nodeId && rel.evidence_item_id === hoveredNodeId
      );
    } else {
      // hovered node is a claim
      return !relations.some(
        (rel) => rel.claim_id === hoveredNodeId && rel.evidence_item_id === nodeId
      );
    }
  };

  // Fixed coordinates for bipartite rendering
  // Claims are drawn on the left column (X = 100), passages on the right column (X = 500)
  const leftX = 100;
  const rightX = 480;

  const claimSpacing = 160;
  const passageSpacing = 110;

  return (
    <div className="relative flex-1 bg-slate-950 overflow-hidden select-none border border-border rounded-xl">
      {/* Zoom and Pan Floating Toolbar */}
      <div className="absolute top-4 left-4 z-40 flex items-center bg-slate-900 border border-border rounded-lg p-1.5 space-x-1.5 shadow-xl">
        <button
          onClick={() => handleZoom(1.1)}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleZoom(0.9)}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <div className="w-[1px] h-4 bg-border" />
        <button
          onClick={handleReset}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Recenter"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <span className="text-[9px] font-mono text-slate-500 px-1.5">{Math.round(scale * 100)}%</span>
      </div>

      {/* Grid Canvas */}
      <div
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`w-full h-full relative cursor-grab ${isPanning ? "cursor-grabbing" : ""}`}
        style={{
          backgroundImage: `radial-gradient(#334155 1px, transparent 1px)`,
          backgroundSize: "20px 20px",
          backgroundPosition: `${offset.x}px ${offset.y}px`,
        }}
      >
        <div
          className="absolute origin-center transition-transform duration-100 ease-out"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
          }}
        >
          {/* SVG Connection Lines layer */}
          <svg className="absolute overflow-visible w-1 h-1 pointer-events-none" style={{ left: 0, top: 0 }}>
            <defs>
              <marker id="arrow-supports" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10B981" />
              </marker>
              <marker id="arrow-contradicts" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#EF4444" />
              </marker>
            </defs>

            {relations.map((rel) => {
              const claimIdx = claims.findIndex((c) => c.id === rel.claim_id);
              const passageIdx = evidenceItems.findIndex((e) => e.id === rel.evidence_item_id);

              if (claimIdx === -1 || passageIdx === -1) return null;
              if (collapsedClaims[rel.claim_id]) return null;

              const cY = 100 + claimIdx * claimSpacing;
              const pY = 80 + passageIdx * passageSpacing;

              const isHighlighted = hoveredNodeId === rel.claim_id || hoveredNodeId === rel.evidence_item_id;
              const pathOpacity = hoveredNodeId ? (isHighlighted ? 0.9 : 0.15) : 0.5;
              const lineColor = rel.relation_type === "CONTRADICTS" ? "#EF4444" : "#10B981";
              const markerId = rel.relation_type === "CONTRADICTS" ? "url(#arrow-contradicts)" : "url(#arrow-supports)";

              return (
                <g key={rel.id}>
                  {/* Connection Line */}
                  <path
                    d={`M ${rightX} ${pY} Q ${(rightX + leftX) / 2} ${(pY + cY) / 2}, ${leftX + 220} ${cY}`}
                    fill="none"
                    stroke={lineColor}
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                    strokeDasharray={rel.relation_type === "CONTRADICTS" ? "4 4" : "none"}
                    strokeOpacity={pathOpacity}
                    markerEnd={markerId}
                    className="transition-all duration-150"
                  />
                  {/* Conflict VS badge */}
                  {rel.relation_type === "CONTRADICTS" && (
                    <foreignObject
                      x={(rightX + leftX) / 2 - 12}
                      y={(pY + cY) / 2 - 10}
                      width="24"
                      height="20"
                      opacity={pathOpacity}
                    >
                      <div className="w-6 h-5 rounded bg-danger flex items-center justify-center text-[8px] font-extrabold text-white shadow shadow-danger/30">
                        VS
                      </div>
                    </foreignObject>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Left Column Nodes: Claims */}
          <div className="absolute space-y-0" style={{ left: `${leftX}px`, top: `60px` }}>
            {claims.map((claim, idx) => {
              const collapsed = collapsedClaims[claim.id];
              const cY = idx * claimSpacing;
              const dimmed = isDimmed(claim.id, "claim");

              return (
                <div
                  key={claim.id}
                  style={{ transform: `translateY(${cY}px)` }}
                  onMouseEnter={() => setHoveredNodeId(claim.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  onClick={() => onSelectNode("claim", claim)}
                  className={`absolute w-[220px] p-3 rounded-lg border bg-slate-900 shadow-md cursor-pointer transition-all duration-150 ${
                    dimmed ? "opacity-30 border-slate-800 scale-95" : "border-slate-700 hover:border-brand scale-100"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[8px] font-mono text-slate-500 uppercase">Factual Claim</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleClaimCollapse(claim.id);
                      }}
                      className="text-[9px] font-mono text-brand hover:text-brand-hover px-1 rounded hover:bg-slate-800"
                    >
                      {collapsed ? "Expand" : "Collapse"}
                    </button>
                  </div>
                  <p className="text-[10px] text-slate-200 font-medium leading-normal line-clamp-3">
                    {claim.claim_text}
                  </p>
                  <div className="flex items-center space-x-1.5 mt-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        claim.status === "SUPPORTED"
                          ? "bg-success"
                          : claim.status === "CONTRADICTED"
                          ? "bg-danger"
                          : "bg-warning"
                      }`}
                    />
                    <span className="text-[8px] font-mono text-slate-500 uppercase">{claim.status}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Right Column Nodes: Passages */}
          <div className="absolute space-y-0" style={{ left: `${rightX}px`, top: `40px` }}>
            {evidenceItems.map((item, idx) => {
              const pY = idx * passageSpacing;
              const dimmed = isDimmed(item.id, "passage");

              return (
                <div
                  key={item.id}
                  style={{ transform: `translateY(${pY}px)` }}
                  onMouseEnter={() => setHoveredNodeId(item.id)}
                  onMouseLeave={() => setHoveredNodeId(null)}
                  onClick={() => onSelectNode("passage", item)}
                  className={`absolute w-[240px] p-3 rounded-lg border bg-slate-900 shadow-md cursor-pointer transition-all duration-150 ${
                    dimmed ? "opacity-30 border-slate-800 scale-95" : "border-slate-700 hover:border-brand scale-100"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[8px] font-mono text-slate-500 uppercase truncate pr-2">
                      {item.publisher}
                    </span>
                    <span className="text-[8px] font-mono text-slate-500 shrink-0">Passage</span>
                  </div>
                  <p className="text-[10px] text-slate-350 italic leading-relaxed line-clamp-3">
                    "{item.passage_text}"
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
