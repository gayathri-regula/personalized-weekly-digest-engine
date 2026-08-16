import React from "react";
import { User } from "../types";

interface TopHeaderProps {
  user: User | null;
  onOpenDrawer: () => void;
  onShowToast: (message: string) => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  user,
  onOpenDrawer,
  onShowToast,
}) => {
  const getGreetingTime = (): string => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const firstName = user ? user.name.split(" ")[0] : "Guest";
  const greeting = `${getGreetingTime()}, ${firstName}`;

  return (
    <header className="redesign-top-header">
      {/* Greeting Title */}
      <div className="redesign-header-greeting">
        <h1 className="redesign-greeting-title">{greeting} 👋</h1>
        <p className="redesign-greeting-sub">
          Here is your personalized AI activity digest overview.
        </p>
      </div>

      {/* Center Search Bar (Visual Placeholder, Light Styling) */}
      <div className="redesign-header-search">
        <div
          className="redesign-search-box"
          onClick={() =>
            onShowToast("This feature is scheduled for a future update.")
          }
          title="Global Search (Coming Soon)"
        >
          <span className="search-box-icon">🔍</span>
          <input
            type="text"
            className="search-box-input"
            placeholder="Search digest stories, topics, tags..."
            disabled
            readOnly
          />
          <span className="search-box-shortcut">⌘K</span>
        </div>
      </div>

      {/* Right Controls (Notification Bell & Profile Avatar) */}
      <div className="redesign-header-controls">
        <button
          type="button"
          className="btn-header-bell"
          onClick={() =>
            onShowToast("This feature is scheduled for a future update.")
          }
          title="Notifications (Coming Soon)"
          aria-label="Notifications"
        >
          <span className="bell-icon-text">🔔</span>
          <span className="bell-badge-count">3</span>
        </button>

        <button
          type="button"
          className="btn-header-avatar"
          onClick={onOpenDrawer}
          title="Manage Profile & Interests"
          aria-label="User Profile Menu"
        >
          <div className="avatar-circle-sm">
            {user ? user.name.charAt(0).toUpperCase() : "👤"}
          </div>
          <span className="avatar-label-name">{user ? firstName : "Select"}</span>
          <span className="avatar-dropdown-arrow">▾</span>
        </button>
      </div>
    </header>
  );
};
