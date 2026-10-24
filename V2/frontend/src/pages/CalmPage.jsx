import React, { useState, useEffect, useRef } from "react";
import PebbleMascot3D from "../components/PebbleMascot3D";
import PebbleStudioModal from "../components/PebbleStudioModal";
import soundEngine from "../services/soundEngine";

export default function CalmPage() {
  const [activeTab, setActiveTab] = useState("breathing"); // "breathing" | "grounding"

  // Breathing state
  const [rhythm, setRhythm] = useState("box"); // "box" (4-4-4-4), "relaxing" (4-7-8), "balanced" (5-5)
  const [duration, setDuration] = useState(180); // seconds
  const [isRunning, setIsRunning] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [mascotMode, setMascotMode] = useState("3d"); // "3d" | "2d"
  const [isStudioOpen, setIsStudioOpen] = useState(false);

  // Phases logic
  const rhythmsConfig = {
    box: [
      { name: "Breathe in", seconds: 4, startScale: 0.92, endScale: 1.15 },
      { name: "Hold gently", seconds: 4, startScale: 1.15, endScale: 1.15 },
      { name: "Breathe out", seconds: 4, startScale: 1.15, endScale: 0.9 },
      { name: "Hold", seconds: 4, startScale: 0.9, endScale: 0.9 },
    ],
    relaxing: [
      { name: "Breathe in", seconds: 4, startScale: 0.9, endScale: 1.2 },
      { name: "Hold gently", seconds: 7, startScale: 1.2, endScale: 1.2 },
      { name: "Breathe out", seconds: 8, startScale: 1.2, endScale: 0.88 },
    ],
    balanced: [
      { name: "Breathe in", seconds: 5, startScale: 0.92, endScale: 1.15 },
      { name: "Breathe out", seconds: 5, startScale: 1.15, endScale: 0.92 },
    ],
  };

  const currentPhases = rhythmsConfig[rhythm];
  const totalCycleSeconds = currentPhases.reduce((sum, p) => sum + p.seconds, 0);
  const [cycleTime, setCycleTime] = useState(0);

  // High-precision smooth animation frame loop (60fps continuous glide)
  useEffect(() => {
    if (!isRunning) return;

    let animId;
    let lastTimestamp = performance.now();

    const loop = (now) => {
      const deltaSec = Math.min((now - lastTimestamp) / 1000, 0.1);
      lastTimestamp = now;

      setCycleTime((prev) => {
        const next = prev + deltaSec;
        if (next >= totalCycleSeconds) {
          return next % totalCycleSeconds;
        }
        return next;
      });

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [isRunning, totalCycleSeconds]);

  // Compute active phase, remaining time, and smooth progress from continuous cycleTime
  let accumulated = 0;
  let activePhaseIndex = 0;
  let phaseElapsed = 0;

  for (let i = 0; i < currentPhases.length; i++) {
    const p = currentPhases[i];
    if (cycleTime < accumulated + p.seconds) {
      activePhaseIndex = i;
      phaseElapsed = cycleTime - accumulated;
      break;
    }
    accumulated += p.seconds;
  }

  const activePhase = currentPhases[activePhaseIndex];
  const secondsRemaining = Math.max(1, Math.ceil(activePhase.seconds - phaseElapsed));
  const overallProgress = Math.min(1, Math.max(0, cycleTime / totalCycleSeconds));

  // Dynamic smooth scaling for the breathing circle
  const phaseProgressFrac = Math.min(1, Math.max(0, phaseElapsed / activePhase.seconds));
  const currentScale =
    activePhase.startScale +
    (activePhase.endScale - activePhase.startScale) * phaseProgressFrac;

  // Gentle Tibetan Singing Bowl Chime on phase transition
  const prevPhaseRef = useRef(activePhaseIndex);
  useEffect(() => {
    if (prevPhaseRef.current !== activePhaseIndex) {
      prevPhaseRef.current = activePhaseIndex;
      if (soundEnabled) {
        const pitches = [528, 660, 432, 396];
        soundEngine.playChime(pitches[activePhaseIndex % pitches.length]);
      }
    }
  }, [activePhaseIndex, soundEnabled]);

  // Grounding Checklist State
  const [groundingStep, setGroundingStep] = useState(1);
  const groundingSteps = [
    { step: 1, count: 5, sense: "Sight", prompt: "Acknowledge 5 things you see around you.", sub: "A pattern on the wall, light reflecting off a surface, an unmoving shadow." },
    { step: 2, count: 4, sense: "Touch", prompt: "Acknowledge 4 things you can physically touch.", sub: "The cold fabric of your sleeves, the texture of your desk, your feet planted on the floor." },
    { step: 3, count: 3, sense: "Sound", prompt: "Acknowledge 3 things you hear right now.", sub: "A faint hum of an appliance, distant traffic, your own inhalation." },
    { step: 4, count: 2, sense: "Smell", prompt: "Acknowledge 2 things you can smell.", sub: "Cold morning air, faint pine or tea, clean linen." },
    { step: 5, count: 1, sense: "Taste", prompt: "Acknowledge 1 thing you can taste.", sub: "A sip of water, or simply the neutral stillness of your mouth." },
  ];

  return (
    <div className="w-full max-w-[1240px] xl:max-w-[1360px] mx-auto px-6 lg:px-12 xl:px-16 py-8 flex flex-col gap-8 select-none">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between bg-surface-container-low px-6 py-3 rounded-2xl border border-surface-container-highest">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-lichen animate-pulse"></span>
          <span className="font-label-sm text-xs text-on-surface-variant uppercase tracking-wider">
            Somatic Pacing & Stillness Studio
          </span>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-surface-container p-1 rounded-xl border border-surface-container-highest text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("breathing")}
            className={`px-3 py-1 rounded-lg font-medium transition-colors ${
              activeTab === "breathing"
                ? "bg-primary text-on-primary shadow-sm"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            Breathing Pacing
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("grounding")}
            className={`px-3 py-1 rounded-lg font-medium transition-colors ${
              activeTab === "grounding"
                ? "bg-primary text-on-primary shadow-sm"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            5-4-3-2-1 Grounding
          </button>
        </div>
      </div>

      {activeTab === "breathing" ? (
        <>
          {/* Rhythm, Duration & Sound Control Bar */}
          <div className="bg-surface-container-low rounded-2xl p-6 border border-surface-container-highest flex flex-col md:flex-row md:items-center justify-between gap-6">
            {/* Rhythm Selector */}
            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-xs text-secondary uppercase tracking-wider font-semibold">
                Rhythm Pattern
              </span>
              <div className="flex flex-wrap items-center gap-2">
                {[
                  { id: "box", label: "Box (4-4-4-4)" },
                  { id: "relaxing", label: "Relaxing (4-7-8)" },
                  { id: "balanced", label: "Balanced (5-5)" },
                ].map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => {
                      setRhythm(r.id);
                      setCycleTime(0);
                    }}
                    className={`px-3.5 py-1.5 rounded-xl font-label-md text-xs transition-colors ${
                      rhythm === r.id
                        ? "bg-primary-container text-on-primary font-semibold"
                        : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Duration Selector */}
            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-xs text-secondary uppercase tracking-wider font-semibold">
                Target Duration
              </span>
              <div className="flex flex-wrap items-center gap-2">
                {[
                  { val: 60, label: "1 min" },
                  { val: 180, label: "3 min" },
                  { val: 300, label: "5 min" },
                  { val: 9999, label: "No limit" },
                ].map((d) => (
                  <button
                    key={d.val}
                    type="button"
                    onClick={() => setDuration(d.val)}
                    className={`px-3 py-1.5 rounded-xl font-label-md text-xs transition-colors ${
                      duration === d.val
                        ? "bg-primary-container text-on-primary font-semibold"
                        : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Sound Toggle */}
            <div className="flex flex-col gap-2 shrink-0">
              <span className="font-label-sm text-xs text-secondary uppercase tracking-wider font-semibold">
                Chime
              </span>
              <button
                type="button"
                onClick={() => setSoundEnabled(!soundEnabled)}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-surface-container text-on-surface-variant hover:bg-surface-container-high transition-colors text-xs font-medium"
              >
                <span className="material-symbols-outlined text-[16px]">
                  {soundEnabled ? "volume_up" : "volume_off"}
                </span>
                <span>{soundEnabled ? "Active" : "Muted"}</span>
              </button>
            </div>

            {/* Mascot View Mode Toggle */}
            <div className="flex flex-col gap-2 shrink-0">
              <span className="font-label-sm text-xs text-secondary uppercase tracking-wider font-semibold">
                Pebble Stone
              </span>
              <div className="flex items-center gap-1 bg-surface-container p-1 rounded-xl">
                <button
                  type="button"
                  onClick={() => setMascotMode("3d")}
                  className={`px-3 py-1 rounded-lg text-xs font-label transition-colors ${
                    mascotMode === "3d" ? "bg-surface text-primary font-medium shadow-xs" : "text-secondary hover:text-on-surface"
                  }`}
                >
                  3D Stone
                </button>
                <button
                  type="button"
                  onClick={() => setMascotMode("2d")}
                  className={`px-3 py-1 rounded-lg text-xs font-label transition-colors ${
                    mascotMode === "2d" ? "bg-surface text-primary font-medium shadow-xs" : "text-secondary hover:text-on-surface"
                  }`}
                >
                  2D Print
                </button>
              </div>
            </div>
          </div>

          {/* Breathing Circle Stage */}
          <div className="bg-surface-container-low rounded-3xl p-10 border border-surface-container-highest flex flex-col items-center justify-center relative min-h-[460px] shadow-sm">
            <div className="relative w-72 sm:w-88 h-72 sm:h-88 flex items-center justify-center">
              {/* Outer Progress Ring — Smooth 60fps RAF Glide completing the full 360-degree circle */}
              <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 380 380">
                {/* Background Ring Track */}
                <circle
                  cx="190"
                  cy="190"
                  r="170"
                  fill="none"
                  stroke="#DDE2DA"
                  strokeWidth="6"
                />
                {/* Active Outer Green Loop */}
                <circle
                  cx="190"
                  cy="190"
                  r="170"
                  fill="none"
                  stroke="#2E4B3F"
                  strokeWidth="7"
                  strokeDasharray="1068.14"
                  strokeDashoffset={1068.14 * (1 - overallProgress)}
                  strokeLinecap="round"
                />
              </svg>

              {/* Inner Expanding Disc with Continuous Organic Scale */}
              <div
                style={{ transform: `scale(${currentScale})` }}
                className="w-60 sm:w-72 h-60 sm:h-72 rounded-full bg-surface-container border border-surface-container-highest flex flex-col items-center justify-center text-center p-3 shadow-inner transition-transform duration-100 ease-out"
              >
                {/* Contemplative Breathing 3D Pebble */}
                <div className="w-20 h-20 shrink-0 mb-1 flex items-center justify-center pointer-events-none overflow-hidden">
                  <PebbleMascot3D
                    pose={isRunning ? "breathing" : "welcome"}
                    interactive={false}
                    showControls={false}
                    showRipples={false}
                    className="w-full h-full"
                  />
                </div>

                <h2 className="font-headline-lg text-xl sm:text-2xl font-serif text-primary mb-0.5 leading-tight">
                  {activePhase.name}
                </h2>
                <div className="font-body-lg text-xs text-on-surface-variant font-medium">
                  {secondsRemaining}s remaining
                </div>
                <div className="font-label-sm text-[10px] text-secondary tracking-widest uppercase mt-0.5">
                  Phase {activePhaseIndex + 1} of {currentPhases.length}
                </div>
              </div>
            </div>

            {/* Direct Flow Controls */}
            <div className="flex items-center gap-3 mt-8">
              <button
                type="button"
                onClick={() => setIsRunning(!isRunning)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-surface-container text-primary font-label-md text-xs font-semibold hover:bg-surface-container-high transition-colors"
              >
                <span className="material-symbols-outlined text-[18px]">
                  {isRunning ? "pause" : "play_arrow"}
                </span>
                <span>{isRunning ? "Pause" : "Resume"}</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setPhaseIndex(0);
                  setSecondsInPhase(0);
                  setElapsedSeconds(0);
                }}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-container text-secondary hover:text-on-surface hover:bg-surface-container-high transition-colors text-xs font-medium"
                title="Reset session"
              >
                <span className="material-symbols-outlined text-[18px]">restart_alt</span>
                <span>Reset</span>
              </button>
            </div>
          </div>
        </>
      ) : (
        /* 5-4-3-2-1 Sensory Grounding Wizard */
        <div className="bg-surface-container-low rounded-3xl p-8 lg:p-12 border border-surface-container-highest flex flex-col gap-8 shadow-sm">
          <div className="flex flex-col gap-2">
            <span className="font-label-sm text-xs uppercase tracking-widest text-secondary font-semibold">
              Somatic Re-orientation • Step {groundingStep} of 5
            </span>
            <h2 className="font-headline-lg text-2xl lg:text-3xl font-serif text-primary">
              {groundingSteps[groundingStep - 1].prompt}
            </h2>
            <p className="font-body-md text-sm text-on-surface-variant leading-relaxed max-w-xl">
              {groundingSteps[groundingStep - 1].sub}
            </p>
          </div>

          <div className="flex flex-col gap-3 py-2">
            {[...Array(groundingSteps[groundingStep - 1].count)].map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-3 p-3.5 rounded-xl bg-surface-container-lowest border border-surface-container-highest"
              >
                <span className="w-6 h-6 rounded-full bg-surface-container text-primary flex items-center justify-center font-serif text-xs font-semibold">
                  {i + 1}
                </span>
                <input
                  type="text"
                  placeholder={`Notice detail ${i + 1} in your surroundings...`}
                  className="w-full bg-transparent border-none text-xs text-on-surface placeholder:text-outline focus:outline-none"
                />
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-surface-container-high">
            <button
              type="button"
              disabled={groundingStep <= 1}
              onClick={() => setGroundingStep((s) => Math.max(1, s - 1))}
              className="px-4 py-2 rounded-xl border border-surface-container-highest text-xs font-medium text-secondary hover:text-on-surface disabled:opacity-30"
            >
              Previous sense
            </button>

            {groundingStep < 5 ? (
              <button
                type="button"
                onClick={() => setGroundingStep((s) => Math.min(5, s + 1))}
                className="px-5 py-2 rounded-xl bg-primary text-on-primary font-label-md text-xs font-medium hover:bg-primary-container transition-colors"
              >
                Next Step
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  alert("Grounding complete. Notice your breathing and grounded feet.");
                  setGroundingStep(1);
                  setActiveTab("breathing");
                }}
                className="px-5 py-2 rounded-xl bg-primary text-on-primary font-label-md text-xs font-medium hover:bg-primary-container transition-colors"
              >
                Complete Grounding
              </button>
            )}
          </div>
        </div>
      )}

      {/* 3D Pebble Studio Fullscreen Modal */}
      <PebbleStudioModal
        isOpen={isStudioOpen}
        onClose={() => setIsStudioOpen(false)}
      />
    </div>
  );
}
