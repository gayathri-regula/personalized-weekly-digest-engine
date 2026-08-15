import React, { useEffect, useState } from "react";
import { createUser, generateDigest, getInterests } from "../api/client";
import { InterestMultiSelect } from "./InterestMultiSelect";
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
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [createdUser, setCreatedUser] = useState<User | null>(null);
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

  const isNameValid = name.trim().length >= 1 && name.trim().length <= 100;
  const isTagsValid = selectedTags.length >= 2;
  const canSubmit = isNameValid && isTagsValid && !isCreating;

  // Step 1: Create user profile ONLY
  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsCreating(true);
    setError(null);

    try {
      const newUser = await createUser(name.trim(), selectedTags);
      setCreatedUser(newUser);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred during user creation.";
      setError(msg);
    } finally {
      setIsCreating(false);
    }
  };

  // Step 2: Generate digest for newly created user
  const handleGenerateDigest = async () => {
    if (!createdUser) return;

    setIsGenerating(true);
    setError(null);

    try {
      await generateDigest(createdUser.id);
      const userToSelect = createdUser;
      // Reset form state
      setCreatedUser(null);
      setName("");
      setSelectedTags([]);
      // Parent callback to select user and close drawer
      onUserCreated(userToSelect);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to generate digest for new user.";
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="create-user-card">
      <div className="create-user-header">
        <span className="create-user-badge">✨ Onboarding</span>
        <h3 className="create-user-title">New here? Create your profile</h3>
        <p className="create-user-subtitle">
          Select 2 or more interest topics to receive a personalized weekly digest
          ranking.
        </p>
      </div>

      {error && (
        <div className="form-error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Confirmation Step: Profile created, prompt user to generate digest */}
      {createdUser ? (
        <div className="step-confirmation-box">
          <div className="confirmation-banner-success">
            <span className="confirm-icon">🎉</span>
            <div className="confirm-text">
              <strong>Profile created for {createdUser.name}!</strong>
              <p>Generate your first digest below.</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGenerateDigest}
            disabled={isGenerating}
            className="btn-step-action btn-generate-step"
          >
            {isGenerating ? (
              <>
                <span className="spinner-icon-sm"></span> Generating your digest...
              </>
            ) : (
              <>
                <span>⚡</span> Generate My Digest
              </>
            )}
          </button>
        </div>
      ) : (
        /* Initial Profile Creation Form */
        <form onSubmit={handleCreateProfile} className="onboarding-form">
          <div className="form-field-group">
            <label htmlFor="user-name-input" className="form-label">
              Full Name
            </label>
            <input
              id="user-name-input"
              type="text"
              className="styled-text-input"
              placeholder="e.g. Grace Hopper"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isCreating}
              maxLength={100}
            />
          </div>

          <div className="form-field-group">
            <div className="interests-header-row">
              <label className="form-label">Interest Topics</label>
              <span className="interests-counter-pill">
                {selectedTags.length} Selected
              </span>
            </div>

            {loadingInterests ? (
              <div className="interests-loading-box">
                <span className="spinner-icon-sm"></span> Loading available topics...
              </div>
            ) : (
              <InterestMultiSelect
                availableInterests={availableInterests}
                selectedTags={selectedTags}
                onChange={setSelectedTags}
                disabled={isCreating}
              />
            )}

            <div className="interests-hint-row">
              {selectedTags.length < 2 ? (
                <span className="hint-warning">
                  💡 Please select at least 2 interests ({2 - selectedTags.length} more needed).
                </span>
              ) : (
                <span className="hint-success">
                  ✓ Valid selection ({selectedTags.length} topics chosen).
                </span>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={!canSubmit}
            className="btn-submit-onboarding"
          >
            {isCreating ? (
              <>
                <span className="spinner-icon-sm"></span> Creating profile...
              </>
            ) : (
              <>Create Profile</>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
