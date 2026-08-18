import React from "react";
import { User } from "../types";

interface TopHeaderProps {
  user: User | null;
  onOpenDrawer: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  user,
  onOpenDrawer,
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

      {/* Right Controls (Profile Avatar) */}
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

