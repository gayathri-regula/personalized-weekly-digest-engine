import React, { useEffect } from "react";
import { BookmarkIcon, HistoryIcon, VoiceIcon } from "./icons/NavIcons";

export interface NavItemDef {
  key: string;
  label: string;
  icon: React.ReactNode;
  isFunctional: boolean;
}

export const NAV_ITEMS: NavItemDef[] = [
  { key: "dashboard", label: "Dashboard", icon: "📊", isFunctional: true },
  { key: "interests", label: "Interests", icon: "🎯", isFunctional: true },
  { key: "saved", label: "Saved", icon: <BookmarkIcon />, isFunctional: true },
  { key: "history", label: "History", icon: <HistoryIcon />, isFunctional: true },
  { key: "voice-digest", label: "Voice Digest", icon: <VoiceIcon />, isFunctional: true },
];

interface NavDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeNav: string;
  onNavSelect: (navKey: string) => void;
  onOpenDrawer: () => void;
  onShowToast: (message: string) => void;
}

export const NavDrawer: React.FC<NavDrawerProps> = ({
  isOpen,
  onClose,
  activeNav,
  onNavSelect,
  onOpenDrawer,
  onShowToast,
}) => {
  // Listen for Escape key press to close drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleItemClick = (item: NavItemDef) => {
    if (!item.isFunctional) {
      onShowToast("This feature is scheduled for a future update.");
      return;
    }
    if (item.key === "interests") {
      onOpenDrawer();
      onNavSelect("interests");
      onClose();
      return;
    }
    onNavSelect(item.key);
    onClose();
  };

  return (
    <>
      {/* Backdrop Scrim */}
      <div
        className={`nav-drawer-backdrop ${isOpen ? "open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-out Navigation Drawer Panel */}
      <aside
        className={`nav-drawer-panel ${isOpen ? "open" : ""}`}
        aria-label="Main Navigation Menu"
      >
        {/* Panel Header */}
        <div className="nav-drawer-header">
          <div className="redesign-header-brand">
            <span className="redesign-brand-icon">⚡</span>
            <div className="redesign-brand-titles">
              <span className="redesign-brand-name">SFCollab Digest</span>
              <span className="redesign-brand-sub">AI Digest Engine</span>
            </div>
          </div>
          <button
            type="button"
            className="btn-close-nav-drawer"
            onClick={onClose}
            title="Close Menu"
            aria-label="Close Navigation Menu"
          >
            ✕
          </button>
        </div>

        {/* Panel Navigation List */}
        <nav className="nav-drawer-body">
          <span className="redesign-nav-section-title">NAVIGATION</span>
          <ul className="redesign-nav-list">
            {NAV_ITEMS.map((item) => {
              const isActive = activeNav === item.key;
              return (
                <li key={item.key}>
                  <button
                    type="button"
                    className={`redesign-nav-btn ${isActive ? "active" : ""} ${
                      !item.isFunctional ? "is-placeholder" : ""
                    }`}
                    onClick={() => handleItemClick(item)}
                  >
                    <span className="nav-btn-icon">{item.icon}</span>
                    <span className="nav-btn-label">{item.label}</span>
                    {!item.isFunctional && (
                      <span className="redesign-soon-badge">Soon</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>
    </>
  );
};
