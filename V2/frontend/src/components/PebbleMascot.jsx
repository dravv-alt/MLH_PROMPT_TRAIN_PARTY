import React, { useState } from "react";

// Official Google Stitch image assets for Sanctuary Pebble Mascot
export const MASCOT_POSES = {
  // Key feature poses
  writing: "/assets/mascot/mascot_1.png",      // Writing in green journal with pencil
  breathing: "/assets/mascot/mascot_2.png",    // Meditating with closed eyes and breath streams
  watering: "/assets/mascot/mascot_3.png",     // Watering a tiny green sprout
  candle: "/assets/mascot/mascot_4.png",       // Sitting quietly beside glowing stone candle
  welcome: "/assets/mascot/mascot_5.png",      // Open arms welcome
  listening: "/assets/mascot/mascot_6.png",    // Attentive head tilt, gentle smile
  epiphany: "/assets/mascot/mascot_7.png",     // Thinking with celestial spark
  wave: "/assets/mascot/mascot_8.png",         // Cheerful wave
  insight: "/assets/mascot/mascot_9.png",      // Pointing up with glowing sprout
  gratitude: "/assets/mascot/mascot_10.png",   // Hands on heart, blissful gratitude
  wondering: "/assets/mascot/mascot_11.png",   // Gentle question mark
  attentive: "/assets/mascot/mascot_12.png",   // Hand cupped to ear listening
  joyful: "/assets/mascot/mascot_13.png",      // Joyful greeting
  peaceful: "/assets/mascot/mascot_14.png",    // Calm serene wave
  idea: "/assets/mascot/mascot_15.png",        // Lightbulb moment
  empty: "/assets/mascot/mascot_16.png",       // Gentle shrugging for no results
};

// Aliases for intuitive semantic usage
export const POSE_ALIASES = {
  resting: "listening",
  calm: "breathing",
  journal: "writing",
  talk: "listening",
  moments: "watering",
  remembered: "epiphany",
  unresolved: "wondering",
  curtain: "candle",
  hero: "welcome",
};

// Google Stitch cloud-hosted fallbacks
export const OFFICIAL_STITCH_CLOUD_IMG =
  "https://lh3.googleusercontent.com/aida/AEtjO1Wg222OZpNx3_SAHVewrDRW6sPgjXMo4NZgmb0M-85c33lOys1hG-vxgEAFRM0clvzQesUKlMd6qgV7tMOFuYyOHgQ-sfqhH1-7cYn8rgwy4jBwI07W0CIJJ7SEAYKVq-vSgsNd29fvkNuYIyCel90bIqD0LVFLNndn-kN4Y5vSr887J-s16XYYeIyYyixoCRL80X9k_S79C8enqiW6kavwAbCpQQ_wxee9On-QBrMREFR5TbVHL5jV_Yg";

export const OFFICIAL_BRAND_LOGO =
  "https://lh3.googleusercontent.com/aida/AEtjO1WLwibH1a6D15VoiRi40MEKlos8GegiuItKrt-nnXqcEc_aCHsbgoj3DVuaHkQGecWCgpAhoYH5W6-l8uBI6uePZSGNY6mpj3CIVYAXgeYNggzpPiMSE8cOACJFLztsVLQCUKRwDSPociCu_GNBRdax3K64Osa90uxjPgFweYcdtgg5dBSirFSlzt6GQ0mROb9T4sq70C_JA3AZhI9qZgqrPPcDfqzNWHoeZ8tEHfurmSNaVrtujgQO1Sk";

export const OFFICIAL_RIVERSTONE_MARK =
  "https://lh3.googleusercontent.com/aida/AEtjO1XasxiGISVbwyT2oYKLeMM-kKqZ6AQquUTQIPnxTk36J4YAWihA9zHYs-QNjkr4TsjlZl9r9enSShzU8MXYpHKoP_EwKOk5yUf6R04B4UxRMr0jlFs_S8h20HHZYftfH8xmkjyE4lkiRRc0VWYAU9mpQbVmiXXjovHVN3BY1yQb31j7HqrhKwyPR9IiZ_6iuIhz1oSR6AkZGf9IhtQv49dMo8elUZCibNKmrEC1EQ5JH6VcFHmrB4OVkD0";

/**
 * PebbleMascot - The official Sanctuary riverstone companion.
 * 
 * Supports 16 official Google Stitch poses, custom sizes, breathing micro-animations,
 * and seamless fallback handling.
 */
export default function PebbleMascot({
  pose = "resting", // semantic name or key in MASCOT_POSES
  size = "md",      // "xs" (20px), "sm" (28px), "md" (40px), "lg" (80px), "xl" (128px), "2xl" (180px), "hero" (260px)
  className = "",
  animate = true,
  caption = "",
  onClick,
}) {
  const [useFallback, setUseFallback] = useState(false);

  const resolvedKey = POSE_ALIASES[pose] || pose;
  const imageSrc = useFallback
    ? OFFICIAL_STITCH_CLOUD_IMG
    : MASCOT_POSES[resolvedKey] || MASCOT_POSES.listening;

  const sizeDimensions = {
    xs: "w-5 h-5",
    sm: "w-7 h-7",
    md: "w-10 h-10",
    lg: "w-20 h-20",
    xl: "w-32 h-32",
    "2xl": "w-44 h-44",
    hero: "w-64 h-64 sm:w-72 sm:h-72",
  };

  const containerClasses = `${sizeDimensions[size] || sizeDimensions.md} ${className} relative inline-flex flex-col items-center justify-center shrink-0 select-none ${
    onClick ? "cursor-pointer hover:scale-105 active:scale-95 transition-transform" : ""
  }`;

  return (
    <div
      className={containerClasses}
      onClick={onClick}
      title={caption || `Sanctuary Pebble Mascot (${resolvedKey})`}
    >
      <img
        src={imageSrc}
        alt={`Sanctuary Pebble mascot · ${resolvedKey}`}
        onError={() => setUseFallback(true)}
        className={`w-full h-full object-contain filter drop-shadow-xs transition-transform duration-700 ${
          animate && (resolvedKey === "breathing" || pose === "calm")
            ? "animate-pulse"
            : ""
        }`}
      />

      {caption && (
        <span className="font-label-sm text-[11px] text-secondary mt-1 text-center font-normal">
          {caption}
        </span>
      )}
    </div>
  );
}
