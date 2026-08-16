import React from "react";
import { DigestSection } from "../utils/groupDigestItems";
import { getCategoryTheme } from "../utils/categoryIcons";

interface CategoryHighlightsProps {
  sections: DigestSection[];
  selectedCategory: string | null;
  onSelectCategory: (categoryId: string | null) => void;
}

export const CategoryHighlights: React.FC<CategoryHighlightsProps> = ({
  sections,
  selectedCategory,
  onSelectCategory,
}) => {
  if (!sections || sections.length === 0) return null;

  return (
    <section className="redesign-category-highlights">
      <div className="category-section-title-row">
        <div className="category-title-group">
          <span className="category-title-icon">🔥</span>
          <h3 className="category-title-heading">Top Highlights</h3>
        </div>
        {selectedCategory && (
          <button
            type="button"
            className="btn-clear-category-filter"
            onClick={() => onSelectCategory(null)}
          >
            Show All Sections ✕
          </button>
        )}
      </div>

      <div className="category-cards-flex-grid">
        {/* "All Highlights" Card */}
        <div
          className={`category-highlight-tile ${
            selectedCategory === null ? "is-selected" : ""
          }`}
          onClick={() => onSelectCategory(null)}
          role="button"
          tabIndex={0}
        >
          <div
            className="category-tile-badge"
            style={{
              background: "linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)",
              borderColor: "#6366f1",
            }}
          >
            🌟
          </div>
          <div className="category-tile-info">
            <span className="category-tile-name">All Highlights</span>
            <span className="category-tile-count">
              {sections.reduce((acc, s) => acc + s.items.length, 0)} Stories
            </span>
          </div>
        </div>

        {/* Dynamic Category Cards */}
        {sections.map((sec) => {
          const theme = getCategoryTheme(sec.title);
          const isSelected = selectedCategory === sec.id;

          return (
            <div
              key={sec.id}
              className={`category-highlight-tile ${isSelected ? "is-selected" : ""}`}
              onClick={() => onSelectCategory(sec.id)}
              role="button"
              tabIndex={0}
            >
              <div
                className="category-tile-badge"
                style={{
                  background: theme.gradient,
                  borderColor: theme.borderColor,
                }}
              >
                {theme.icon}
              </div>
              <div className="category-tile-info">
                <span className="category-tile-name">{sec.title}</span>
                <span className="category-tile-count">
                  {sec.items.length} {sec.items.length === 1 ? "Story" : "Stories"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
