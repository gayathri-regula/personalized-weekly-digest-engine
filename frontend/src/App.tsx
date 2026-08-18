import React, { useState } from "react";
import { ActivityHistoryView } from "./components/ActivityHistoryView";
import { DigestView } from "./components/DigestView";
import { LeftSidebar } from "./components/LeftSidebar";
import { SavedItemsView } from "./components/SavedItemsView";
import { SharedDigestView } from "./components/SharedDigestView";
import { SideDrawer } from "./components/SideDrawer";
import { TopHeader } from "./components/TopHeader";
import { User } from "./types";
import "./App.css";

export const App: React.FC = () => {
  // Check if current browser URL is a public share link (/share/{token})
  const pathname = window.location.pathname;
  const shareMatch = pathname.match(/^\/share\/([^/]+)/);

  if (shareMatch) {
    const shareToken = shareMatch[1];
    return <SharedDigestView token={shareToken} />;
  }

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [userRefreshKey, setUserRefreshKey] = useState<number>(0);
  const [activeNav, setActiveNav] = useState<string>("dashboard");

  // Toast notification state for placeholder interactions
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (message: string) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage((current) => (current === message ? null : current));
    }, 3500);
  };

  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
  };

  const handleUserCreated = (newUser: User) => {
    setUserRefreshKey((prev) => prev + 1);
    setSelectedUser(newUser);
  };

  const handleNavSelect = (navKey: string) => {
    setActiveNav(navKey);
    if (navKey === "interests") {
      setIsDrawerOpen(true);
    }
  };

  return (
    <div className="redesign-app-shell">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="redesign-toast-banner" role="alert">
          <span className="toast-icon">ℹ️</span>
          <span className="toast-message">{toastMessage}</span>
          <button
            type="button"
            className="btn-close-toast"
            onClick={() => setToastMessage(null)}
            aria-label="Close notification"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Dashboard Layout Container */}
      <div className="redesign-dashboard-layout">
        {/* Left Sidebar Navigation */}
        <LeftSidebar
          selectedUser={selectedUser}
          activeNav={activeNav}
          onNavSelect={handleNavSelect}
          onOpenDrawer={() => setIsDrawerOpen(true)}
          onShowToast={showToast}
        />

        {/* Main Content Area */}
        <main className="redesign-main-content">
          <div className="redesign-content-container">
            {/* Top Greeting Header */}
            <TopHeader
              user={selectedUser}
              onOpenDrawer={() => setIsDrawerOpen(true)}
            />

            {/* Redesigned Main Digest / Saved / History Display Area */}
            <section className="digest-display-area">
              {activeNav === "saved" ? (
                <SavedItemsView
                  user={selectedUser}
                  onOpenDrawer={() => setIsDrawerOpen(true)}
                />
              ) : activeNav === "history" ? (
                <ActivityHistoryView
                  user={selectedUser}
                  onOpenDrawer={() => setIsDrawerOpen(true)}
                />
              ) : (
                <DigestView
                  user={selectedUser}
                  onOpenDrawer={() => setIsDrawerOpen(true)}
                  onOpenEditInterests={() => setIsDrawerOpen(true)}
                  onShowToast={showToast}
                  onUserUpdated={(updatedUser) => setSelectedUser(updatedUser)}
                />
              )}
            </section>
          </div>
        </main>
      </div>

      {/* Side Drawer Component */}
      <SideDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        selectedUser={selectedUser}
        onUserSelect={handleUserSelect}
        onUserCreated={handleUserCreated}
        refreshKey={userRefreshKey}
      />
    </div>
  );
};

export default App;
