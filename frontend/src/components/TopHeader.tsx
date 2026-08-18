import React from "react";
import { User } from "../types";

interface TopHeaderProps {
  user: User | null;
  onOpenNavDrawer: () => void;
  onOpenDrawer: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  user,
  onOpenNavDrawer,
  onOpenDrawer,
}) => {
  const firstName = user ? user.name.split(" ")[0] : "Guest";

  return (
    <header className="redesign-top-header">
      {/* Left Section: Hamburger Icon + Brand Logo */}
      <div className="redesign-header-left">
        <button
          type="button"
          className="btn-hamburger-menu"
          onClick={onOpenNavDrawer}
          title="Open Navigation Menu"
          aria-label="Open Navigation Menu"
        >
          ☰
        </button>

        <div className="redesign-header-brand">
          <span className="redesign-brand-icon">⚡</span>
          <div className="redesign-brand-titles">
            <span className="redesign-brand-name">SFCollab Digest</span>
            <span className="redesign-brand-sub">AI Digest Engine</span>
          </div>
        </div>
      </div>

      {/* Right Controls (Profile Avatar Button) */}
      <div className="redesign-header-controls">
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
