import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PebbleMascot3D from "../components/PebbleMascot3D";
import soundEngine from "../services/soundEngine";

export default function LandingPage() {
  const [activeSound, setActiveSound] = useState(null);

  useEffect(() => {
    return () => {
      soundEngine.stop(0.3);
    };
  }, []);

  const handleToggleSound = (id) => {
    if (activeSound === id) {
      soundEngine.stop();
      setActiveSound(null);
    } else {
      soundEngine.play(id);
      setActiveSound(id);
    }
  };

  const sounds = [
    { id: "rain", label: "Cold Rainfall", freq: "432 Hz", desc: "Steady drops upon river slate" },
    { id: "stream", label: "Glacial Melt", freq: "528 Hz", desc: "Rippling water through granite beds" },
    { id: "wind", label: "Mountain Stillness", freq: "396 Hz", desc: "Low altitude alpine draft" },
  ];

  return (
    <div className="w-full flex flex-col items-center select-none">
      {/* Hero Section: Monograph Presentation */}
      <section className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 pt-12 lg:pt-16 pb-16">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container border border-surface-container-highest text-secondary font-label-sm text-xs tracking-widest uppercase mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-lichen animate-pulse"></span>
            <span>Monograph / Public Record • Revision 2026</span>
          </div>

          <h1 className="font-display-lg text-4xl sm:text-5xl lg:text-6xl text-primary font-normal tracking-tight font-serif leading-[1.15] mb-6">
            A quiet, unobserved space for your interior life.
          </h1>

          <p className="font-body-lg text-lg lg:text-xl text-on-surface-variant max-w-2xl font-light leading-relaxed">
            No surveillance algorithms, no emotional scoring, no telemetry relays. Simply a private vessel made of stone, local memory, and silence.
          </p>
        </div>

        {/* Monumental Landscape Art: Circular Riverbed Stone Ripple */}
        <div className="relative w-full max-w-4xl mx-auto flex flex-col items-center justify-center my-6">
          <div className="absolute inset-0 m-auto w-[420px] h-[420px] lg:w-[520px] lg:h-[520px] rounded-full border border-surface-container-highest/80 -z-0 pointer-events-none"></div>
          <div className="absolute inset-0 m-auto w-[520px] h-[520px] lg:w-[640px] lg:h-[640px] rounded-full border border-surface-container-highest/40 -z-0 pointer-events-none"></div>

          <div className="absolute -top-4 right-4 lg:right-24 bg-surface-container-low border border-surface-container-highest px-3.5 py-1.5 rounded-lg font-mono text-[11px] text-secondary tracking-tight z-20 flex items-center gap-2 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-lichen"></span>
            <span>Zero External Calls</span>
          </div>

          {/* Central Circular Riverbed Art featuring Official Pebble Mascot */}
          <div className="relative z-10 w-72 h-72 sm:w-88 sm:h-88 lg:w-[420px] lg:h-[420px] rounded-full overflow-hidden border-4 border-surface-container-lowest bg-surface-container shadow-md flex items-center justify-center">
            <PebbleMascot3D
              pose="welcome"
              interactive={true}
              showControls={false}
              showRipples={true}
              autoRotate={false}
              className="w-full h-full"
            />
          </div>

          <div className="mt-5 text-center max-w-md flex flex-col items-center">
            <p className="font-label-sm text-xs text-secondary tracking-widest uppercase">
              Figure 01. The Unindexed Bedrock
            </p>
            <p className="font-body-sm text-xs text-outline mt-1.5 italic font-serif leading-relaxed">
              "Like river stones smoothed beneath dark cold currents, human thoughts deserve dissolution without archival harvesting."
            </p>
          </div>
        </div>

        {/* CTA Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
          <Link
            to="/talk"
            className="w-full sm:w-auto text-center bg-primary text-on-primary font-label-md text-sm uppercase tracking-wider py-4 px-8 rounded-full hover:bg-primary-container transition-all flex items-center justify-center gap-3 group shadow-sm"
          >
            <span>Begin Writing in Sanctuary</span>
            <span className="material-symbols-outlined text-base group-hover:translate-x-1 transition-transform">
              arrow_forward
            </span>
          </Link>
          <Link
            to="/privacy"
            className="w-full sm:w-auto text-center border border-outline-variant bg-surface-container-lowest text-on-surface font-label-md text-sm uppercase tracking-wider py-4 px-8 rounded-full hover:bg-surface-container transition-all"
          >
            Explore Privacy Ledger
          </Link>
        </div>
      </section>

      {/* Pillars Section: The Four Architectural Foundations */}
      <section className="w-full bg-surface-container-low border-y border-surface-container-highest py-16 px-6 lg:px-12 xl:px-16">
        <div className="max-w-[1540px] mx-auto">
          <div className="flex flex-col items-center text-center max-w-2xl mx-auto mb-16">
            <span className="font-label-sm text-xs uppercase tracking-widest text-secondary mb-2">
              Architectural Tenets
            </span>
            <h2 className="font-headline-lg text-3xl lg:text-4xl font-serif text-primary">
              Principles of quiet permanence.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Tenet 1 */}
            <div className="bg-surface-container-lowest p-8 rounded-2xl border border-surface-container-highest flex flex-col justify-between gap-6">
              <div className="flex flex-col gap-3">
                <span className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center text-primary font-serif font-bold text-sm">
                  01
                </span>
                <h3 className="font-headline-sm text-xl font-serif text-primary">Stone-like Stillness</h3>
                <p className="font-body-sm text-on-surface-variant leading-relaxed">
                  Zero gamified streaks, badges, notifications, or engagement loops. Sanctuary waits quietly until you arrive, and recedes when you are done.
                </p>
              </div>
              <span className="font-label-sm text-xs text-secondary">No algorithmic push</span>
            </div>

            {/* Tenet 2 */}
            <div className="bg-surface-container-lowest p-8 rounded-2xl border border-surface-container-highest flex flex-col justify-between gap-6">
              <div className="flex flex-col gap-3">
                <span className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center text-primary font-serif font-bold text-sm">
                  02
                </span>
                <h3 className="font-headline-sm text-xl font-serif text-primary">Client-Side Cipher</h3>
                <p className="font-body-sm text-on-surface-variant leading-relaxed">
                  Names, entities, locations, and personal timestamps are masked in your browser's isolated memory before any reflection synthesis takes place.
                </p>
              </div>
              <span className="font-label-sm text-xs text-secondary">Zero raw identity transmission</span>
            </div>

            {/* Tenet 3 */}
            <div className="bg-surface-container-lowest p-8 rounded-2xl border border-surface-container-highest flex flex-col justify-between gap-6">
              <div className="flex flex-col gap-3">
                <span className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center text-primary font-serif font-bold text-sm">
                  03
                </span>
                <h3 className="font-headline-sm text-xl font-serif text-primary">Companion Fade</h3>
                <p className="font-body-sm text-on-surface-variant leading-relaxed">
                  When you reach resolution and clarity, Sanctuary intentionally shortens its presence and encourages you to set the notebook down and reconnect with the world.
                </p>
              </div>
              <span className="font-label-sm text-xs text-secondary">Anti-dependency protocol</span>
            </div>

            {/* Tenet 4 */}
            <div className="bg-surface-container-lowest p-8 rounded-2xl border border-surface-container-highest flex flex-col justify-between gap-6">
              <div className="flex flex-col gap-3">
                <span className="w-8 h-8 rounded-lg bg-surface-container flex items-center justify-center text-primary font-serif font-bold text-sm">
                  04
                </span>
                <h3 className="font-headline-sm text-xl font-serif text-primary">Non-Diagnostic Space</h3>
                <p className="font-body-sm text-on-surface-variant leading-relaxed">
                  Reflective contemplation, never clinical diagnosis or therapy. Sanctuary reflects the shape of your sentences without affixing pathology labels.
                </p>
              </div>
              <span className="font-label-sm text-xs text-secondary">Pure contemplative inquiry</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stillness & Ambient Sound Station */}
      <section className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 py-16">
        <div className="bg-surface-container-low rounded-3xl p-8 lg:p-14 border border-surface-container-highest flex flex-col lg:flex-row items-center justify-between gap-10">
          <div className="flex flex-col gap-4 max-w-xl">
            <span className="font-label-sm text-xs uppercase tracking-widest text-secondary">
              Contemplative Acoustics
            </span>
            <h2 className="font-headline-lg text-3xl font-serif text-primary">
              The Riverstone Sound Station.
            </h2>
            <p className="font-body-md text-on-surface-variant leading-relaxed">
              Quiet natural acoustic frequencies to anchor your breathing and writing. Recorded in glacial basins and mountain streams without synthetic synthesizer tones.
            </p>
            <div className="flex items-center gap-3 pt-2">
              <Link
                to="/calm"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-on-primary font-label-md text-xs uppercase tracking-wider hover:bg-primary-container transition-colors"
              >
                <span>Open Calm & Breathing Studio</span>
                <span className="material-symbols-outlined text-sm">spa</span>
              </Link>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full lg:w-96">
            {sounds.map((s) => {
              const isPlaying = activeSound === s.id;
              return (
                <button
                  key={s.id}
                  onClick={() => handleToggleSound(s.id)}
                  type="button"
                  className={`p-4 rounded-xl border transition-all text-left flex items-center justify-between ${
                    isPlaying
                      ? "bg-secondary-container border-secondary text-primary shadow-sm"
                      : "bg-surface-container-lowest border-surface-container-highest hover:bg-surface-container text-on-surface"
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-label-md text-sm font-semibold">{s.label}</span>
                    <span className="font-body-sm text-xs text-secondary">{s.desc}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] text-outline">{s.freq}</span>
                    <span className="material-symbols-outlined text-lg text-primary">
                      {isPlaying ? "volume_up" : "play_circle"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t border-surface-container-highest py-12 px-6 lg:px-12 bg-surface-container-lowest">
        <div className="max-w-[1540px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6 text-xs text-secondary">
          <div className="flex items-center gap-3 font-serif">
            <span className="font-semibold text-primary">Sanctuary</span>
            <span>•</span>
            <span>Revision 2026 Public Monograph</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/talk" className="hover:text-primary transition-colors">Talk</Link>
            <Link to="/how-this-was-read" className="hover:text-primary transition-colors">How This Was Read</Link>
            <Link to="/moments" className="hover:text-primary transition-colors">Moments</Link>
            <Link to="/calm" className="hover:text-primary transition-colors">Calm</Link>
            <Link to="/privacy" className="hover:text-primary transition-colors">Privacy Ledger</Link>
            <a href="tel:988" className="text-surface-tint font-medium hover:underline">Crisis Lifeline: 988</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
