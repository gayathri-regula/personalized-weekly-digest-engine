import React, { useEffect } from "react";
import { CreateUserForm } from "./CreateUserForm";
import { UserSelector } from "./UserSelector";
import { User } from "../types";

interface SideDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedUserId: string | null;
  onUserSelect: (user: User) => void;
  onUserCreated: (newUser: User) => void;
  refreshKey: number;
}

export const SideDrawer: React.FC<SideDrawerProps> = ({
  isOpen,
  onClose,
  selectedUserId,
  onUserSelect,
  onUserCreated,
  refreshKey,
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

  const handleSelectUser = (user: User) => {
    onUserSelect(user);
    onClose();
  };

  const handleCreateUser = (newUser: User) => {
    onUserCreated(newUser);
    onClose();
  };

  return (
    <>
      {/* Background Overlay */}
      <div
        className={`drawer-overlay ${isOpen ? "visible" : ""}`}
        onClick={onClose}
        aria-hidden={!isOpen}
      />

      {/* Slide-out Drawer Panel */}
      <aside className={`side-drawer ${isOpen ? "open" : ""}`}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <span className="drawer-icon">👤</span>
            <h2 className="drawer-title">User Controls</h2>
          </div>
          <button
            onClick={onClose}
            className="drawer-close-btn"
            aria-label="Close user controls drawer"
          >
            ✕
          </button>
        </div>

        <div className="drawer-content">
          {/* Section 1: User Profile Selection */}
          <section className="drawer-section">
            <UserSelector
              selectedUserId={selectedUserId}
              onUserSelect={handleSelectUser}
              refreshKey={refreshKey}
            />
          </section>

          <hr className="drawer-divider" />

          {/* Section 2: New User Onboarding Form */}
          <section className="drawer-section">
            <CreateUserForm onUserCreated={handleCreateUser} />
          </section>
        </div>
      </aside>
    </>
  );
};
