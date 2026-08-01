import React, { useEffect, useState } from "react";
import { generateDigest, getInterests, updateUserInterests } from "../api/client";
import { InterestMultiSelect } from "./InterestMultiSelect";
import { User } from "../types";

interface EditInterestsFormProps {
  user: User;
  onUpdated: (updatedUser: User) => void;
}

export const EditInterestsForm: React.FC<EditInterestsFormProps> = ({
  user,
  onUpdated,
}) => {
  const [availableInterests, setAvailableInterests] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>(
    user.interest_tags || []
  );
  const [loadingInterests, setLoadingInterests] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [updatedUser, setUpdatedUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedTags(user.interest_tags || []);
    setUpdatedUser(null);
    setError(null);
  }, [user]);

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

  const initialSorted = [...(user.interest_tags || [])].sort().join(",");
  const currentSorted = [...selectedTags].sort().join(",");
  const isChanged = initialSorted !== currentSorted;

  const isTagsValid = selectedTags.length >= 2 && selectedTags.length <= 4;
  const canSave = isChanged && isTagsValid && !isSaving;

  // Step 1: Save interest changes ONLY
  const handleSaveChanges = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSave) return;

    setIsSaving(true);
    setError(null);

    try {
      const savedUser = await updateUserInterests(user.id, selectedTags);
      setUpdatedUser(savedUser);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to update profile interests.";
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  // Step 2: Regenerate digest for user
  const handleRegenerateDigest = async () => {
    if (!updatedUser) return;

    setIsGenerating(true);
    setError(null);

    try {
      await generateDigest(updatedUser.id);
      const userToSelect = updatedUser;
      setUpdatedUser(null);
      onUpdated(userToSelect);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Failed to regenerate digest.";
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="edit-interests-card">
      <div className="edit-interests-header">
        <span className="edit-interests-badge">⚙️ Preferences</span>
        <h3 className="edit-interests-title">
          Edit Interests for {user.name.split(" ")[0]}
        </h3>
        <p className="edit-interests-subtitle">
          Update tracked topics to customize relevance ranking.
        </p>
      </div>

      {error && (
        <div className="form-error-banner">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Confirmation Step: Interests updated, prompt user to regenerate digest */}
      {updatedUser ? (
        <div className="step-confirmation-box">
          <div className="confirmation-banner-success">
            <span className="confirm-icon">✅</span>
            <div className="confirm-text">
              <strong>Interests updated!</strong>
              <p>Regenerate your digest below.</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleRegenerateDigest}
            disabled={isGenerating}
            className="btn-step-action btn-regenerate-step"
          >
            {isGenerating ? (
              <>
                <span className="spinner-icon-sm"></span> Generating your digest...
              </>
            ) : (
              <>
                <span>⚡</span> Regenerate Digest
              </>
            )}
          </button>
        </div>
      ) : (
        /* Interest Selection Form */
        <form onSubmit={handleSaveChanges} className="edit-interests-form">
          <div className="form-field-group">
            <div className="interests-header-row">
              <label className="form-label">Tracked Topics</label>
              <span className="interests-counter-pill">
                {selectedTags.length} / 4 Selected
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
                disabled={isSaving}
              />
            )}

            <div className="interests-hint-row">
              {selectedTags.length < 2 ? (
                <span className="hint-warning">
                  💡 Select at least 2 interests ({2 - selectedTags.length} more needed).
                </span>
              ) : selectedTags.length === 4 ? (
                <span className="hint-info">
                  ✓ Maximum of 4 interest topics selected.
                </span>
              ) : !isChanged ? (
                <span className="hint-info">
                  Change selection to save updated preferences.
                </span>
              ) : (
                <span className="hint-success">
                  ✓ Ready to save new interest preferences.
                </span>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={!canSave}
            className="btn-submit-edit-interests"
          >
            {isSaving ? (
              <>
                <span className="spinner-icon-sm"></span> Saving changes...
              </>
            ) : (
              <>Save Changes</>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
