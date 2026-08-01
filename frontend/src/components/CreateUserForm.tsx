import React, { useEffect, useState } from "react";
import { createUser, generateDigest, getInterests } from "../api/client";
import { User } from "../types";

interface CreateUserFormProps {
  onUserCreated: (newUser: User) => void;
}

export const CreateUserForm: React.FC<CreateUserFormProps> = ({
  onUserCreated,
}) => {
  const [name, setName] = useState<string>("");
  const [availableInterests, setAvailableInterests] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [loadingInterests, setLoadingInterests] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submittingStep, setSubmittingStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchTaxonomy = async () => {
      setLoadingInterests(true);
      try {
        const list = await getInterests();
        if (isMounted) {
          setAvailableInterests(list);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg =
            err instanceof Error
              ? err.message
              : "Failed to load interest topics.";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoadingInterests(false);
        }
      }
    };

    fetchTaxonomy();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleCheckboxToggle = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      if (selectedTags.length < 4) {
        setSelectedTags([...selectedTags, tag]);
      }
    }
  };

  const isNameValid = name.trim().length >= 1 && name.trim().length <= 100;
  const isTagsValid = selectedTags.length >= 2 && selectedTags.length <= 4;
  const canSubmit = isNameValid && isTagsValid && !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setError(null);

    try {
      setSubmittingStep("Creating profile...");
      const newUser = await createUser(name.trim(), selectedTags);

      setSubmittingStep("Generating your digest...");
      await generateDigest(newUser.id);

      // Reset form
      setName("");
      setSelectedTags([]);

      // Trigger parent callback to auto-select the user
      onUserCreated(newUser);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during user creation.";
      setError(msg);
    } finally {
      setIsSubmitting(false);
      setSubmittingStep("");
    }
  };

  return (
    <div className="create-user-card">
      <div className="create-user-header">
        <span className="create-user-badge">✨ Onboarding</span>
        <h3 className="create-user-title">New here? Create your profile</h3>
        <p className="create-user-subtitle">
          Select 2 to 4 interest topics to receive a personalized weekly digest
          ranking.
        </p>
      </div>

      {error && (
        <div className="form-error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="onboarding-form">
        {/* Name Field */}
        <div className="form-field-group">
          <label htmlFor="user-name-input" className="form-label">
            Full Name <span className="required-star">*</span>
          </label>
          <input
            id="user-name-input"
            type="text"
            className="styled-text-input"
            placeholder="e.g. Grace Hopper"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isSubmitting}
            maxLength={100}
          />
        </div>

        {/* Interests Checkboxes Section */}
        <div className="form-field-group">
          <div className="interests-header-row">
            <label className="form-label">
              Interest Topics <span className="required-star">*</span>
            </label>
            <span className="interests-counter-pill">
              {selectedTags.length} / 4 Selected
            </span>
          </div>

          {loadingInterests ? (
            <div className="interests-loading-box">
              <span className="spinner-icon-sm"></span> Loading available topics...
            </div>
          ) : (
            <div className="interests-checkbox-grid">
              {availableInterests.map((tag) => {
                const isChecked = selectedTags.includes(tag);
                const isDisabled = !isChecked && selectedTags.length >= 4;

                return (
                  <label
                    key={tag}
                    className={`checkbox-chip-label ${isChecked ? "chip-active" : ""} ${isDisabled ? "chip-disabled" : ""}`}
                  >
                    <input
                      type="checkbox"
                      className="hidden-checkbox"
                      checked={isChecked}
                      onChange={() => handleCheckboxToggle(tag)}
                      disabled={isDisabled || isSubmitting}
                    />
                    <span className="custom-checkbox">
                      {isChecked ? "✓" : "+"}
                    </span>
                    <span className="tag-name">{tag}</span>
                  </label>
                );
              })}
            </div>
          )}

          {/* Validation Hint */}
          <div className="interests-hint-row">
            {selectedTags.length < 2 ? (
              <span className="hint-warning">
                💡 Please select at least 2 interests ({2 - selectedTags.length} more needed).
              </span>
            ) : selectedTags.length === 4 ? (
              <span className="hint-info">
                ✓ Maximum of 4 interest topics selected.
              </span>
            ) : (
              <span className="hint-success">
                ✓ Valid selection ({selectedTags.length} topics chosen). You can add up to 4.
              </span>
            )}
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="btn-submit-onboarding"
        >
          {isSubmitting ? (
            <>
              <span className="spinner-icon-sm"></span>
              {submittingStep || "Processing..."}
            </>
          ) : (
            <>
              <span>⚡</span> Create Profile & Generate My Digest
            </>
          )}
        </button>
      </form>
    </div>
  );
};
