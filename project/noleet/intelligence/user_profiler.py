"""User profiling for personalized recommendations."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
from datetime import datetime


class UserProfiler:
    """Manages user profiles for personalized recommendations."""

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize user profiler.

        Args:
            storage_dir: Directory to store user profiles
            logger: Optional logger instance
        """
        self._storage_dir = storage_dir or Path.home() / ".noleet" / "profiles"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger or logging.getLogger(__name__)

        # In-memory cache
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._load_profiles()

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile.

        Args:
            user_id: User identifier

        Returns:
            User profile or None if not found
        """
        return self._profiles.get(user_id)

    def create_profile(
        self,
        user_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user profile.

        Args:
            user_id: User identifier
            initial_data: Initial profile data

        Returns:
            Created profile
        """
        profile = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "preferred_difficulty": "intermediate",
            "preferred_project_types": [],
            "skill_levels": {},
            "completed_projects": [],
            "feedback_history": [],
            "interaction_count": 0,
            **(initial_data or {})
        }

        self._profiles[user_id] = profile
        self._save_profile(user_id)

        self._logger.info(f"Created profile for user: {user_id}")
        return profile

    def update_profile(self, user_id: str, updates: Dict[str, Any]):
        """
        Update user profile.

        Args:
            user_id: User identifier
            updates: Profile updates
        """
        if user_id not in self._profiles:
            self.create_profile(user_id)

        profile = self._profiles[user_id]
        profile.update(updates)
        profile["last_updated"] = datetime.utcnow().isoformat()

        self._save_profile(user_id)

        self._logger.debug(f"Updated profile for user: {user_id}")

    def update_feedback(
        self,
        user_id: str,
        project_id: str,
        rating: float,
        feedback: Optional[str] = None
    ):
        """
        Update profile with user feedback.

        Args:
            user_id: User identifier
            project_id: Project identifier
            rating: Rating (0.0 to 1.0)
            feedback: Optional feedback text
        """
        if user_id not in self._profiles:
            self.create_profile(user_id)

        profile = self._profiles[user_id]

        # Add to feedback history
        feedback_entry = {
            "project_id": project_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        }

        profile["feedback_history"].append(feedback_entry)

        # Update skill levels based on feedback
        self._update_skill_levels_from_feedback(profile, project_id, rating)

        # Update interaction count
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1

        profile["last_updated"] = datetime.utcnow().isoformat()
        self._save_profile(user_id)

    def _update_skill_levels_from_feedback(
        self,
        profile: Dict[str, Any],
        project_id: str,
        rating: float
    ):
        """Update skill levels based on project completion feedback."""
        # This is a simplified implementation
        # In a real system, you'd analyze the project's DSA topics
        # and update skill levels accordingly

        skill_levels = profile.get("skill_levels", {})

        # Generic skill improvement based on rating
        improvement = (rating - 0.5) * 0.1  # Small improvement for good ratings

        # Update general DSA skill
        current_skill = skill_levels.get("dsa_general", 0.5)
        skill_levels["dsa_general"] = max(0.0, min(1.0, current_skill + improvement))

        profile["skill_levels"] = skill_levels

    def track_project_interaction(
        self,
        user_id: str,
        project_id: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track user interaction with a project.

        Args:
            user_id: User identifier
            project_id: Project identifier
            interaction_type: Type of interaction (view, start, complete, etc.)
            metadata: Additional metadata
        """
        if user_id not in self._profiles:
            self.create_profile(user_id)

        profile = self._profiles[user_id]

        interaction = {
            "project_id": project_id,
            "interaction_type": interaction_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        if "interactions" not in profile:
            profile["interactions"] = []

        profile["interactions"].append(interaction)
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        profile["last_updated"] = datetime.utcnow().isoformat()

        self._save_profile(user_id)

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences for recommendations.

        Args:
            user_id: User identifier

        Returns:
            User preferences
        """
        profile = self.get_profile(user_id)
        if not profile:
            return {}

        return {
            "preferred_difficulty": profile.get("preferred_difficulty", "intermediate"),
            "preferred_project_types": profile.get("preferred_project_types", []),
            "skill_levels": profile.get("skill_levels", {}),
            "avoid_completed": True
        }

    def get_similar_users(self, user_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Find users with similar profiles.

        Args:
            user_id: User identifier
            limit: Maximum similar users to return

        Returns:
            List of (user_id, similarity_score) tuples
        """
        target_profile = self.get_profile(user_id)
        if not target_profile:
            return []

        similarities = []

        for other_id, profile in self._profiles.items():
            if other_id == user_id:
                continue

            similarity = self._calculate_profile_similarity(target_profile, profile)
            similarities.append((other_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def _calculate_profile_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """Calculate similarity between two profiles."""
        similarity = 0.0
        factors = 0

        # Difficulty preference
        if profile1.get("preferred_difficulty") == profile2.get("preferred_difficulty"):
            similarity += 0.3
        factors += 1

        # Project types
        types1 = set(profile1.get("preferred_project_types", []))
        types2 = set(profile2.get("preferred_project_types", []))
        if types1 and types2:
            overlap = len(types1.intersection(types2))
            type_similarity = overlap / max(len(types1), len(types2))
            similarity += type_similarity * 0.4
            factors += 1

        # Skill levels
        skills1 = profile1.get("skill_levels", {})
        skills2 = profile2.get("skill_levels", {})
        if skills1 and skills2:
            common_skills = set(skills1.keys()).intersection(set(skills2.keys()))
            if common_skills:
                skill_diff = sum(abs(skills1[s] - skills2[s]) for s in common_skills)
                skill_similarity = 1.0 - (skill_diff / len(common_skills))
                similarity += skill_similarity * 0.3
                factors += 1

        return similarity / factors if factors > 0 else 0.0

    def _load_profiles(self):
        """Load user profiles from storage."""
        for profile_file in self._storage_dir.glob("*.json"):
            try:
                with open(profile_file, "r") as f:
                    profile = json.load(f)
                    user_id = profile["user_id"]
                    self._profiles[user_id] = profile
            except Exception as e:
                self._logger.error(f"Failed to load profile {profile_file}: {e}")

        self._logger.info(f"Loaded {len(self._profiles)} user profiles")

    def _save_profile(self, user_id: str):
        """Save user profile to storage."""
        profile = self._profiles[user_id]
        profile_file = self._storage_dir / f"{user_id}.json"

        try:
            with open(profile_file, "w") as f:
                json.dump(profile, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save profile for {user_id}: {e}")

    def get_profile_count(self) -> int:
        """Get total number of profiles."""
        return len(self._profiles)

    def cleanup_old_profiles(self, days: int = 365):
        """Clean up profiles that haven't been updated recently."""
        # Implementation for cleaning up inactive profiles
        pass

