import React, { useEffect, useRef, useState } from "react";

interface InterestMultiSelectProps {
  availableInterests: string[];
  selectedTags: string[];
  onChange: (newTags: string[]) => void;
  disabled?: boolean;
}

export const InterestMultiSelect: React.FC<InterestMultiSelectProps> = ({
  availableInterests,
  selectedTags,
  onChange,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Click-outside listener to close the dropdown menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleToggleTag = (tag: string) => {
    if (disabled) return;
    if (selectedTags.includes(tag)) {
      onChange(selectedTags.filter((t) => t !== tag));
    } else {
      if (selectedTags.length < 4) {
        onChange([...selectedTags, tag]);
      }
    }
  };

  const renderSummaryText = () => {
    if (selectedTags.length === 0) {
      return "Select 2-4 interest topics...";
    }
    return `${selectedTags.length} selected: ${selectedTags.join(", ")}`;
  };

  return (
    <div
      ref={dropdownRef}
      className={`multi-select-dropdown ${disabled ? "dropdown-disabled" : ""}`}
    >
      {/* Closed State Summary Bar */}
      <button
        type="button"
        className={`dropdown-trigger ${isOpen ? "trigger-open" : ""}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        aria-expanded={isOpen}
      >
        <span
          className={`summary-text ${selectedTags.length === 0 ? "placeholder-summary" : ""}`}
        >
          {renderSummaryText()}
        </span>
        <span className={`dropdown-chevron ${isOpen ? "chevron-up" : ""}`}>
          ▼
        </span>
      </button>

      {/* Expanded Dropdown Menu Options */}
      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-menu-header">
            <span>Select 2 to 4 interests:</span>
            <span className="selection-count-badge">
              {selectedTags.length}/4
            </span>
          </div>
          <div className="options-list">
            {availableInterests.map((tag) => {
              const isChecked = selectedTags.includes(tag);
              const isMaxReached = selectedTags.length >= 4;
              const isOptionDisabled = !isChecked && isMaxReached;

              return (
                <label
                  key={tag}
                  className={`dropdown-option ${isChecked ? "option-selected" : ""} ${
                    isOptionDisabled ? "option-disabled" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    className="option-checkbox"
                    checked={isChecked}
                    onChange={() => handleToggleTag(tag)}
                    disabled={isOptionDisabled || disabled}
                  />
                  <span className="custom-option-check">
                    {isChecked ? "✓" : ""}
                  </span>
                  <span className="option-label-text">{tag}</span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
