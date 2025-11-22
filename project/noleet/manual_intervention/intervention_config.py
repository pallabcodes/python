"""Configuration for manual intervention system."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class InterventionConfig:
    """Configuration for manual intervention workflows."""

    # Enable/disable manual intervention
    enabled: bool = False

    # Intervention points in workflows
    intervention_points: list[str] = None

    # Data export settings
    export_format: str = "json"  # json, markdown, yaml
    export_directory: Optional[Path] = None
    include_raw_data: bool = True
    include_analysis: bool = True

    # Manual processing settings
    max_wait_time_seconds: int = 3600  # 1 hour default
    polling_interval_seconds: int = 30
    auto_resume_on_file_change: bool = True

    # Notification settings
    notify_on_pause: bool = True
    notification_command: Optional[str] = None  # e.g., "osascript -e 'display notification..."
    desktop_notifications: bool = True
    email_notifications: bool = False
    email_recipient: Optional[str] = None

    # Resume conditions
    resume_on_file_pattern: str = "manual_*.json"
    resume_on_directory_change: bool = True
    auto_resume_delay_seconds: int = 5  # Check for completion every 5 seconds

    # Quality control
    validate_manual_input: bool = True
    require_expert_signature: bool = True
    quality_score_threshold: float = 0.7

    # User experience
    create_status_files: bool = True  # Create .status files for progress tracking
    generate_external_prompts: bool = True  # Create prompts for external LLMs

    # Backup and versioning
    create_backups: bool = True
    max_backup_versions: int = 5

    # Advanced settings
    allow_partial_resume: bool = False
    custom_prompt_templates: Dict[str, str] = None

    def __post_init__(self):
        """Initialize defaults after dataclass creation."""
        if self.intervention_points is None:
            self.intervention_points = ["project_recommendation_agent"]

        if self.export_directory is None:
            self.export_directory = Path.home() / ".noleet" / "manual_intervention"

        if self.custom_prompt_templates is None:
            self.custom_prompt_templates = self._get_default_templates()

        # Ensure export directory exists
        self.export_directory.mkdir(parents=True, exist_ok=True)

    def _get_default_templates(self) -> Dict[str, str]:
        """Get default prompt templates for manual intervention."""
        return {
            "project_recommendation": """
# Manual Project Recommendation

## Context
User Query: {user_query}
Selected Topics: {topics}
Available Projects: {project_count}

## Gathered Data
{analysis_data}

## Current AI Recommendations
{ai_recommendations}

## Manual Recommendation Task
Based on the above context and data, create project recommendations in JSON format:

```json
{{
  "recommendations": [
    {{
      "project_id": "project_identifier",
      "title": "Project Title",
      "confidence_score": 0.0-1.0,
      "reasoning": "Why this project matches",
      "key_topics": ["topic1", "topic2"],
      "estimated_complexity": "beginner|intermediate|advanced",
      "learning_objectives": ["objective1", "objective2"]
    }}
  ],
  "metadata": {{
    "manual_reviewer": "Your Name",
    "review_timestamp": "ISO timestamp",
    "additional_notes": "Any additional insights"
  }}
}}
```

## Instructions
1. Review the user query and selected topics carefully
2. Analyze the available projects and their relevance
3. Consider the AI recommendations but apply your expertise
4. Create 3-5 high-quality recommendations
5. Focus on projects that provide genuine learning value
6. Ensure recommendations align with user's goals

Save this file as: manual_recommendations_{timestamp}.json
""",
            "question_analysis": """
# Manual Question Analysis

## Question Details
Title: {question_title}
Content: {question_content}
Source: {source}

## AI Analysis Results
Difficulty: {ai_difficulty}
Topics: {ai_topics}
Quality Score: {ai_quality_score}

## Manual Analysis Task
Provide enhanced analysis in JSON format:

```json
{{
  "difficulty": {{
    "level": "easy|medium|hard",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed reasoning for difficulty assessment"
  }},
  "topics": [
    {{
      "topic": "DSA_TOPIC_ENUM",
      "confidence": 0.0-1.0,
      "relevance_reason": "Why this topic applies"
    }}
  ],
  "quality_assessment": {{
    "overall_score": 0.0-1.0,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "improvement_suggestions": ["suggestion1", "suggestion2"]
  }},
  "educational_value": {{
    "target_audience": "beginners|intermediate|advanced",
    "learning_objectives": ["objective1", "objective2"],
    "prerequisites": ["prereq1", "prereq2"]
  }}
}}
```
"""
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "InterventionConfig":
        """Create config from dictionary."""
        # Handle Path objects
        if "export_directory" in config_dict and config_dict["export_directory"]:
            config_dict["export_directory"] = Path(config_dict["export_directory"])

        return cls(**config_dict)

    @classmethod
    def from_json_file(cls, config_path: Path) -> "InterventionConfig":
        """Load config from JSON file."""
        if not config_path.exists():
            return cls()  # Return defaults

        with open(config_path, "r") as f:
            config_dict = json.load(f)

        return cls.from_dict(config_dict)

    @classmethod
    def from_env(cls) -> "InterventionConfig":
        """Create config from environment variables."""
        config = cls()

        # Check environment variables
        if os.getenv("NOLEET_MANUAL_INTERVENTION_ENABLED", "").lower() in ("true", "1"):
            config.enabled = True

        if os.getenv("NOLEET_INTERVENTION_POINTS"):
            config.intervention_points = os.getenv("NOLEET_INTERVENTION_POINTS").split(",")

        if os.getenv("NOLEET_EXPORT_FORMAT"):
            config.export_format = os.getenv("NOLEET_EXPORT_FORMAT")

        if os.getenv("NOLEET_EXPORT_DIR"):
            config.export_directory = Path(os.getenv("NOLEET_EXPORT_DIR"))

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        config_dict = asdict(self)
        # Convert Path to string for JSON serialization
        if isinstance(config_dict.get("export_directory"), Path):
            config_dict["export_directory"] = str(config_dict["export_directory"])

        return config_dict

    def save_to_file(self, config_path: Path) -> None:
        """Save config to JSON file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_prompt_template(self, intervention_type: str) -> str:
        """Get prompt template for intervention type."""
        return self.custom_prompt_templates.get(
            intervention_type,
            self.custom_prompt_templates.get("project_recommendation", "")
        )

    def should_intervene_at(self, agent_type: str) -> bool:
        """Check if intervention is needed at this agent."""
        return self.enabled and agent_type in self.intervention_points

    def get_export_path(self, intervention_type: str, timestamp: str) -> Path:
        """Get export path for intervention data."""
        filename = f"{intervention_type}_data_{timestamp}.{self.export_format}"
        return self.export_directory / filename

    def get_resume_pattern(self) -> str:
        """Get file pattern for resume detection."""
        return self.resume_on_file_pattern
