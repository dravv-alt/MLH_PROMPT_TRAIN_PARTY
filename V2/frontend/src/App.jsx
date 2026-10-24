import React, { useState, useEffect } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import TopNavigation from "./components/TopNavigation";
import StoneCurtain from "./components/StoneCurtain";
import LandingPage from "./pages/LandingPage";
import TalkPage from "./pages/TalkPage";
import MomentsPage from "./pages/MomentsPage";
import RememberedPage from "./pages/RememberedPage";
import CalmPage from "./pages/CalmPage";
import PrivacyPage from "./pages/PrivacyPage";
import HowThisWasReadPage from "./pages/HowThisWasReadPage";

export default function App() {
  const [isCurtainOpen, setIsCurtainOpen] = useState(false);
  const location = useLocation();

  // Global 'Escape' key listener to drop/lift the stone curtain
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (e.key === "Escape") {
        setIsCurtainOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-background font-body-md text-on-surface flex flex-col selection:bg-secondary-fixed selection:text-on-secondary-fixed">
      {/* Stone Curtain Privacy Shield */}
      <StoneCurtain
        isOpen={isCurtainOpen}
        onClose={() => setIsCurtainOpen(false)}
      />

      {/* Top Folio Header */}
      <TopNavigation
        onToggleCurtain={() => setIsCurtainOpen((prev) => !prev)}
      />

      {/* Main Sanctuary Route Canvas */}
      <main className="w-full flex-1 flex flex-col">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/talk" element={<TalkPage />} />
          <Route path="/moments" element={<MomentsPage />} />
          <Route path="/remembered" element={<RememberedPage />} />
          <Route path="/calm" element={<CalmPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/how-this-was-read" element={<HowThisWasReadPage />} />

          {/* Graceful aliases for legacy routes */}
          <Route path="/chat" element={<Navigate to="/talk" replace />} />
          <Route path="/journal" element={<Navigate to="/moments" replace />} />
          <Route path="/memory" element={<Navigate to="/remembered" replace />} />
          <Route path="/settings" element={<Navigate to="/privacy" replace />} />
          <Route path="/analysis" element={<Navigate to="/how-this-was-read" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
