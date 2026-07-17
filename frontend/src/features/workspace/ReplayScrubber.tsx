import { useEffect } from "react";
import { Play, Pause, ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";

interface ReplayScrubberProps {
  maxSteps: number;
  currentStep: number;
  onChangeStep: (step: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onReset: () => void;
}

export function ReplayScrubber({
  maxSteps,
  currentStep,
  onChangeStep,
  isPlaying,
  onTogglePlay,
  onReset,
}: ReplayScrubberProps) {
  // Replay ticks checkpoints
  const checkpoints = [
    { label: "Plan", step: 0 },
    { label: "Ingest", step: Math.round(maxSteps * 0.25) },
    { label: "Passages", step: Math.round(maxSteps * 0.5) },
    { label: "Claims", step: Math.round(maxSteps * 0.75) },
    { label: "Verdict", step: maxSteps },
  ];

  // Auto-play interval effect
  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      interval = setInterval(() => {
        if (currentStep < maxSteps) {
          onChangeStep(currentStep + 1);
        } else {
          onTogglePlay(); // stop at end
        }
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, currentStep, maxSteps, onChangeStep, onTogglePlay]);

  return (
    <div className="h-14 border-t border-border px-6 flex items-center justify-between bg-slate-900/60 backdrop-blur-md select-none shrink-0">
      {/* Controls */}
      <div className="flex items-center space-x-1.5 shrink-0">
        <button
          onClick={onReset}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Reset"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => onChangeStep(Math.max(0, currentStep - 1))}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Step Backward"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
          onClick={onTogglePlay}
          className="p-2 rounded-lg bg-brand hover:bg-brand-hover text-white transition-colors flex items-center justify-center"
          title={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
        </button>
        <button
          onClick={() => onChangeStep(Math.min(maxSteps, currentStep + 1))}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Step Forward"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Slider & checkpoints */}
      <div className="flex-1 max-w-2xl mx-8 flex flex-col justify-center space-y-1">
        <input
          type="range"
          min={0}
          max={maxSteps}
          value={currentStep}
          onChange={(e) => onChangeStep(parseInt(e.target.value))}
          className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-brand focus:outline-none"
        />

        {/* Checkpoint Indicators */}
        <div className="relative w-full flex justify-between px-1">
          {checkpoints.map((cp, idx) => {
            const isActive = currentStep >= cp.step;
            return (
              <button
                key={idx}
                onClick={() => onChangeStep(cp.step)}
                className={`text-[8px] font-mono transition-colors focus:outline-none ${
                  isActive ? "text-slate-200 font-semibold" : "text-slate-600"
                }`}
              >
                {cp.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Counter */}
      <div className="text-[10px] font-mono text-slate-500 shrink-0 select-none">
        Step {currentStep} / {maxSteps}
      </div>
    </div>
  );
}
