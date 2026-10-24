import React, { useState } from "react";

/**
 * ChatHistoryDrawer
 * 
 * Contemplative slide-over sheet allowing users to:
 * - Browse previous chats / archives with dates, message counts, and topic tags
 * - Search past reflections by title or content
 * - Switch seamlessly between past dialogues
 * - Start a brand new reflection session
 * - Rename or delete past reflections
 */
export default function ChatHistoryDrawer({
  isOpen,
  onClose,
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState("");

  if (!isOpen) return null;

  const filteredChats = chats.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const titleMatch = (c.title || "").toLowerCase().includes(q);
    const snippetMatch = (c.preview || "").toLowerCase().includes(q);
    const tagMatch = (c.tags || []).some((t) => t.toLowerCase().includes(q));
    const msgMatch = (c.messages || []).some((m) =>
      (typeof m.text === "string" ? m.text : m.rawText || "")
        .toLowerCase()
        .includes(q)
    );
    return titleMatch || snippetMatch || tagMatch || msgMatch;
  });

  const handleStartRename = (e, chat) => {
    e.stopPropagation();
    setEditingChatId(chat.id);
    setEditTitle(chat.title || "Untitled Reflection");
  };

  const handleSaveRename = (e, chatId) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameChat(chatId, editTitle.trim());
    }
    setEditingChatId(null);
  };

  const handleKeyDownRename = (e, chatId) => {
    if (e.key === "Enter") {
      handleSaveRename(e, chatId);
    } else if (e.key === "Escape") {
      setEditingChatId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Dimmed backdrop */}
      <div
        className="fixed inset-0 bg-black/30 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over panel */}
      <aside
        aria-label="Previous Dialogues & Inquiries"
        className="relative w-full max-w-[460px] bg-[#F7FAF5] border-l border-[#CDD2C8] flex flex-col shadow-2xl z-10 overflow-hidden animate-in slide-in-from-right duration-300"
      >
        {/* Drawer Header */}
        <div className="px-6 py-5 border-b border-[#CDD2C8] flex items-start justify-between bg-[#F7FAF5]/95 backdrop-blur-md sticky top-0 z-20">
          <div className="flex flex-col gap-1 pr-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px] text-primary">history_edu</span>
              <h2 className="font-headline-sm text-lg font-serif text-[#23261F] font-normal tracking-tight">
                Previous Dialogues
              </h2>
            </div>
            <p className="font-body-sm text-xs text-[#52594D] leading-snug">
              Encrypted locally in your browser RAM. Sovereign, unrecorded, and yours alone.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#52594D] hover:text-[#23261F] hover:bg-[#E3E8DE] transition-colors"
            title="Close dialogues drawer"
            type="button"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Action Header: New Dialogue Button & Search */}
        <div className="p-5 border-b border-[#CDD2C8]/70 flex flex-col gap-3 bg-[#EFF4EC]/60">
          <button
            type="button"
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-on-primary hover:bg-primary-container font-label-md text-xs font-semibold tracking-wide transition-all shadow-2xs active:scale-[0.98]"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            <span>Start New Dialogue</span>
          </button>

          {/* Search Bar */}
          <div className="relative w-full">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-[18px] text-[#767E70]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search previous dialogues or topics..."
              className="w-full pl-9 pr-8 py-2 rounded-xl bg-white/80 border border-[#CDD2C8] text-xs font-body-sm text-[#23261F] placeholder:text-[#767E70] focus:outline-none focus:border-primary focus:bg-white transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-2.5 text-[#767E70] hover:text-[#23261F]"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            )}
          </div>

          <div className="flex items-center justify-between text-[11px] font-label-sm text-[#767E70] px-0.5">
            <span>{filteredChats.length} {filteredChats.length === 1 ? "dialogue" : "dialogues"} stored</span>
            <span>Local Sovereign Storage</span>
          </div>
        </div>

        {/* Dialogues List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
          {filteredChats.length === 0 ? (
            <div className="py-12 px-4 text-center flex flex-col items-center gap-2">
              <span className="material-symbols-outlined text-[32px] text-[#A6AF9F]">search_off</span>
              <p className="font-body-md text-sm text-[#52594D]">No dialogues match your search.</p>
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="text-xs text-primary underline underline-offset-2 mt-1"
              >
                Clear search query
              </button>
            </div>
          ) : (
            filteredChats.map((chat) => {
              const isActive = chat.id === activeChatId;
              const isEditing = editingChatId === chat.id;
              const messageCount = (chat.messages || []).length;
              const userMessageCount = (chat.messages || []).filter((m) => m.role === "user").length;

              return (
                <div
                  key={chat.id}
                  onClick={() => {
                    if (!isEditing) {
                      onSelectChat(chat.id);
                      onClose();
                    }
                  }}
                  className={`group relative rounded-xl p-3.5 border transition-all cursor-pointer flex flex-col gap-2 ${
                    isActive
                      ? "bg-white border-primary shadow-xs ring-1 ring-primary/30"
                      : "bg-white/60 hover:bg-white border-[#CDD2C8]/80 hover:border-[#B4BCAD] shadow-2xs"
                  }`}
                >
                  {/* Top Row: Title, Date, Active Indicator & Menu */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {isActive && (
                        <span className="w-2 h-2 rounded-full bg-primary shrink-0 ring-2 ring-primary/20" title="Active session" />
                      )}
                      
                      {isEditing ? (
                        <div className="flex items-center gap-1.5 w-full" onClick={(e) => e.stopPropagation()}>
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => handleKeyDownRename(e, chat.id)}
                            autoFocus
                            className="flex-1 px-2 py-1 text-xs border border-primary rounded bg-white font-medium text-[#23261F] focus:outline-none"
                          />
                          <button
                            type="button"
                            onClick={(e) => handleSaveRename(e, chat.id)}
                            className="p-1 hover:text-primary text-secondary"
                            title="Save title"
                          >
                            <span className="material-symbols-outlined text-[16px]">check</span>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingChatId(null);
                            }}
                            className="p-1 hover:text-red-600 text-secondary"
                            title="Cancel"
                          >
                            <span className="material-symbols-outlined text-[16px]">close</span>
                          </button>
                        </div>
                      ) : (
                        <h3 className={`font-serif text-sm font-medium tracking-tight truncate ${
                          isActive ? "text-primary" : "text-[#23261F]"
                        }`}>
                          {chat.title || "Untitled Reflection"}
                        </h3>
                      )}
                    </div>

                    {!isEditing && (
                      <div className="flex items-center gap-1 shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
                        <span className="text-[10px] font-label-sm text-[#767E70] whitespace-nowrap">
                          {chat.date || chat.time || "Recently"}
                        </span>
                        
                        {/* Quick Rename & Delete actions */}
                        <div className="flex items-center gap-0.5 ml-1" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            onClick={(e) => handleStartRename(e, chat)}
                            className="p-1 rounded text-[#767E70] hover:text-[#23261F] hover:bg-[#EFF4EC]"
                            title="Rename dialogue"
                          >
                            <span className="material-symbols-outlined text-[14px]">edit</span>
                          </button>
                          
                          {chats.length > 1 && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (window.confirm(`Delete "${chat.title || "this reflection"}"? This action removes it from local memory.`)) {
                                  onDeleteChat(chat.id);
                                }
                              }}
                              className="p-1 rounded text-[#767E70] hover:text-red-700 hover:bg-red-50"
                              title="Delete dialogue"
                            >
                              <span className="material-symbols-outlined text-[14px]">delete</span>
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Dialogue Preview Snippet */}
                  {chat.preview && (
                    <p className="font-body-sm text-xs text-[#52594D] line-clamp-2 leading-relaxed">
                      "{chat.preview}"
                    </p>
                  )}

                  {/* Bottom Meta Row: Turn Badges & Tags */}
                  <div className="flex items-center justify-between pt-1 border-t border-[#CDD2C8]/40 text-[11px] font-label-sm text-[#767E70]">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center gap-1">
                        <span className="material-symbols-outlined text-[13px]">forum</span>
                        <span>{userMessageCount} {userMessageCount === 1 ? "inquiry" : "inquiries"}</span>
                      </span>
                      {isActive && (
                        <span className="px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium text-[10px]">
                          Current Session
                        </span>
                      )}
                    </div>

                    {chat.tags && chat.tags.length > 0 && (
                      <div className="flex items-center gap-1 overflow-hidden">
                        {chat.tags.slice(0, 2).map((tag, tIdx) => (
                          <span
                            key={tIdx}
                            className="px-1.5 py-0.5 rounded bg-[#EFF4EC] text-[#52594D] text-[10px] truncate"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-[#CDD2C8] bg-[#F7FAF5] flex items-center justify-between text-xs text-[#767E70]">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px] text-primary">shield_person</span>
            <span>Zero cloud logging · Local RAM</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg border border-[#CDD2C8] hover:bg-[#EFF4EC] text-[#23261F] text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </aside>
    </div>
  );
}
