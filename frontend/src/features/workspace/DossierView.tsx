import { AlertTriangle, BookOpen, GitPullRequest, ShieldAlert, ShieldCheck } from "lucide-react";
import type {
  Claim,
  EvidenceGraph,
  EvidenceItem,
  EvidenceRelation,
  Investigation,
  InvestigationPlan,
  TimelineEvent,
} from "../../core/api";

interface DossierViewProps {
  investigation: Investigation;
  plan?: InvestigationPlan;
  graph?: EvidenceGraph;
  events: TimelineEvent[];
  onSelectClaim: (claimData: Claim & { evidence: EvidenceBundle[]; status: string }) => void;
  onSelectSource: (title: string, domain: string) => void;
}

interface EvidenceBundle {
  relation: EvidenceRelation;
  evidence: EvidenceItem;
}

export function DossierView({
  investigation,
  plan,
  graph,
  events,
  onSelectClaim,
  onSelectSource,
}: DossierViewProps) {
  const verdictEvent = [...events].reverse().find((evt) => evt.event_type === "VERDICT_GENERATED");
  const supportedRelations = graph?.relations.filter((rel) => rel.relation_type === "SUPPORTS") || [];
  const contradictedRelations =
    graph?.relations.filter((rel) => rel.relation_type === "CONTRADICTS") || [];
  const supportedClaims =
    graph?.claims.filter((claim) =>
      supportedRelations.some((rel) => rel.claim_id === claim.id)
    ) || [];
  const contradictedClaims =
    graph?.claims.filter((claim) =>
      contradictedRelations.some((rel) => rel.claim_id === claim.id)
    ) || [];
  const limitations =
    plan?.limitations ||
    events
      .filter((evt) => evt.event_type.includes("SKIPPED") || evt.event_type.includes("BLOCKED"))
      .map((evt) => evt.description);

  const evidenceById = new Map((graph?.evidence_items || []).map((item) => [item.id, item]));

  const getEvidenceForClaim = (claimId: string, relationType?: EvidenceRelation["relation_type"]) =>
    (graph?.relations || [])
      .filter((rel) => rel.claim_id === claimId)
      .filter((rel) => (relationType ? rel.relation_type === relationType : true))
      .map((relation) => {
        const evidence = evidenceById.get(relation.evidence_item_id);
        return evidence ? { relation, evidence } : null;
      })
      .filter((bundle): bundle is EvidenceBundle => bundle !== null);

  const renderEvidenceBundle = (bundle: EvidenceBundle) => (
    <div
      key={bundle.relation.id}
      onClick={(event) => {
        event.stopPropagation();
        onSelectSource(bundle.evidence.title, bundle.evidence.publisher);
      }}
      className="p-3 rounded-lg border border-slate-800 bg-slate-950/50 hover:border-slate-700 cursor-pointer space-y-2"
    >
      <div className="flex items-center justify-between gap-3 text-[10px] font-mono">
        <span className="text-slate-400 truncate">{bundle.evidence.publisher}</span>
        <span className="text-slate-500 uppercase">{bundle.relation.relation_type}</span>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
        "{bundle.evidence.passage_text}"
      </p>
      <p className="text-[10px] font-mono text-slate-600 truncate">{bundle.evidence.url}</p>
    </div>
  );

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto w-full font-sans leading-relaxed select-none">
      <div className="border-b border-border pb-4 space-y-1">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-500">
          <span>INVESTIGATION DOSSIER</span>
          <span>•</span>
          <span>QUERY ID: {investigation.id.slice(0, 8)}</span>
        </div>
        <h2 className="text-xl font-extrabold text-white">{investigation.query}</h2>
      </div>

      <section className="space-y-3">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <BookOpen className="w-4 h-4 text-brand" />
          <span className="uppercase font-semibold tracking-wider">1. Executive Summary</span>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed pl-6 border-l-2 border-slate-800">
          {verdictEvent?.metadata?.explanation ||
            "No final verdict has been generated yet. The dossier will populate from backend execution artifacts as the investigation progresses."}
        </p>
      </section>

      <section className="space-y-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <ShieldCheck className="w-4 h-4 text-success" />
          <span className="uppercase font-semibold tracking-wider">2. Supported Claims</span>
        </div>
        <div className="pl-6 space-y-3">
          {supportedClaims.length === 0 ? (
            <p className="text-xs text-slate-500">No supported claims recorded yet.</p>
          ) : (
            supportedClaims.map((claim) => {
              const evidence = getEvidenceForClaim(claim.id, "SUPPORTS");
              return (
                <div
                  key={claim.id}
                  onClick={() => onSelectClaim({ ...claim, status: "SUPPORTED", evidence })}
                  className="p-4 rounded-xl border border-border bg-slate-900/30 hover:border-slate-700 cursor-pointer transition-colors space-y-3"
                >
                  <p className="text-sm font-medium text-slate-200">{claim.claim_text}</p>
                  <div className="flex flex-wrap gap-2 text-[10px] font-mono text-success">
                    <span>{evidence.length} supporting evidence item(s)</span>
                    {evidence[0] && <span>from {evidence[0].evidence.publisher}</span>}
                  </div>
                  <div className="space-y-2">{evidence.slice(0, 2).map(renderEvidenceBundle)}</div>
                </div>
              );
            })
          )}
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <ShieldAlert className="w-4 h-4 text-danger" />
          <span className="uppercase font-semibold tracking-wider">3. Highlighted Contradictions</span>
        </div>
        <div className="pl-6 space-y-4">
          {contradictedClaims.length === 0 ? (
            <p className="text-xs text-slate-500">No contradictions recorded yet.</p>
          ) : (
            contradictedClaims.map((claim) => {
              const evidence = getEvidenceForClaim(claim.id, "CONTRADICTS");
              return (
                <div key={claim.id} className="p-4 rounded-xl border border-danger/20 bg-danger/5 space-y-3">
                  <h4 className="text-xs font-semibold text-slate-200">
                    Contradicted claim: "{claim.claim_text}"
                  </h4>
                  <div className="space-y-2">{evidence.slice(0, 3).map(renderEvidenceBundle)}</div>
                </div>
              );
            })
          )}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <AlertTriangle className="w-4 h-4 text-warning" />
          <span className="uppercase font-semibold tracking-wider">4. Gaps & Unknowns</span>
        </div>
        <ul className="pl-12 list-disc space-y-2 text-xs text-slate-400">
          {limitations.length === 0 ? (
            <li>No limitations have been recorded yet.</li>
          ) : (
            limitations.map((gap, i) => <li key={`${gap}-${i}`}>{gap}</li>)
          )}
        </ul>
      </section>

      <section className="space-y-4 border-t border-border pt-6">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          <span className="uppercase font-semibold tracking-wider text-slate-300">5. Source Provenance & Citations</span>
        </div>
        <div className="pl-6 space-y-4">
          {(() => {
            // Group evidence by publisher to find cited sources
            const citedSourcesMap = new Map<string, {
              publisher: string;
              title: string;
              url: string;
              count: number;
              category: string;
            }>();

            (graph?.evidence_items || []).forEach((item) => {
              const existing = citedSourcesMap.get(item.publisher);
              if (existing) {
                existing.count += 1;
              } else {
                citedSourcesMap.set(item.publisher, {
                  publisher: item.publisher,
                  title: item.title,
                  url: item.url,
                  count: 1,
                  category: item.source_category || "GENERAL",
                });
              }
            });

            const citedSources = Array.from(citedSourcesMap.values());
            const ingestedSources = events
              .filter((evt) => evt.event_type === "SOURCE_INGESTED")
              .map((evt) => ({
                domain: evt.metadata?.domain || evt.metadata?.publisher || "unknown",
                url: evt.metadata?.url || "",
                title: evt.metadata?.title || evt.message || "unknown",
              }));

            return (
              <div className="space-y-6">
                {citedSources.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No citations mapped from ingested sources yet. Claims are still being verified.</p>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950/20">
                    <table className="w-full text-left border-collapse text-xs font-sans">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-950/60 font-mono text-[10px] text-slate-500 uppercase tracking-wider">
                          <th className="p-3">Source / Institution</th>
                          <th className="p-3">Category</th>
                          <th className="p-3 text-center">Citations Used</th>
                          <th className="p-3">Resource Location</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {citedSources.map((src, idx) => (
                          <tr key={`${src.publisher}-${idx}`} className="hover:bg-slate-900/20 transition-colors">
                            <td className="p-3 font-medium text-slate-200">
                              <div className="flex flex-col space-y-0.5 max-w-md">
                                <span className="font-mono text-xs text-slate-200 font-semibold">{src.publisher}</span>
                                <span className="text-[10px] text-slate-400 truncate">{src.title}</span>
                              </div>
                            </td>
                            <td className="p-3">
                              <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-mono font-medium bg-slate-900 border border-slate-800 text-slate-400">
                                {src.category}
                              </span>
                            </td>
                            <td className="p-3 text-center text-indigo-400 font-mono font-bold text-xs">
                              {src.count} quote(s)
                            </td>
                            <td className="p-3 max-w-xs truncate font-mono text-[10px] text-slate-500 hover:text-indigo-400">
                              <a href={src.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                {src.url}
                              </a>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {ingestedSources.length > 0 && (
                  <div className="space-y-3">
                    <div className="font-mono text-[10px] text-slate-500 uppercase tracking-wider">
                      Scanned Bibliography ({ingestedSources.length} sources crawled)
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {ingestedSources.map((src, idx) => {
                        const isCited = citedSources.some((c) => c.publisher === src.domain);
                        return (
                          <div key={`${src.domain}-${idx}`} className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/20 flex items-start justify-between gap-3 text-xs leading-relaxed hover:border-slate-700/80 transition-colors">
                            <div className="space-y-1 truncate">
                              <p className="font-semibold text-slate-300 truncate">{src.title}</p>
                              <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-[10px] font-mono text-slate-500 hover:text-indigo-400 hover:underline block truncate">
                                {src.url}
                              </a>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[8px] font-mono font-bold tracking-wider shrink-0 uppercase border ${
                              isCited 
                                ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" 
                                : "bg-slate-950 text-slate-500 border-slate-800"
                            }`}>
                              {isCited ? "Cited" : "Scanned"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      </section>

      <section className="space-y-3 border-t border-border pt-6">
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-500">
          <GitPullRequest className="w-4 h-4" />
          <span className="uppercase font-semibold tracking-wider">6. Integrity Audit Log</span>
        </div>
        <div className="pl-6 font-mono text-[10px] text-slate-500 space-y-1">
          {events.slice(-5).map((evt) => (
            <p key={evt.id}>* {evt.event_type}: {evt.description}</p>
          ))}
        </div>
      </section>
    </div>
  );
}
