import React, { useState, useRef, useEffect, useLayoutEffect } from "react";
import { Link } from "react-router-dom";
import InspectionDrawer from "../components/InspectionDrawer";
import PebblePet3D from "../components/PebblePet3D";
import ChatHistoryDrawer from "../components/ChatHistoryDrawer";
import {
  distillPII,
  computeCenteringTrace,
  parseHobbsPronouns,
  parseClausesAndConnectives,
  evolveSessionMemory,
  findRelevantMemoryForContext,
  analyzeEmotionalSemantics,
  synthesizeNaturalReflection,
} from "../services/nlpEngine";
import { HISTORICAL_CHATS, HISTORICAL_MEMORIES } from "../data/historicalChats";

export default function TalkPage({ onToggleCurtain }) {
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [selectedTurnData, setSelectedTurnData] = useState(null);
  const [draft, setDraft] = useState("");
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isMascotEnabled, setIsMascotEnabled] = useState(true);

  // Living Mascot Bot: Semantic & Environmental Reactivity
  const [companionEmotion, setCompanionEmotion] = useState("neutral");
  const [keystrokeCount, setKeystrokeCount] = useState(0);

  // Cross-Session sovereign memories
  const [savedMemories, setSavedMemories] = useState(() => {
    try {
      const stored = localStorage.getItem("sanctuary_memories");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed.some(m => m.id === "mem-achievement")) {
          return parsed;
        }
      }
    } catch (e) {}
    try {
      localStorage.setItem("sanctuary_memories", JSON.stringify(HISTORICAL_MEMORIES));
      localStorage.setItem("sanctuary_moments", JSON.stringify(HISTORICAL_MEMORIES));
    } catch (e) {}
    return HISTORICAL_MEMORIES;
  });

  const [pendingConsentMemory, setPendingConsentMemory] = useState(null);
  const [consecratedNotification, setConsecratedNotification] = useState(null);

  // Sovereign Local Dialogues Archive & Multi-Chat Management
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [chats, setChats] = useState(() => {
    try {
      const stored = localStorage.getItem("sanctuary_chats");
      if (stored) {
        const parsed = JSON.parse(stored);
        const achievementChat = parsed.find((c) => c.id === "chat-achievement");
        const firstAsst = achievementChat?.messages?.find((m) => m.role === "assistant");
        const isNaturalReflective = firstAsst?.paragraphs?.[0]?.includes("The finish line arrived");
        if (isNaturalReflective) {
          return parsed;
        }
      }
    } catch (e) {}
    try {
      localStorage.setItem("sanctuary_chats", JSON.stringify(HISTORICAL_CHATS));
    } catch (e) {}
    return HISTORICAL_CHATS;
  });

  const [activeChatId, setActiveChatId] = useState(() => {
    try {
      const stored = localStorage.getItem("sanctuary_active_chat_id");
      if (stored && (stored === "chat-achievement" || stored === "chat-pattern" || stored === "chat-resistance" || stored === "chat-boundaries" || stored.startsWith("chat-"))) {
        return stored;
      }
    } catch (e) {}
    return HISTORICAL_CHATS[0]?.id || "chat-achievement";
  });

  const currentChat =
    chats.find((c) => c.id === activeChatId) ||
    chats[0] ||
    HISTORICAL_CHATS[0] || {
      id: "chat-achievement",
      title: "Achievement, exhaustion and the meaning of success",
      messages: [],
    };

  const messages = currentChat.messages || [];

  // Atomic message updater that synchronously updates active chat & commits to localStorage
  const setMessages = (updater) => {
    setChats((prevChats) => {
      const targetId = activeChatId;
      const updated = prevChats.map((c) => {
        if (c.id === targetId) {
          const prevMsgs = c.messages || [];
          const nextMsgs = typeof updater === "function" ? updater(prevMsgs) : updater;

          let nextTitle = c.title;
          let nextPreview = c.preview;
          const firstUserMsg = nextMsgs.find((m) => m.role === "user");
          if (firstUserMsg && (!c.title || c.title === "New Reflection" || c.title === "Untitled Reflection")) {
            const raw = firstUserMsg.rawText || (typeof firstUserMsg.text === "string" ? firstUserMsg.text : "");
            if (raw) {
              const snippet = raw.slice(0, 42).replace(/[\n\r]+/g, " ").trim();
              nextTitle = snippet.length >= 42 ? snippet + "..." : snippet;
            }
          }
          if (firstUserMsg) {
            const raw = firstUserMsg.rawText || (typeof firstUserMsg.text === "string" ? firstUserMsg.text : "");
            nextPreview = raw.slice(0, 110);
          }

          return {
            ...c,
            title: nextTitle,
            preview: nextPreview,
            messages: nextMsgs,
            updatedAt: Date.now(),
          };
        }
        return c;
      });

      try {
        localStorage.setItem("sanctuary_chats", JSON.stringify(updated));
      } catch (e) {
        console.error("Failed to persist chats to localStorage:", e);
      }
      return updated;
    });
  };

  // Keep activeChatId synced with localStorage
  useEffect(() => {
    try {
      localStorage.setItem("sanctuary_active_chat_id", activeChatId);
    } catch (e) {}
  }, [activeChatId]);

  // Chat Actions: Create New Chat, Switch/Open Chat, Delete Chat, Rename Chat
  const handleCreateNewChat = () => {
    const newId = `chat-${Date.now()}`;
    const newChatObj = {
      id: newId,
      title: "New Reflection",
      date: "Just now",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      preview: "",
      tags: ["Presence", "Clearing"],
      messages: [],
    };
    setChats((prev) => {
      const updated = [newChatObj, ...prev];
      try {
        localStorage.setItem("sanctuary_chats", JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
    setActiveChatId(newId);
    try {
      localStorage.setItem("sanctuary_active_chat_id", newId);
    } catch (e) {}
    setDraft("");
    setLifecycleState("idle");
    setCompanionEmotion("neutral");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.focus();
    }
  };

  const handleSelectChat = (chatId) => {
    setActiveChatId(chatId);
    try {
      localStorage.setItem("sanctuary_active_chat_id", chatId);
    } catch (e) {}
    setDraft("");
    setLifecycleState("idle");
    setCompanionEmotion("neutral");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleDeleteChat = (chatIdToDelete) => {
    setChats((prev) => {
      const remaining = prev.filter((c) => c.id !== chatIdToDelete);
      let nextActive = activeChatId;
      let finalChats = remaining;
      if (remaining.length === 0) {
        const freshId = `chat-${Date.now()}`;
        const freshChat = {
          id: freshId,
          title: "New Reflection",
          date: "Just now",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          preview: "",
          tags: ["Presence"],
          messages: [],
        };
        finalChats = [freshChat];
        nextActive = freshId;
      } else if (activeChatId === chatIdToDelete) {
        nextActive = remaining[0].id;
      }
      try {
        localStorage.setItem("sanctuary_chats", JSON.stringify(finalChats));
        localStorage.setItem("sanctuary_active_chat_id", nextActive);
      } catch (e) {}
      setActiveChatId(nextActive);
      return finalChats;
    });
  };

  const handleRenameChat = (chatId, newTitle) => {
    setChats((prev) => {
      const updated = prev.map((c) => (c.id === chatId ? { ...c, title: newTitle } : c));
      try {
        localStorage.setItem("sanctuary_chats", JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  // Helper to render user message content with bracketed masked entities
  const renderUserMessageContent = (msg) => {
    if (React.isValidElement(msg.text)) {
      return msg.text;
    }
    const textStr = typeof msg.text === "string" ? msg.text : msg.rawText || "";
    const bracketRegex = /(\[[^\]]+\])/g;
    if (bracketRegex.test(textStr)) {
      const parts = textStr.split(bracketRegex);
      return parts.map((part, pIdx) => {
        if (part.startsWith("[") && part.endsWith("]")) {
          return (
            <span
              key={pIdx}
              className="inline-flex items-center gap-1 bg-[#DDE1DA] border border-[#CDD2C8] px-2 py-0.5 mx-0.5 rounded text-xs font-label-md text-[#23261F] align-baseline select-none"
            >
              <span className="material-symbols-outlined text-[12px] text-[#2E4B3F]">lock</span>
              <span>{part}</span>
            </span>
          );
        }
        return part;
      });
    }
    return textStr;
  };

  // Deterministic companion lifecycle state
  const [lifecycleState, setLifecycleState] = useState("idle");
  // "idle" | "attentive" | "thinking" | "speaking" | "awaiting_followup" | "unburden" | "saved" | "nap"

  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Auto-scroll to bottom of conversation
  const scrollToBottom = (behavior = "smooth") => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior, block: "nearest" });
    }
  };

  useEffect(() => {
    scrollToBottom("smooth");
  }, [messages.length, lifecycleState]);

  // Dynamic textarea expansion & contraction
  // Dynamic textarea expansion, keystroke tracking & live emotional semantic analysis
  const handleDraftChange = (e) => {
    const val = e.target.value;
    setDraft(val);
    setKeystrokeCount((c) => c + 1);

    const target = e.target;
    target.style.height = "auto";
    const nextH = Math.min(Math.max(target.scrollHeight, 28), 140);
    target.style.height = `${nextH}px`;

    // Live Semantic & Emotional cadence analysis while user types
    const detected = analyzeEmotionalSemantics(val);
    if (detected !== "neutral") {
      setCompanionEmotion(detected);
    }

    if (val.trim()) {
      if (lifecycleState === "idle" || lifecycleState === "nap") {
        setLifecycleState("attentive");
      }
    } else {
      if (lifecycleState === "attentive") {
        setLifecycleState("idle");
        setCompanionEmotion("neutral");
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleReflect(e);
    }
  };

  // Structured conversational lifecycle with Centering & Cross-Session Memory Gate
  const handleReflect = (e) => {
    e?.preventDefault();
    if (!draft.trim() || lifecycleState === "thinking") return;

    const userText = draft.trim();

    // 1. Classify emotional cadence of user input to trigger living mascot response
    const userEmotion = analyzeEmotionalSemantics(userText);
    if (userEmotion !== "neutral") {
      setCompanionEmotion(userEmotion);
    }

    // 2. Deterministic NLP Engine: Mask PII, parse clauses, and compute Centering Trace
    const pii = distillPII(userText);
    const clauseData = parseClausesAndConnectives(pii.maskedText);
    const centeringTrace = computeCenteringTrace(pii.maskedText, pii.entities);
    const hobbsData = parseHobbsPronouns(pii.maskedText, pii.entities);

    const newTurnData = {
      rawText: userText,
      maskedText: pii.maskedText,
      entity: pii.entities[0]?.masked || "[Personal Narrative]",
      entityType: pii.entities[0]?.kind === "PERSON" ? "Individual Anonymized" : "Local RAM Session",
      clauses: clauseData.clauses.map((c) => ({ id: c.id, text: c.text })),
      connectors: clauseData.relations.map((r) => ({
        text: r.cue,
        type: r.type,
        source: r.source,
        target: r.target,
      })),
      recurringTopics: centeringTrace
        .filter((c) => c.transition !== "NO_CB")
        .slice(0, 3)
        .map((c) => ({
          term: c.cp || c.cb || "presence",
          label: c.transition,
          detail: `Centering ${c.transition} (cost: ${c.cost})`,
        })),
      centeringTrace,
      hobbsData,
    };

    if (newTurnData.recurringTopics.length === 0) {
      newTurnData.recurringTopics = [
        { term: "contemplation", label: "Anchor", detail: "Centering forward center registered" },
      ];
    }

    // 3. Cross-Session Memory Gate: ONLY connect memory if context directly aligns AND adds value
    const relevantMemoryMatch = findRelevantMemoryForContext(userText, savedMemories);

    // 4. Append user message & enter THINKING state
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        text: userText,
        rawText: userText,
        turnData: newTurnData,
      },
    ]);

    setDraft("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setLifecycleState("thinking");

    // 5. Formulate assistant response & trigger resonant companion reaction
    setTimeout(() => {
      setLifecycleState("speaking");

      let referencedMemory = null;

      if (relevantMemoryMatch) {
        // Context overlap passed: genuinely add reflective value -> Companion epiphany
        setCompanionEmotion("epiphany");
        referencedMemory = relevantMemoryMatch.memory;
      } else if (userEmotion === "empathy") {
        setCompanionEmotion("empathy");
      } else if (userEmotion === "curious") {
        setCompanionEmotion("curious");
      } else {
        setCompanionEmotion("neutral");
      }

      // Synthesize contemplative natural reflective output (non-hardcoded)
      const reflectionText = synthesizeNaturalReflection(
        userText,
        pii,
        clauseData.clauses,
        centeringTrace,
        userEmotion,
        relevantMemoryMatch
      );
      const responseParagraphs = [reflectionText];

      // Parse assistant turn dynamic NLP features
      const asstPii = distillPII(reflectionText);
      const asstClausesData = parseClausesAndConnectives(asstPii.maskedText);
      const asstCentering = computeCenteringTrace(asstPii.maskedText, asstPii.entities);
      const asstRecurringTopics = asstCentering
        .filter((c) => c.cb)
        .map((c) => ({
          term: c.cb,
          label: c.transition,
          detail: `Centering ${c.transition} (cost: ${c.cost})`,
          status: "Linked",
        }));

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          paragraphs: responseParagraphs,
          referencedMemory,
          turnData: {
            entity: asstPii.entities[0]?.masked || "[Sanctuary Reflection]",
            entityType: "Local RAM Session",
            maskedText: asstPii.maskedText,
            clauses: asstClausesData.clauses,
            connectors: asstClausesData.relations.length > 0 ? asstClausesData.relations : [
              {
                cue: "while",
                text: "while",
                type: "Syntactic Balance",
              },
            ],
            recurringTopics: asstRecurringTopics.length > 0 ? asstRecurringTopics : [
              {
                term: relevantMemoryMatch ? relevantMemoryMatch.memory.centerEntity : "territory",
                label: "Attunement",
                detail: relevantMemoryMatch ? "Cross-session memory verified" : "Immediate presence",
                status: "Linked",
              },
            ],
          },
        },
      ]);

      // 6. Transition to AWAITING_FOLLOWUP -> IDLE
      setTimeout(() => {
        setLifecycleState("awaiting_followup");
        setTimeout(() => {
          setLifecycleState("idle");
          setCompanionEmotion("neutral");
        }, 3200);
      }, 1600);
    }, 900);
  };

  // Mindfulness Action: Unburden & evaluate Centering moment
  const handleSetDownWeight = () => {
    setLifecycleState("unburden");
    setCompanionEmotion("grounding");
    const newAssistantMsg = {
      role: "assistant",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      paragraphs: [
        "The unspoken weight has been acknowledged and set down into this quiet vessel.",
        "Notice the breath opening across your chest and shoulders. Nothing is required to be held alone in this room.",
      ],
    };
    setMessages((prev) => [...prev, newAssistantMsg]);

    setTimeout(() => {
      setLifecycleState("idle");
      setCompanionEmotion("neutral");
      // Trigger Centering memory evolver and check if a moment should be proposed
      const candidate = evolveSessionMemory([...messages, newAssistantMsg]);
      if (candidate) {
        setPendingConsentMemory(candidate);
      }
    }, 1800);
  };

  // Mindfulness Action: Conclude conversation & trigger Memory Evolver
  const handleConcludeSession = () => {
    setLifecycleState("attentive");
    const newAssistantMsg = {
      role: "assistant",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      paragraphs: [
        "Concluding this contemplative session. Evaluating discourse trajectory and centering shifts...",
      ],
    };
    setMessages((prev) => [...prev, newAssistantMsg]);

    setTimeout(() => {
      const candidate = evolveSessionMemory([...messages, newAssistantMsg]);
      if (candidate) {
        setPendingConsentMemory(candidate);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            paragraphs: [
              "This session was gentle and complete. No unresolved shifts were left ungrounded. You may close this tab in peace.",
            ],
          },
        ]);
      }
      setLifecycleState("idle");
    }, 1200);
  };

  // Sovereign Consent Handlers: User chooses whether to consecrate to Cairns or keep ephemeral
  const handleConsentSaveMemory = () => {
    if (!pendingConsentMemory) return;
    const newMemory = { ...pendingConsentMemory, id: `mem-${Date.now()}` };
    const updated = [newMemory, ...savedMemories];
    setSavedMemories(updated);
    try {
      localStorage.setItem("sanctuary_memories", JSON.stringify(updated));
      const rawMoments = localStorage.getItem("sanctuary_moments");
      const list = rawMoments ? JSON.parse(rawMoments) : [];
      list.unshift({
        id: newMemory.id,
        title: newMemory.title,
        date: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        quote: newMemory.quote,
        context: newMemory.context,
        stones: newMemory.stoneCount || 3,
        transition: newMemory.transition || "CONTINUE",
        tags: newMemory.tags || ["Centering Insight", "Cairn Anchor"],
      });
      localStorage.setItem("sanctuary_moments", JSON.stringify(list));
    } catch (e) {}

    setPendingConsentMemory(null);
    setLifecycleState("saved");
    setCompanionEmotion("celebrating");

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        paragraphs: [
          `Preserved with your sovereign consent: "${newMemory.title}".`,
          `This anchor has been consecrated into your Cairns with a stack of ${newMemory.stoneCount} stones. In subsequent conversations, Sanctuary will only draw upon this memory if your context directly aligns and adds genuine value; otherwise it will remain resting.`,
        ],
      },
    ]);

    setTimeout(() => {
      setLifecycleState("idle");
      setCompanionEmotion("neutral");
    }, 2800);
  };

  const handleDeclineMemory = () => {
    setPendingConsentMemory(null);
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        paragraphs: [
          "Understood. This reflection will remain ephemeral and dissolve with this session, leaving no trace in your Cairns.",
        ],
      },
    ]);
  };

  return (
    <div className="w-full flex-1 flex flex-col bg-background font-body-md antialiased text-on-surface overflow-hidden max-h-[calc(100vh-5rem)] h-[calc(100vh-5rem)]">
      {/* Slide-over Inspection Sheet */}
      <InspectionDrawer
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
        turnData={selectedTurnData}
        allTurns={messages}
      />

      {/* Slide-over Chat History & Previous Dialogues Drawer */}
      <ChatHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleCreateNewChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
      />

      {/* Region 0: Quiet Metadata Bar (Pinned Header, shrink-0) */}
      <div className="w-full border-b border-[#CDD2C8]/70 bg-surface-container-low/50 backdrop-blur-sm shrink-0 z-10 transition-colors">
        <div className="w-full px-4 sm:px-6 lg:px-8 h-12 flex items-center justify-between text-xs text-[#454B40]">
          {/* Left: Chat Switcher & Quick New Chat */}
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={() => setIsHistoryOpen(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-label-sm text-xs transition-all border border-[#CDD2C8] shadow-2xs group"
              title="Browse previous chats and archives"
            >
              <span className="material-symbols-outlined text-[16px] text-[#2E4B3F] group-hover:scale-105 transition-transform">
                history_edu
              </span>
              <span className="max-w-[130px] sm:max-w-[210px] truncate font-medium text-[#23261F]">
                {currentChat.title || "Reflections"}
              </span>
              <span className="material-symbols-outlined text-[16px] text-[#454B40]">
                arrow_drop_down
              </span>
            </button>

            <button
              type="button"
              onClick={handleCreateNewChat}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#2E4B3F]/10 hover:bg-[#2E4B3F]/20 text-[#2E4B3F] font-label-sm text-xs font-semibold transition-all active:scale-[0.98] border border-[#2E4B3F]/20 shadow-2xs"
              title="Start a new reflection dialogue"
            >
              <span className="material-symbols-outlined text-[15px]">add</span>
              <span className="hidden sm:inline">New Chat</span>
            </button>

            <span className="hidden md:inline text-[#CDD2C8]">|</span>

            <div className="hidden md:flex items-center gap-2 text-[#454B40] font-label-sm text-xs">
              <span className="material-symbols-outlined text-[17px] text-[#2E4B3F]">radio_button_checked</span>
              <span className="uppercase tracking-wider">Volatile Session • Ephemeral RAM only</span>
            </div>
          </div>

          {/* Right: Controls & Status */}
          <div className="flex items-center gap-5 font-label-sm text-[#454B40]">
            <span className="text-xs text-[#454B40]/80">
              Turn {messages.filter((m) => m.role === "user").length} of {messages.length} recorded
            </span>

            {/* 3D Pet Toggle */}
            <button
              type="button"
              onClick={() => setIsMascotEnabled(!isMascotEnabled)}
              className="flex items-center gap-1.5 hover:text-[#2E4B3F] transition-colors py-0.5 px-2 rounded hover:bg-[#DDE1DA]"
              title="Toggle 3D Pet Companion"
            >
              <span className="material-symbols-outlined text-[14px]">
                {isMascotEnabled ? "pets" : "visibility_off"}
              </span>
              <span className="hidden sm:inline">{isMascotEnabled ? "Hide Mascot" : "Show Mascot"}</span>
            </button>

            <div className="hidden sm:flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#2E4B3F]"></span>
              <span className="text-xs text-[#23261F]">Sanctuary Daylight Engine v4.2</span>
            </div>
          </div>
        </div>
      </div>

      {/* Region 1: Dedicated Scrollable Conversation History */}
      <div
        ref={messagesContainerRef}
        className={`flex-1 overflow-y-auto overscroll-contain px-6 lg:px-12 xl:px-16 pt-6 pb-48 focus:outline-none transition-all duration-300 ${
          isInspectorOpen ? "lg:pr-[470px]" : ""
        }`}
      >
        <div className="w-full max-w-[760px] mx-auto flex flex-col gap-8 pb-12">
          {/* Contemplative Presence: Dynamic Title based on current chat */}
          <div className="flex items-center gap-3 text-[#454B40]/70 select-none py-1">
            <span className="h-[1px] flex-1 bg-[#CDD2C8]"></span>
            <span className="font-label-sm text-xs">
              {currentChat.title} • {currentChat.time || "08:42"}
            </span>
            <span className="h-[1px] flex-1 bg-[#CDD2C8]"></span>
          </div>

          {/* Empty Clearing state for New Chat */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center select-none max-w-[560px] mx-auto animate-in fade-in duration-300">
              <div className="w-12 h-12 rounded-2xl bg-[#DDE1DA] border border-[#CDD2C8] flex items-center justify-center text-[#2E4B3F] mb-3 shadow-xs">
                <span className="material-symbols-outlined text-[24px]">air</span>
              </div>
              <h3 className="font-serif text-xl sm:text-2xl text-[#23261F] font-normal">
                A quiet clearing.
              </h3>
              <p className="font-body-md text-sm text-[#454B40] mt-2 leading-relaxed">
                There are no expectations, metrics, or unread tallies here. Speak plainly into the vessel below whenever you are ready.
              </p>
            </div>
          )}

          {/* Conversation Turns Stream */}
          {messages.map((msg, idx) => {
            if (msg.role === "user") {
              return (
                <div key={idx} className="flex flex-col gap-2.5 items-end group max-w-[640px] self-end w-full">
                  <div className="flex items-center gap-2 text-xs text-[#454B40] px-1 font-label-sm">
                    <span className="material-symbols-outlined text-[14px]">person</span>
                    <span>You</span>
                  </div>
                  <div className="w-full bg-[#DCE2D6] p-5 sm:p-6 rounded-2xl rounded-tr-sm border border-[#CDD2C8] leading-relaxed shadow-2xs">
                    <p className="font-body-lg text-base text-[#23261F] leading-relaxed">
                      {renderUserMessageContent(msg)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-[#454B40]/70 font-label-sm text-[11px] pr-1">
                    <span>Masked locally prior to synthesis</span>
                    <span>·</span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedTurnData(msg.turnData || { rawText: msg.rawText || msg.text });
                        setIsInspectorOpen(true);
                      }}
                      className="hover:text-[#23261F] underline underline-offset-2 transition-colors flex items-center gap-0.5"
                    >
                      <span>Inspect input</span>
                    </button>
                  </div>
                </div>
              );
            }

            // Sanctuary Reflection Turn
            return (
              <div
                key={idx}
                className="flex flex-col gap-3 group max-w-[680px] w-full self-start"
              >
                <div className="flex items-center gap-2 text-xs text-[#2E4B3F] px-1 font-label-sm font-semibold">
                  <span className="material-symbols-outlined text-[16px] text-[#2E4B3F]">spa</span>
                  <span>Sanctuary</span>
                </div>

                <div className="w-full bg-[#F6F7F3] p-6 sm:p-7 rounded-2xl rounded-tl-sm border border-[#CDD2C8] flex flex-col gap-5 shadow-2xs">
                  {/* Prior Memory Attribution Tag (Rendered only when strict context gate passed) */}
                  {msg.referencedMemory && (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#DDE1DA] border border-[#2E4B3F]/20 text-[#2E4B3F] font-label-sm text-xs self-start shadow-2xs">
                      <span className="material-symbols-outlined text-[15px]">history_edu</span>
                      <span>Cairns Memory Cross-Reference: <strong>{msg.referencedMemory.title}</strong></span>
                    </div>
                  )}

                  <div className="flex flex-col gap-3">
                    {msg.paragraphs.map((p, pIdx) => (
                      <p
                        key={pIdx}
                        className="font-headline-sm text-base sm:text-lg font-serif text-[#23261F] font-normal leading-relaxed"
                      >
                        {p}
                      </p>
                    ))}
                  </div>

                  {/* Turn Inspection Action bar matching user design */}
                  <div className="pt-4 border-t border-[#CDD2C8]/70 flex flex-wrap items-center justify-between gap-3">
                    <button
                      type="button"
                      aria-controls="inspectionSheet"
                      aria-expanded={isInspectorOpen}
                      onClick={() => {
                        const userTurn = messages[idx - 1] || messages.find((m) => m.role === "user") || null;
                        const combinedTurnData = {
                          rawText: userTurn?.rawText || userTurn?.text || msg.turnData?.maskedText || "",
                          maskedText: userTurn?.turnData?.maskedText || userTurn?.text || msg.turnData?.maskedText || "",
                          entity: userTurn?.turnData?.entity || msg.turnData?.entity || "[The Office]",
                          entityType: userTurn?.turnData?.entityType || msg.turnData?.entityType || "Organization / Location identifier",
                          entitiesMasked: userTurn?.turnData?.entitiesMasked || 1,
                          clauses: userTurn?.turnData?.clauses || msg.turnData?.clauses,
                          connectors: userTurn?.turnData?.connectors || msg.turnData?.connectors,
                          recurringTopics: userTurn?.turnData?.recurringTopics || msg.turnData?.recurringTopics,
                          assistantParagraphs: msg.paragraphs,
                        };
                        setSelectedTurnData(combinedTurnData);
                        setIsInspectorOpen((prev) => !prev);
                      }}
                      className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#2E4B3F] text-[#E9ECE7] hover:bg-[#233A31] transition-all font-label-sm text-xs tracking-normal shadow-none cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[16px]">visibility</span>
                      <span>How this was read</span>
                      <span className="w-1.5 h-1.5 rounded-full bg-[#C4CF5A]"></span>
                    </button>

                    <div className="flex items-center gap-1.5 text-[#454B40]">
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(msg.paragraphs.join("\n\n"));
                        }}
                        className="p-1.5 rounded-md hover:bg-[#DDE1DA] transition-colors"
                        title="Copy raw text"
                      >
                        <span className="material-symbols-outlined text-[17px]">content_copy</span>
                      </button>
                      <button
                        type="button"
                        onClick={handleSetDownWeight}
                        className="p-1.5 rounded-md hover:bg-[#DDE1DA] transition-colors"
                        title="Set down unspoken weight"
                      >
                        <span className="material-symbols-outlined text-[17px]">eco</span>
                      </button>
                      <button
                        type="button"
                        onClick={handleConcludeSession}
                        className="p-1.5 rounded-md hover:bg-[#DDE1DA] transition-colors"
                        title="Conclude & Evolve Memory"
                      >
                        <span className="material-symbols-outlined text-[17px]">psychology</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Minimalist Writing Bar (Active inspection indicator) */}
          {isInspectorOpen && (
            <div className="mt-4 pt-4 border-t border-[#CDD2C8] flex items-center justify-between text-[#454B40] text-xs font-label-sm max-w-[680px]">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#C4CF5A]"></span>
                <span>Inspection overlay active. Press Esc or close sheet to write.</span>
              </div>
              <span className="text-xs text-[#454B40]/70">Zero persistent cloud logs</span>
            </div>
          )}

          {/* Sovereign Memory Proposal Consent Card (Centering Theory & Memory Evolver) */}
          {pendingConsentMemory && (
            <div className="w-full max-w-[760px] mx-auto my-3 p-5 sm:p-6 rounded-2xl bg-surface-container-high/95 border-2 border-primary/40 shadow-lg backdrop-blur-md flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-3">
              <div className="flex items-center justify-between border-b border-surface-container-highest pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse"></span>
                  <span className="font-label-sm text-xs uppercase tracking-widest text-primary font-semibold">
                    Sovereign Memory Proposal · Centering Algorithm
                  </span>
                </div>
                <span className="text-[11px] font-mono text-secondary px-2.5 py-1 rounded bg-surface-container border border-outline-variant/40">
                  Transition: {pendingConsentMemory.transition}
                </span>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-headline-sm text-xl font-serif text-primary font-medium">
                    "{pendingConsentMemory.title}"
                  </h3>
                  <span className="text-xs font-mono text-secondary">
                    Stack: {pendingConsentMemory.stoneCount} stones
                  </span>
                </div>
                <p className="font-body-md text-sm sm:text-base text-on-surface italic font-serif leading-relaxed bg-surface-container/70 p-3.5 rounded-xl border border-surface-container-highest">
                  "{pendingConsentMemory.quote}"
                </p>
                <div className="flex flex-wrap items-center gap-2 text-xs text-secondary font-label-sm pt-1">
                  <span>Anchor Center: <strong className="text-on-surface">{pendingConsentMemory.centerEntity}</strong></span>
                  <span>•</span>
                  <span>Algorithm: <strong>Centering Theory Cb/Cp Tracking</strong></span>
                  <span>•</span>
                  <span>{pendingConsentMemory.context}</span>
                </div>
              </div>

              <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
                Do you consent to preserving this reflection in your Cairns? In future conversations, Sanctuary will only draw upon this memory if your context directly matches and adds genuine value.
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={handleConsentSaveMemory}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-on-primary hover:bg-primary-container font-label-md text-xs font-semibold tracking-wide transition-all shadow-sm active:scale-[0.98]"
                >
                  <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  <span>Consent & Save to Cairns</span>
                </button>

                <button
                  type="button"
                  onClick={handleDeclineMemory}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-outline-variant hover:bg-surface-container text-secondary hover:text-on-surface font-label-md text-xs font-medium transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">close</span>
                  <span>Keep Ephemeral (Do not save)</span>
                </button>
              </div>
            </div>
          )}

          {/* Anchor to scroll cleanly into view above floating composer */}
          <div ref={messagesEndRef} className="h-64 shrink-0" />
        </div>
      </div>

      {/* Floating Island: Companion Mascot Jumping Freely On Top + Sleek Floating Chatbox (Zero White Boundary) */}
      <div
        className={`pointer-events-none fixed bottom-5 inset-x-0 z-30 flex flex-col items-center px-4 transition-all duration-300 ${
          isInspectorOpen ? "lg:pr-[440px]" : ""
        }`}
      >
        <div className="w-full max-w-[560px] flex flex-col items-center">
          
          {/* Unboxed 3D Mascot Freely Roaming & Jumping Directly On Top of the Floating Chatbox */}
          {isMascotEnabled && (
            <div className="w-full h-22 sm:h-26 relative select-none pointer-events-auto overflow-visible -mb-2 z-10">
              <PebblePet3D
                lifecycleState={lifecycleState}
                isTyping={Boolean(draft.trim())}
                emotionalState={companionEmotion}
                keystrokeTrigger={keystrokeCount}
                className="w-full h-full"
              />
            </div>
          )}

          {/* Floating Chatbox Composer (Reduced size, no white boundary, sleek river-stone card) */}
          <form
            onSubmit={handleReflect}
            className="w-full pointer-events-auto bg-[#F7FAF5]/95 backdrop-blur-xl rounded-2xl p-2.5 sm:p-3 border border-outline-variant/60 shadow-[0_16px_40px_-10px_rgba(23,52,41,0.16),0_2px_8px_rgba(0,0,0,0.04)] flex flex-col gap-1 transition-all focus-within:border-primary/50 focus-within:shadow-[0_18px_44px_-8px_rgba(23,52,41,0.22)]"
          >
            <textarea
              ref={textareaRef}
              value={draft}
              onChange={handleDraftChange}
              onKeyDown={handleKeyDown}
              placeholder="Speak plainly into this quiet vessel..."
              rows={1}
              style={{ minHeight: "28px", maxHeight: "110px" }}
              className="w-full bg-transparent resize-none border-0 p-1 text-on-surface placeholder:text-outline font-body-md text-sm sm:text-base focus:ring-0 focus:outline-none leading-relaxed transition-all"
            />

            <div className="flex items-center justify-between pt-1 border-t border-surface-container-highest/60 px-0.5 text-xs">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsVoiceActive(!isVoiceActive)}
                  className={`p-1.5 rounded-lg transition-colors flex items-center justify-center ${
                    isVoiceActive
                      ? "bg-primary text-on-primary"
                      : "text-secondary hover:bg-surface-container"
                  }`}
                  title={isVoiceActive ? "Listening (Local transcription)" : "Local voice capture"}
                >
                  <span className="material-symbols-outlined text-[16px]">
                    {isVoiceActive ? "mic" : "mic_none"}
                  </span>
                </button>
                <span className="text-[11px] font-label-sm text-secondary hidden sm:inline">
                  {draft.length > 0 ? `${draft.length} chars` : "Return to reflect"}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {draft && (
                  <button
                    type="button"
                    onClick={() => {
                      setDraft("");
                      if (textareaRef.current) textareaRef.current.style.height = "auto";
                      if (lifecycleState === "attentive") setLifecycleState("idle");
                    }}
                    className="text-xs text-secondary hover:text-primary px-2 py-0.5 rounded transition-colors"
                  >
                    Clear
                  </button>
                )}
                <button
                  type="submit"
                  disabled={!draft.trim() || lifecycleState === "thinking"}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium font-body-md transition-all ${
                    draft.trim() && lifecycleState !== "thinking"
                      ? "bg-primary text-on-primary hover:bg-primary-container shadow-2xs active:scale-[0.98]"
                      : "bg-surface-container text-outline/60 cursor-not-allowed"
                  }`}
                >
                  <span>{lifecycleState === "thinking" ? "Thinking..." : "Reflect"}</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
