import React, { useEffect } from "react";

export default function StoneCurtain({ isOpen, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 bg-[#17231E]/95 backdrop-blur-2xl flex flex-col items-center justify-center p-6 text-center select-none cursor-pointer transition-opacity duration-300"
      aria-label="Stone Curtain Privacy Shield"
    >
      <div className="max-w-md flex flex-col items-center gap-6" onClick={(e) => e.stopPropagation()}>
        {/* Contemplative Concealment Glyph */}
        <div className="w-20 h-20 rounded-full bg-[#1e2e27] border border-[#3E5247] flex items-center justify-center text-[#C4CF5A] shadow-inner">
          <span className="material-symbols-outlined text-[36px]">shield</span>
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-label-sm text-xs uppercase tracking-widest text-[#C4CF5A]">
            Stone Curtain Active
          </span>
          <h2 className="font-headline-md text-2xl lg:text-3xl font-serif text-[#F7FAF5]">
            Screen concealed.
          </h2>
          <p className="font-body-md text-sm text-[#A7B6AB] max-w-sm leading-relaxed">
            Your reflections are protected from view. Click anywhere or press{" "}
            <kbd className="px-1.5 py-0.5 rounded bg-[#24352D] border border-[#3E5247] text-[#F7FAF5] font-mono text-xs">
              Esc
            </kbd>{" "}
            to lift the curtain.
          </p>
        </div>

        <button
          onClick={onClose}
          className="mt-2 px-6 py-2.5 rounded-full bg-[#2E4B3F] hover:bg-[#395B4D] text-[#F7FAF5] font-label-md text-xs uppercase tracking-wider transition-colors"
        >
          Resume Reflection
        </button>
      </div>
    </div>
  );
}
