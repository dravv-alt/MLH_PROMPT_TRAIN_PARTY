import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { HISTORICAL_MEMORIES } from "../data/historicalChats";

export default function MomentsPage() {
  const [viewMode, setViewMode] = useState("cairns"); // "cairns" | "list"
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState("ALL");
  const [selectedMoment, setSelectedMoment] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [showGuide, setShowGuide] = useState(true);

  // Form state for creating a new moment
  const [newTitle, setNewTitle] = useState("");
  const [newQuote, setNewQuote] = useState("");
  const [newContext, setNewContext] = useState("");
  const [newStones, setNewStones] = useState(3);
  const [newTags, setNewTags] = useState("");

  const [moments, setMoments] = useState(() => {
    try {
      const stored = localStorage.getItem("sanctuary_moments");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      }
    } catch (e) {}
    try {
      localStorage.setItem("sanctuary_moments", JSON.stringify(HISTORICAL_MEMORIES));
    } catch (e) {}
    return HISTORICAL_MEMORIES;
  });

  // Extract all unique tags
  const allTags = useMemo(() => {
    const set = new Set();
    moments.forEach((m) => {
      if (Array.isArray(m.tags)) {
        m.tags.forEach((t) => set.add(t));
      }
    });
    return Array.from(set);
  }, [moments]);

  const filteredMoments = moments.filter((m) => {
    const matchesSearch =
      (m.title || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.quote || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.context || "").toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTag =
      selectedTag === "ALL" || (Array.isArray(m.tags) && m.tags.includes(selectedTag));
    return matchesSearch && matchesTag;
  });

  const handleSaveNewMoment = (e) => {
    e.preventDefault();
    if (!newQuote.trim()) return;

    const parsedTags = newTags
      .split(",")
      .map((t) => t.trim().replace(/^#/, ""))
      .filter(Boolean);

    const created = {
      id: `mem-${Date.now()}`,
      title: newTitle.trim() || "Kept Realization",
      date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
      quote: newQuote.trim(),
      context: newContext.trim() || "Personal reflection milestone placed by you.",
      stoneCount: Number(newStones) || 3,
      transition: "CONTINUE",
      tags: parsedTags.length > 0 ? parsedTags : ["Milestone", "Grounded"],
    };

    const updated = [created, ...moments];
    setMoments(updated);
    try {
      localStorage.setItem("sanctuary_moments", JSON.stringify(updated));
      const rawMem = localStorage.getItem("sanctuary_memories");
      const listMem = rawMem ? JSON.parse(rawMem) : [];
      listMem.unshift(created);
      localStorage.setItem("sanctuary_memories", JSON.stringify(listMem));
    } catch (err) {}

    // Reset and close
    setNewTitle("");
    setNewQuote("");
    setNewContext("");
    setNewStones(3);
    setNewTags("");
    setIsAddModalOpen(false);
  };

  const handleDeleteMoment = (id) => {
    if (!window.confirm("Dissolve this cairn stone? It will be removed from your kept moments.")) return;
    const updated = moments.filter((m) => m.id !== id);
    setMoments(updated);
    try {
      localStorage.setItem("sanctuary_moments", JSON.stringify(updated));
      const rawMem = localStorage.getItem("sanctuary_memories");
      if (rawMem) {
        const listMem = JSON.parse(rawMem).filter((m) => m.id !== id);
        localStorage.setItem("sanctuary_memories", JSON.stringify(listMem));
      }
    } catch (err) {}
    setSelectedMoment(null);
  };

  return (
    <div className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 py-8 flex flex-col gap-6 select-none">
      {/* Page Header & Atmospheric Bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-4 border-b border-surface-container-highest">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-primary shadow-2xs">
            <span className="material-symbols-outlined text-[24px] text-secondary">eco</span>
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <h1 className="text-primary text-3xl sm:text-4xl font-normal tracking-tight font-serif">
                Moments & Cairns
              </h1>
              <button
                type="button"
                onClick={() => setShowGuide((prev) => !prev)}
                className="text-xs px-2.5 py-1 rounded-full bg-surface-container border border-surface-container-highest text-secondary hover:text-primary transition-colors flex items-center gap-1"
                title="Toggle explanation of Moments"
              >
                <span className="material-symbols-outlined text-[14px]">info</span>
                <span>{showGuide ? "Hide concept" : "Why Cairns?"}</span>
              </button>
            </div>
            <p className="text-on-surface-variant text-sm sm:text-base font-normal leading-relaxed">
              Pivotal words worth keeping. Consecrated by you, nurtured in stone.
            </p>
          </div>
        </div>

        {/* Controls: Search, View Toggle, Place Stone */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full sm:w-[220px] h-10">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary">
              <span className="material-symbols-outlined text-[18px]">search</span>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search kept words..."
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

          {/* Place Stone Button */}
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary text-on-primary font-medium text-xs hover:bg-primary/90 transition-all shadow-sm h-10"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            <span>Place stone</span>
          </button>

          <Link
            to="/talk"
            className="hidden lg:flex items-center gap-1.5 px-3 py-2 rounded-xl bg-surface-container border border-surface-container-highest text-secondary hover:text-primary transition-all text-xs h-10"
            title="Open real-time conversation"
          >
            <span className="material-symbols-outlined text-[16px]">chat</span>
            <span>Talk</span>
          </Link>
        </div>
      </div>

      {/* Concept Explainer Banner: Why Cairns & What is a Moment */}
      {showGuide && (
        <aside
          aria-label="Moments Guide"
          className="relative bg-surface-container-low border border-surface-container-highest rounded-2xl p-5 sm:p-6 transition-all shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
        >
          <div className="flex items-start gap-4 flex-1">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 mt-0.5">
              <span className="material-symbols-outlined text-[20px]">landscape</span>
            </div>
            <div className="flex flex-col gap-1 text-xs sm:text-sm text-on-surface-variant leading-relaxed">
              <h2 className="font-serif text-base sm:text-lg font-medium text-primary">
                The Purpose of Moments & Cairns
              </h2>
              <p>
                <strong>Sovereign Agency over Memory:</strong> Most AI apps automatically summarize or psychoanalyze your feelings. Sanctuary does not. Here, <em>you</em> hold full narrative ownership—deciding which turns, realizations, and breakthroughs are consecrated into memory.
              </p>
              <p>
                <strong>Waymarkers on Foggy Paths:</strong> Like stone cairns stacked by travelers to mark a mountain trail, each stone placed here anchors a hard-won truth from your conversations. When you return to Sanctuary, these memories ground future reflections in your own authentic words.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowGuide(false)}
            className="self-end md:self-center shrink-0 px-3 py-1.5 rounded-lg border border-surface-container-highest bg-surface-container text-xs text-secondary hover:text-primary transition-colors"
          >
            Dismiss note
          </button>
        </aside>
      )}

      {/* Tags Filter Bar */}
      {allTags.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-xs">
          <span className="text-secondary shrink-0 font-medium">Filter:</span>
          <button
            type="button"
            onClick={() => setSelectedTag("ALL")}
            className={`px-3 py-1 rounded-lg transition-all shrink-0 ${
              selectedTag === "ALL"
                ? "bg-primary text-on-primary font-semibold"
                : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            All stones ({moments.length})
          </button>
          {allTags.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setSelectedTag(t)}
              className={`px-2.5 py-1 rounded-lg transition-all shrink-0 ${
                selectedTag === t
                  ? "bg-primary text-on-primary font-semibold"
                  : "bg-surface-container text-secondary hover:text-on-surface"
              }`}
            >
              #{t}
            </button>
          ))}
        </div>
      )}

      {/* Empty State */}
      {filteredMoments.length === 0 && (
        <div className="w-full rounded-3xl border border-dashed border-outline-variant/60 p-12 flex flex-col items-center justify-center text-center gap-4 min-h-[380px] bg-surface-container-lowest">
          <div className="w-14 h-14 rounded-2xl bg-surface-container-high flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-[28px]">landscape</span>
          </div>
          <div className="flex flex-col gap-1 max-w-md">
            <h2 className="font-serif text-xl font-medium text-primary">No stones found</h2>
            <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
              {searchQuery || selectedTag !== "ALL"
                ? "No kept moments match your current search or tag filter."
                : "You haven't preserved any moments yet. When a dialogue turn gives you clarity, save it as a cairn, or manually place one here."}
            </p>
          </div>
          <div className="flex items-center gap-3 mt-2">
            <button
              type="button"
              onClick={() => setIsAddModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-primary text-on-primary text-xs font-medium"
            >
              Place a new stone
            </button>
            <Link
              to="/talk"
              className="px-4 py-2 rounded-xl bg-surface-container border border-surface-container-highest text-secondary text-xs hover:text-primary transition-colors"
            >
              Start Talk Session
            </Link>
          </div>
        </div>
      )}

      {/* Cairns View (Zen Sand Pattern Meditation Ground) */}
      {viewMode === "cairns" && filteredMoments.length > 0 && (
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
            <ellipse cx="240" cy="220" rx="120" ry="50" strokeDasharray="3 4" />
            <ellipse cx="740" cy="190" rx="130" ry="55" strokeDasharray="4 5" />
            <ellipse cx="280" cy="450" rx="140" ry="60" strokeDasharray="3 5" />
            <ellipse cx="760" cy="430" rx="130" ry="55" strokeDasharray="4 5" />
          </svg>

          {/* Interactive Cairn Clusters */}
          <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-y-12 gap-x-12 items-start">
            {filteredMoments.map((m) => (
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
      {viewMode === "list" && filteredMoments.length > 0 && (
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

              <div className="flex items-center justify-between pt-2 border-t border-surface-container-high">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {(m.tags || []).map((t, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-surface-container text-[11px] text-secondary font-medium">
                      #{t}
                    </span>
                  ))}
                </div>
                <span className="text-xs text-secondary hover:text-primary transition-colors flex items-center gap-1">
                  <span>Inspect</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Place New Stone Cairn */}
      {isAddModalOpen && (
        <div
          onClick={() => setIsAddModalOpen(false)}
          className="fixed inset-0 z-50 bg-[#17231E]/60 backdrop-blur-md flex items-center justify-center p-6"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg bg-surface-container-lowest rounded-3xl p-6 sm:p-8 border border-surface-container-highest shadow-2xl flex flex-col gap-5"
          >
            <div className="flex items-center justify-between border-b border-surface-container-high pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-[20px]">landscape</span>
                </div>
                <div>
                  <h2 className="font-serif text-xl font-medium text-primary">Place a Cairn Stone</h2>
                  <p className="text-xs text-secondary">Consecrate a grounded truth into your personal archive</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="p-1.5 rounded-lg hover:bg-surface-container text-on-surface-variant"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleSaveNewMoment} className="flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-medium text-on-surface">Title or Milestone Label</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Useful planning versus delayed action"
                  className="bg-surface-container border border-surface-container-highest rounded-xl px-3 py-2 text-on-surface placeholder:text-outline text-xs focus:outline-none focus:border-primary"
                  maxLength={120}
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-medium text-on-surface">
                  Pivotal Realization or Quote <span className="text-secondary">*</span>
                </label>
                <textarea
                  value={newQuote}
                  onChange={(e) => setNewQuote(e.target.value)}
                  placeholder="e.g., Planning helps when the task is genuinely complicated. It becomes a problem when I keep planning after I already know enough to begin."
                  rows={3}
                  required
                  className="bg-surface-container border border-surface-container-highest rounded-xl p-3 text-on-surface placeholder:text-outline text-xs focus:outline-none focus:border-primary leading-relaxed"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-medium text-on-surface">Context / Reflection Note</label>
                <textarea
                  value={newContext}
                  onChange={(e) => setNewContext(e.target.value)}
                  placeholder="What was happening when you realized this? Why is this stone worth keeping?"
                  rows={2}
                  className="bg-surface-container border border-surface-container-highest rounded-xl p-3 text-on-surface placeholder:text-outline text-xs focus:outline-none focus:border-primary leading-relaxed"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="font-medium text-on-surface">Stack Weight (Stones)</label>
                  <select
                    value={newStones}
                    onChange={(e) => setNewStones(Number(e.target.value))}
                    className="bg-surface-container border border-surface-container-highest rounded-xl px-3 py-2 text-on-surface text-xs focus:outline-none focus:border-primary"
                  >
                    <option value={3}>3 Stones (Gentle Marker)</option>
                    <option value={4}>4 Stones (Grounded Anchor)</option>
                    <option value={5}>5 Stones (Pivotal Milestone)</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="font-medium text-on-surface">Tags (comma-separated)</label>
                  <input
                    type="text"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    placeholder="e.g. Planning, Boundaries"
                    className="bg-surface-container border border-surface-container-highest rounded-xl px-3 py-2 text-on-surface placeholder:text-outline text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-surface-container-high mt-1">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-surface-container-highest text-secondary hover:text-on-surface transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newQuote.trim()}
                  className="px-5 py-2 rounded-xl bg-primary text-on-primary font-medium disabled:opacity-50 hover:bg-primary/90 transition-all shadow-sm"
                >
                  Consecrate stone
                </button>
              </div>
            </form>
          </div>
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
                    {selectedMoment.date} • Placed Cairn ({selectedMoment.stoneCount || selectedMoment.stones || 3} stones)
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

            {selectedMoment.transition && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-secondary font-medium">Discourse Transition:</span>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-primary/10 text-primary">
                  {selectedMoment.transition}
                </span>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-surface-container-high">
              <div className="flex items-center gap-1.5 flex-wrap">
                {(selectedMoment.tags || []).map((t, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-surface-container text-[10px] text-secondary font-medium">
                    #{t}
                  </span>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDeleteMoment(selectedMoment.id)}
                  className="px-3 py-1.5 rounded-lg border border-error/30 text-error hover:bg-error/10 font-label-md text-xs transition-colors"
                  title="Remove this moment from archive"
                >
                  Dissolve cairn
                </button>
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
        </div>
      )}
    </div>
  );
}
