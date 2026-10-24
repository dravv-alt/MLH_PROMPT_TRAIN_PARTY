import React from "react";
import { Link, useLocation } from "react-router-dom";
import BrandLogo from "./BrandLogo";

export default function TopNavigation({ onToggleCurtain }) {
  const location = useLocation();

  const navLinks = [
    { label: "Monograph", path: "/" },
    { label: "Talk", path: "/talk" },
    { label: "How This Was Read", path: "/how-this-was-read" },
    { label: "Moments", path: "/moments" },
    { label: "Remembered", path: "/remembered" },
    { label: "Calm", path: "/calm" },
    { label: "Privacy", path: "/privacy" },
  ];

  return (
    <header className="w-full border-b border-surface-container-highest/80 bg-surface-bright/95 backdrop-blur-md sticky top-0 z-40 transition-all select-none">
      <div className="w-full px-6 lg:px-12 xl:px-16 h-20 flex items-center justify-between gap-6">
        {/* Brand & Main Navigation */}
        <div className="flex items-center gap-8 lg:gap-12">
          <Link to="/" className="flex items-center gap-3.5 group">
            {/* Official River-Stone Brand Logo */}
            <BrandLogo size={36} className="group-hover:scale-105 transition-transform" />
            <div className="flex flex-col">
              <span className="font-headline-sm text-xl tracking-tight text-primary font-medium leading-none font-serif">
                Sanctuary
              </span>
              <span className="font-label-sm text-[11px] text-secondary mt-1 font-normal tracking-wide">
                Contemplative Journal
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-6 lg:gap-8 font-body-md text-sm text-on-surface-variant font-normal">
            {navLinks.map((link) => {
              const isActive =
                link.path === "/"
                  ? location.pathname === "/"
                  : location.pathname.startsWith(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`py-1 transition-colors ${
                    isActive
                      ? "text-primary font-semibold border-b-2 border-primary"
                      : "hover:text-primary"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right Status & Quick Tools */}
        <div className="flex items-center gap-3 sm:gap-4 lg:gap-5 shrink-0">
          <a
            href="tel:988"
            className="hidden xl:flex items-center gap-1.5 text-xs text-secondary hover:text-primary transition-colors py-1"
            title="Always available crisis hotline"
          >
            <span className="material-symbols-outlined text-[16px] text-surface-tint">
              emergency
            </span>
            <span>Crisis Lifeline (988)</span>
          </a>

          <div className="hidden xl:block h-4 w-px bg-outline-variant/60"></div>

          {/* Curtain Trigger */}
          <button
            type="button"
            onClick={onToggleCurtain}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors text-xs font-medium"
            title="Instant stone curtain (Esc)"
          >
            <span className="material-symbols-outlined text-[16px]">visibility_off</span>
            <span className="hidden sm:inline">Curtain</span>
            <kbd className="px-1 py-0.5 rounded bg-surface-container-lowest text-on-surface font-mono text-[10px]">
              Esc
            </kbd>
          </button>

          {/* Quiet Status Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container text-[11px] font-label-sm text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-lichen"></span>
            <span>0 telemetry</span>
          </div>

          <Link
            to="/talk"
            className="inline-flex items-center gap-2 bg-primary text-on-primary font-body-md text-sm font-medium px-4 py-2 rounded-lg hover:bg-primary-container active:scale-[0.98] transition-all"
          >
            <span>Begin writing</span>
            <span className="material-symbols-outlined text-base">arrow_forward</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
