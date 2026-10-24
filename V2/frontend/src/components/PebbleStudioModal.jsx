import React, { useState, useEffect } from "react";
import PebbleMascot3D from "./PebbleMascot3D";

/**
 * PebbleStudioModal
 * 
 * Fullscreen contemplative 3D Zen sanctuary featuring the official
 * Sanctuary Pebble mascot in real-time Three.js.
 */
export default function PebbleStudioModal({ isOpen, onClose }) {
  const [activePose, setActivePose] = useState("welcome");
  const [ambientMood, setAmbientMood] = useState("studio"); // "studio", "dawn", "twilight"
  const [pokeTotal, setPokeTotal] = useState(0);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const moodStyles = {
    studio: "bg-[#F7FAF5]/95 text-primary border-outline-variant/30",
    dawn: "bg-[#FFF9F0]/95 text-[#2E281E] border-[#E8DDCB]/50",
    twilight: "bg-[#1E2522]/95 text-[#E6EFEA] border-[#36443E]/60",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 backdrop-blur-md bg-black/40 animate-fadeIn">
      <div
        className={`relative w-full max-w-3xl rounded-3xl border shadow-2xl overflow-hidden flex flex-col transition-colors duration-500 ${
          moodStyles[ambientMood]
        }`}
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant/20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
              01
            </div>
            <div>
              <h2 className="font-headline-sm text-lg font-serif tracking-tight">
                Pebble 3D Contemplative Studio
              </h2>
              <p className="font-label-sm text-[11px] text-secondary">
                Official Sanctuary Riverstone · Real-time 3D Sculpture
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Mood selector */}
            <div className="hidden sm:flex items-center gap-1 bg-surface-container-low p-1 rounded-full border border-outline-variant/30 text-xs">
              <button
                type="button"
                onClick={() => setAmbientMood("studio")}
                className={`px-2.5 py-1 rounded-full transition-all text-[11px] font-label ${
                  ambientMood === "studio"
                    ? "bg-surface text-primary font-medium shadow-xs"
                    : "text-secondary hover:text-on-surface"
                }`}
              >
                Studio
              </button>
              <button
                type="button"
                onClick={() => setAmbientMood("dawn")}
                className={`px-2.5 py-1 rounded-full transition-all text-[11px] font-label ${
                  ambientMood === "dawn"
                    ? "bg-[#FFF4E0] text-[#5A4520] font-medium shadow-xs"
                    : "text-secondary hover:text-on-surface"
                }`}
              >
                Dawn
              </button>
              <button
                type="button"
                onClick={() => setAmbientMood("twilight")}
                className={`px-2.5 py-1 rounded-full transition-all text-[11px] font-label ${
                  ambientMood === "twilight"
                    ? "bg-[#2A3530] text-[#A6D4B8] font-medium shadow-xs"
                    : "text-secondary hover:text-on-surface"
                }`}
              >
                Twilight
              </button>
            </div>

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-full hover:bg-surface-container transition-colors text-secondary hover:text-on-surface"
              title="Close 3D Studio (Esc)"
            >
              <span className="material-symbols-outlined text-xl">close</span>
            </button>
          </div>
        </div>

        {/* 3D Canvas Frame */}
        <div className="relative w-full h-[420px] sm:h-[480px] flex items-center justify-center p-4">
          <PebbleMascot3D
            pose={activePose}
            interactive={true}
            showControls={true}
            showRipples={true}
            autoRotate={false}
            className="w-full h-full max-w-md"
            onPoke={() => setPokeTotal((p) => p + 1)}
          />
        </div>

        {/* Bottom Contemplative Footnote */}
        <div className="px-6 py-3.5 bg-surface-container-low/60 border-t border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between text-[11px] text-secondary gap-2 font-label">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-lichen"></span>
            <span>Procedural Quartz Vein & Riverbed Granite · Zero Texture Downloads</span>
          </div>

          <div className="flex items-center gap-4">
            <span>Pokes received: {pokeTotal}</span>
            <span className="hidden sm:inline">·</span>
            <span>Press <kbd className="px-1 py-0.5 rounded bg-surface border border-outline-variant/40 font-mono text-[10px]">Esc</kbd> to return</span>
          </div>
        </div>
      </div>
    </div>
  );
}
