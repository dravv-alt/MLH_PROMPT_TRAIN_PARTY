import React, { useState } from "react";
import { OFFICIAL_BRAND_LOGO } from "./PebbleMascot";

/**
 * Sanctuary Official Brand Logo Mark
 * Renders the minimalist river-stone brand mark: organic smoothed pebbles
 * in deep spruce-green (#173429 / #2E4B3F) with the diagonal quartz mineral vein
 * and lichen botanical sprout.
 */
export default function BrandLogo({ size = 36, className = "" }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div
      className={`relative rounded-xl overflow-hidden flex items-center justify-center shrink-0 shadow-xs border border-primary/20 bg-gradient-to-b from-[#2E4B3F] to-[#173429] ${className}`}
      style={{ width: `${size}px`, height: `${size}px` }}
      title="Sanctuary Contemplative Journal Brand Logo"
    >
      {!imgError ? (
        <img
          src={OFFICIAL_BRAND_LOGO}
          alt="Sanctuary Brand Logo"
          className="w-full h-full object-cover p-1"
          onError={() => setImgError(true)}
        />
      ) : (
        <svg
          viewBox="0 0 40 40"
          className="w-full h-full p-1"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Base River Stone */}
          <ellipse
            cx="20"
            cy="26"
            rx="14"
            ry="9"
            fill="#C8D4C5"
            stroke="#173429"
            strokeWidth="1.2"
          />
          <path
            d="M 12 25 Q 20 28 28 25"
            stroke="#9EAEA0"
            strokeWidth="0.8"
            strokeLinecap="round"
          />

          {/* Top River Stone */}
          <path
            d="M 12 20 C 11 12, 17 8, 20 8 C 23 8, 29 12, 28 20 C 27 24, 13 24, 12 20 Z"
            fill="#E5ECE2"
            stroke="#173429"
            strokeWidth="1.2"
          />

          {/* Diagonal Quartz Mineral Vein */}
          <path
            d="M 15 12 Q 21 16 26 21"
            stroke="#FFFFFF"
            strokeWidth="1.4"
            strokeLinecap="round"
          />

          {/* Lichen Sprout Crown */}
          <path
            d="M 20 8 Q 20 4 23 3"
            stroke="#8CA84E"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
          <circle cx="23" cy="3" r="1.6" fill="#C4CF5A" />
        </svg>
      )}
    </div>
  );
}
