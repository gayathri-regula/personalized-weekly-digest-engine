import React from "react";
import { User } from "../types";

interface LeftSidebarProps {
  selectedUser: User | null;
  activeNav: string;
  onNavSelect: (navKey: string) => void;
  onOpenDrawer: () => void;
  onShowToast: (message: string) => void;
}

interface NavItemDef {
  key: string;
  label: string;
  icon: string;
  isFunctional: boolean;
}

const NAV_ITEMS: NavItemDef[] = [
  { key: "dashboard", label: "Dashboard", icon: "📊", isFunctional: true },
  { key: "my-digest", label: "My Digest", icon: "📰", isFunctional: true },
  { key: "interests", label: "Interests", icon: "🎯", isFunctional: true },
  { key: "sources", label: "Sources", icon: "📡", isFunctional: false },
  { key: "saved", label: "Saved", icon: "🔖", isFunctional: false },
  { key: "history", label: "History", icon: "🕒", isFunctional: false },
  { key: "voice-digest", label: "Voice Digest", icon: "🎙️", isFunctional: false },
  { key: "settings", label: "Settings", icon: "⚙️", isFunctional: false },
  { key: "feedback", label: "Feedback", icon: "💬", isFunctional: false },
];

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  selectedUser,
  activeNav,
  onNavSelect,
  onOpenDrawer,
  onShowToast,
}) => {
  const handleItemClick = (item: NavItemDef) => {
    if (!item.isFunctional) {
      onShowToast(`This feature is scheduled for a future update.`);
      return;
    }
    if (item.key === "interests") {
      onOpenDrawer();
      onNavSelect("interests");
      return;
    }
    onNavSelect(item.key);
  };

  return (
    <aside className="redesign-left-sidebar">
      {/* Brand Header */}
      <div className="redesign-sidebar-brand">
        <span className="redesign-brand-icon">⚡</span>
        <div className="redesign-brand-titles">
          <span className="redesign-brand-name">SFCollab Digest</span>
          <span className="redesign-brand-sub">AI Digest Engine</span>
        </div>
      </div>

      {/* User Profile Switcher Card */}
      <div className="redesign-profile-card">
        <div className="redesign-profile-avatar">
          {selectedUser ? selectedUser.name.charAt(0).toUpperCase() : "?"}
        </div>
        <div className="redesign-profile-info">
          <span className="redesign-profile-name">
            {selectedUser ? selectedUser.name : "Select Profile"}
          </span>
          <span className="redesign-profile-sub">
            {selectedUser
              ? `${selectedUser.interest_tags.length} Topics Followed`
              : "No user selected"}
          </span>
        </div>
        <button
          type="button"
          onClick={onOpenDrawer}
          className="btn-switch-profile"
          title="Switch user profile"
          aria-label="Switch user profile"
        >
          🔄
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="redesign-sidebar-nav">
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

      {/* Footer System Indicator */}
      <div className="redesign-sidebar-footer">
        <div className="redesign-system-status">
          <span className="status-dot-green"></span>
          <span>Live Supabase Postgres</span>
        </div>
      </div>
    </aside>
  );
};
