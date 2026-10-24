import React, { useState } from "react";
import { HISTORICAL_MEMORIES } from "../data/historicalChats";

export default function MomentsPage() {
  const [viewMode, setViewMode] = useState("cairns"); // "cairns" | "list"
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMoment, setSelectedMoment] = useState(null);

  const [moments, setMoments] = useState(() => {
    try {
      const stored = localStorage.getItem("sanctuary_moments");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed.some((m) => m.id === "mem-achievement")) {
          return parsed;
        }
      }
    } catch (e) {}
    try {
      localStorage.setItem("sanctuary_moments", JSON.stringify(HISTORICAL_MEMORIES));
    } catch (e) {}
    return HISTORICAL_MEMORIES;
  });

  const filteredMoments = moments.filter(
    (m) =>
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.quote.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 py-8 flex flex-col gap-8 select-none">
      {/* Page Header & Atmospheric Bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-4 border-b border-surface-container-highest">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-primary shadow-2xs">
            <span className="material-symbols-outlined text-[24px] text-secondary">eco</span>
          </div>
          <div className="flex flex-col gap-1">
            <h1 className="text-primary text-3xl sm:text-4xl font-normal tracking-tight font-serif">
              Moments
            </h1>
            <p className="text-on-surface-variant text-sm sm:text-base font-normal leading-relaxed">
              A few words worth keeping. Nurtured in stone.
            </p>
          </div>
        </div>

        {/* Controls: Search & View Toggle */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative w-full sm:w-[260px] h-10">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
              <span className="material-symbols-outlined text-[18px]">search</span>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search kept words or titles..."
              className="w-full h-full bg-surface-container border border-surface-container-highest text-on-surface placeholder:text-outline text-xs rounded-xl pl-9 pr-3 focus:outline-none focus:border-primary transition-all"
            />
          </div>

          {/* Segmented Control */}
          <div className="flex items-center bg-surface-container-high p-1 rounded-xl border border-surface-container-highest h-10">
            <button
              type="button"
              onClick={() => setViewMode("cairns")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "cairns"
                  ? "bg-surface-container-lowest text-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">filter_hdr</span>
              <span>Cairns</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("list")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === "list"
                  ? "bg-surface-container-lowest text-primary shadow-sm"
                  : "text-on-surface-variant hover:text-on-surface"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">view_agenda</span>
              <span>List</span>
            </button>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs text-secondary bg-surface-container px-3 py-2 rounded-lg border border-surface-container-highest">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
            <span>Sorted by recency · {filteredMoments.length} stones placed</span>
          </div>
        </div>
      </div>

      {/* Cairns View (Zen Sand Pattern Meditation Ground) */}
      {viewMode === "cairns" && (
        <section
          aria-label="Cairns landscape meditation ground"
          className="relative w-full rounded-3xl zen-sand-pattern border border-[#D5DAD2] min-h-[560px] p-8 lg:p-14 overflow-hidden shadow-inner flex flex-col justify-between"
        >
          {/* Subtle Vector Raked Sand Ridges */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none stroke-[#CBD2C6] stroke-[0.85] fill-none opacity-60"
            viewBox="0 0 1000 600"
            preserveAspectRatio="none"
          >
            <path d="M-50,120 Q 250,80 550,130 T 1050,100" />
            <path d="M-50,240 Q 300,210 650,260 T 1050,220" />
            <path d="M-50,380 Q 200,350 600,400 T 1050,360" />
            <path d="M-50,500 Q 350,470 700,530 T 1050,490" />
            {/* Concentric ripples around placement sites */}
            <ellipse cx="240" cy="220" rx="120" ry="50" strokeDasharray="3 4" />
            <ellipse cx="740" cy="190" rx="130" ry="55" strokeDasharray="4 5" />
            <ellipse cx="280" cy="450" rx="140" ry="60" strokeDasharray="3 5" />
            <ellipse cx="760" cy="430" rx="130" ry="55" strokeDasharray="4 5" />
          </svg>

          {/* 4 Interactive Cairn Clusters */}
          <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-y-12 gap-x-12 items-start">
            {filteredMoments.map((m, idx) => (
              <article
                key={m.id}
                onClick={() => setSelectedMoment(m)}
                className="group relative flex flex-col sm:flex-row items-center sm:items-end gap-6 p-4 rounded-2xl transition-all duration-300 hover:bg-[#F2F5F0]/80 border border-transparent hover:border-[#CCD4C7] cursor-pointer"
              >
                {/* Interactive Cairn SVG Graphic */}
                <div className="relative w-32 h-36 flex items-end justify-center shrink-0">
                  <div className="absolute bottom-1 w-24 h-4 bg-[#303832]/10 rounded-full blur-[3px]"></div>
                  <svg
                    className="w-28 h-32 relative z-10 stone-hover-transition group-hover:-translate-y-2"
                    viewBox="0 0 130 140"
                    fill="none"
                  >
                    {/* Bottom Stone */}
                    <path
                      d="M12 118 C10 102, 28 92, 65 92 C102 92, 122 102, 118 118 C115 132, 98 138, 65 138 C28 138, 14 132, 12 118 Z"
                      fill="#A9A79B"
                      stroke="#8E8B7F"
                      strokeWidth="1.25"
                    />
                    <path d="M30 114 Q 62 108 98 122" stroke="#E5E8E0" strokeWidth="1" strokeLinecap="round" opacity="0.65" />

                    {/* Middle Stone */}
                    <path
                      d="M26 78 C24 64, 40 56, 66 56 C92 56, 108 64, 104 78 C100 90, 86 96, 66 96 C42 96, 28 90, 26 78 Z"
                      fill="#9E9C91"
                      stroke="#838176"
                      strokeWidth="1.25"
                    />
                    <path d="M42 74 Q 68 68 90 82" stroke="#E3E6DF" strokeWidth="0.85" strokeLinecap="round" opacity="0.55" />

                    {/* Top Stone */}
                    <path
                      d="M42 42 C40 30, 52 24, 68 24 C84 24, 94 30, 92 42 C90 52, 80 56, 68 56 C52 56, 44 52, 42 42 Z"
                      fill="#B5B3A8"
                      stroke="#9A988D"
                      strokeWidth="1.25"
                    />
                    {/* Lichen Sprout on Top */}
                    <circle cx="76" cy="31" r="3" fill="#C4CF5A" />
                    <circle cx="79" cy="33" r="2" fill="#A8B548" />
                  </svg>
                </div>

                {/* Cairn Description Card */}
                <div className="flex-1 flex flex-col gap-1.5 text-left">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-secondary">
                      {m.date}
                    </span>
                    {m.transition && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#E4EAE1] text-[#2E4B3F] font-medium border border-[#D5DCD2]">
                        Centering: {m.transition}
                      </span>
                    )}
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xs font-semibold text-primary flex items-center gap-0.5">
                      <span>Inspect stone</span>
                      <span className="material-symbols-outlined text-[13px]">arrow_forward</span>
                    </span>
                  </div>
                  <h2 className="font-serif text-lg font-medium text-[#23261F] leading-snug">
                    {m.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-[#454B40] leading-relaxed italic bg-[#F6F8F4]/80 p-3 rounded-xl border border-[#DCE2DB]">
                    "{m.quote}"
                  </p>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      {/* List View */}
      {viewMode === "list" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredMoments.map((m) => (
            <div
              key={m.id}
              onClick={() => setSelectedMoment(m)}
              className="p-6 rounded-2xl bg-surface-container-lowest border border-surface-container-highest hover:border-primary transition-all cursor-pointer flex flex-col justify-between gap-4"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs text-secondary">
                  <span>{m.date}</span>
                  <div className="flex items-center gap-2">
                    {m.transition && (
                      <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-mono text-[10px] font-medium">
                        {m.transition}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">landscape</span>
                      <span>{m.stoneCount || m.stones || 3} stones</span>
                    </span>
                  </div>
                </div>
                <h3 className="font-serif text-xl font-medium text-primary">{m.title}</h3>
                <blockquote className="text-sm font-serif italic text-on-surface border-l-2 border-primary/30 pl-3 my-1">
                  "{m.quote}"
                </blockquote>
                <p className="text-xs text-on-surface-variant leading-relaxed">{m.context}</p>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-surface-container-high">
                {m.tags.map((t, i) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-surface-container text-[11px] text-secondary font-medium">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal for Selected Moment */}
      {selectedMoment && (
        <div
          onClick={() => setSelectedMoment(null)}
          className="fixed inset-0 z-50 bg-[#17231E]/60 backdrop-blur-md flex items-center justify-center p-6"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg bg-surface-container-lowest rounded-3xl p-8 border border-surface-container-highest shadow-2xl flex flex-col gap-6"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-primary shrink-0">
                  <span className="material-symbols-outlined text-[20px] text-secondary">bookmark_added</span>
                </div>
                <div className="flex flex-col">
                  <span className="font-label-sm text-xs uppercase tracking-wider text-secondary">
                    {selectedMoment.date} • Placed Cairn
                  </span>
                  <h2 className="font-serif text-2xl font-medium text-primary mt-0.5">
                    {selectedMoment.title}
                  </h2>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMoment(null)}
                className="p-1 rounded-lg hover:bg-surface-container text-on-surface-variant"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <blockquote className="p-4 rounded-xl bg-surface-container-low border border-surface-container-highest text-base font-serif italic text-on-surface leading-relaxed">
              "{selectedMoment.quote}"
            </blockquote>

            <div className="flex flex-col gap-1.5 text-xs text-on-surface-variant">
              <span className="font-label-sm uppercase tracking-wider text-secondary">Reflection Context</span>
              <p className="leading-relaxed">{selectedMoment.context}</p>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-surface-container-high">
              <div className="flex items-center gap-1.5">
                {selectedMoment.tags.map((t, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-surface-container text-[10px] text-secondary font-medium">
                    #{t}
                  </span>
                ))}
              </div>
              <button
                type="button"
                onClick={() => setSelectedMoment(null)}
                className="px-4 py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-xs"
              >
                Close stone
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
