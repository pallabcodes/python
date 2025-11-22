"""Data exporter for manual intervention processing."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .intervention_config import InterventionConfig

# Optional yaml import
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


class DataExporter:
    """Exports workflow data for manual processing."""

    def __init__(self, config: InterventionConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize data exporter.

        Args:
            config: Intervention configuration
            logger: Optional logger instance
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

    async def export_for_intervention(
        self,
        session_data: Dict[str, Any],
        agent_type: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Export data for manual intervention with comprehensive file structure.

        Args:
            session_data: Intervention session data
            agent_type: Type of agent requesting intervention
            timestamp: Export timestamp

        Returns:
            Export result with all file paths and status
        """
        try:
            session_id = session_data["session_id"]

            # Create intervention directory structure
            intervention_dir = self._config.export_directory / f"session_{session_id}"
            intervention_dir.mkdir(parents=True, exist_ok=True)

            # Prepare export data
            export_data = self._prepare_export_data(session_data, agent_type)

            # Generate different types of prompts
            prompts = self._generate_all_prompts(export_data, agent_type, session_id)

            # Create export files
            files_created = {}

            # 1. Data file (JSON)
            data_file = intervention_dir / f"data.json"
            await self._write_data_file(data_file, export_data)
            files_created["data_file"] = str(data_file)

            # 2. Human-readable prompt (Markdown)
            if self._config.generate_external_prompts:
                prompt_file = intervention_dir / f"prompt.md"
                await self._write_prompt_file(prompt_file, prompts["human_readable"])
                files_created["prompt_file"] = str(prompt_file)

            # 3. Structured prompt for external LLMs
            structured_prompt_file = intervention_dir / f"llm_prompt.json"
            await self._write_structured_prompt(structured_prompt_file, prompts["structured"])
            files_created["structured_prompt_file"] = str(structured_prompt_file)

            # 4. Status file for tracking
            if self._config.create_status_files:
                status_file = intervention_dir / f"status.json"
                await self._create_status_file(status_file, session_data, files_created)
                files_created["status_file"] = str(status_file)

            # 5. Expected output template
            template_file = intervention_dir / f"output_template.json"
            await self._create_output_template(template_file, agent_type)
            files_created["template_file"] = str(template_file)

            # 6. Instructions file
            instructions_file = intervention_dir / f"INSTRUCTIONS.md"
            await self._create_instructions_file(instructions_file, session_id, files_created)
            files_created["instructions_file"] = str(instructions_file)

            # Create backup if enabled
            if self._config.create_backups:
                await self._create_backup(data_file, timestamp)

            # Send notifications
            await self._send_export_notifications(session_data, files_created)

            self._logger.info(f"Complete intervention package exported to {intervention_dir}")

            return {
                "success": True,
                "intervention_dir": str(intervention_dir),
                "files_created": files_created,
                "session_id": session_id,
                "expected_output": str(intervention_dir / "output_template.json")
            }

        except Exception as e:
            self._logger.error(f"Data export failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_export_data(self, session_data: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Prepare data for export based on agent type."""
        export_data = {
            "session_info": {
                "session_id": session_data["session_id"],
                "workflow_id": session_data["workflow_id"],
                "agent_type": agent_type,
                "export_timestamp": datetime.utcnow().isoformat(),
                "pause_reason": f"Manual intervention requested for {agent_type}"
            },
            "context_data": session_data["context_data"],
            "intervention_data": session_data["intervention_data"]
        }

        # Add agent-specific data preparation
        if agent_type == "project_recommendation_agent":
            export_data.update(self._prepare_recommendation_data(session_data))
        elif agent_type == "question_analysis_agent":
            export_data.update(self._prepare_question_data(session_data))
        elif agent_type == "research_matching_agent":
            export_data.update(self._prepare_research_data(session_data))

        return export_data

    def _prepare_recommendation_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare project recommendation specific data."""
        context = session_data.get("context_data", {})
        intervention = session_data.get("intervention_data", {})

        return {
            "recommendation_context": {
                "user_query": context.get("query", ""),
                "selected_topics": context.get("topics", []),
                "user_id": context.get("user_id"),
                "max_recommendations": context.get("max_recommendations", 5)
            },
            "available_projects": intervention.get("available_projects", []),
            "current_ai_analysis": intervention.get("analysis_results", {}),
            "matching_criteria": {
                "semantic_similarity_threshold": 0.7,
                "topic_overlap_weight": 0.4,
                "difficulty_alignment_weight": 0.3,
                "user_preference_weight": 0.3
            }
        }

    def _prepare_question_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare question analysis specific data."""
        intervention = session_data.get("intervention_data", {})

        return {
            "question_details": {
                "title": intervention.get("title", ""),
                "content": intervention.get("content", ""),
                "source": intervention.get("source", ""),
                "tags": intervention.get("tags", [])
            },
            "current_ai_analysis": {
                "difficulty": intervention.get("difficulty", {}),
                "topics": intervention.get("topics", {}),
                "quality": intervention.get("quality", {})
            },
            "analysis_criteria": {
                "difficulty_factors": ["algorithm_complexity", "data_structure_usage", "edge_cases"],
                "topic_detection": "keyword_and_context_analysis",
                "quality_metrics": ["clarity", "completeness", "educational_value"]
            }
        }

    def _prepare_research_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare research matching specific data."""
        context = session_data.get("context_data", {})
        intervention = session_data.get("intervention_data", {})

        return {
            "research_context": {
                "target_project": context.get("project_id", ""),
                "research_focus": context.get("topics", []),
                "max_matches": context.get("max_matches", 5)
            },
            "available_papers": intervention.get("research_papers", []),
            "matching_criteria": {
                "algorithm_similarity_weight": 0.5,
                "topic_alignment_weight": 0.3,
                "implementation_relevance_weight": 0.2
            }
        }

    def _generate_prompt_content(self, export_data: Dict[str, Any], agent_type: str) -> str:
        """Generate prompt content for manual processing."""
        template = self._config.get_prompt_template(agent_type)

        # Fill template with data
        replacements = {
            "user_query": export_data.get("recommendation_context", {}).get("user_query", ""),
            "topics": ", ".join(export_data.get("recommendation_context", {}).get("selected_topics", [])),
            "project_count": len(export_data.get("available_projects", [])),
            "analysis_data": self._format_analysis_data(export_data),
            "ai_recommendations": self._format_ai_recommendations(export_data),
            "question_title": export_data.get("question_details", {}).get("title", ""),
            "question_content": export_data.get("question_details", {}).get("content", ""),
            "source": export_data.get("question_details", {}).get("source", ""),
            "ai_difficulty": export_data.get("current_ai_analysis", {}).get("difficulty", {}),
            "ai_topics": export_data.get("current_ai_analysis", {}).get("topics", {}),
            "ai_quality_score": export_data.get("current_ai_analysis", {}).get("quality", {})
        }

        prompt = template
        for key, value in replacements.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))

        return prompt

    def _format_analysis_data(self, export_data: Dict[str, Any]) -> str:
        """Format analysis data for prompt."""
        analysis = export_data.get("current_ai_analysis", {})
        if not analysis:
            return "No AI analysis available yet."

        formatted = []
        for key, value in analysis.items():
            formatted.append(f"- {key}: {value}")

        return "\n".join(formatted)

    def _format_ai_recommendations(self, export_data: Dict[str, Any]) -> str:
        """Format AI recommendations for prompt."""
        projects = export_data.get("available_projects", [])
        if not projects:
            return "No projects available for recommendation."

        formatted = []
        for i, project in enumerate(projects[:5], 1):  # Show top 5
            formatted.append(f"{i}. {project.get('title', 'Unknown')} - {project.get('description', '')[:100]}...")

        return "\n".join(formatted)

    def _generate_all_prompts(self, export_data: Dict[str, Any], agent_type: str, session_id: str) -> Dict[str, str]:
        """Generate different types of prompts for various use cases."""
        base_prompt = self._generate_prompt_content(export_data, agent_type)

        return {
            "human_readable": base_prompt,
            "structured": self._generate_structured_prompt(export_data, agent_type, session_id),
            "llm_friendly": self._generate_llm_friendly_prompt(export_data, agent_type)
        }

    def _generate_structured_prompt(self, export_data: Dict[str, Any], agent_type: str, session_id: str) -> Dict[str, Any]:
        """Generate structured prompt for external LLM processing."""
        if agent_type == "project_recommendation_agent":
            return {
                "task": "project_recommendation",
                "session_id": session_id,
                "context": {
                    "user_query": export_data.get("recommendation_context", {}).get("user_query", ""),
                    "selected_topics": export_data.get("recommendation_context", {}).get("selected_topics", []),
                    "available_projects_count": len(export_data.get("available_projects", []))
                },
                "data": {
                    "projects": export_data.get("available_projects", [])[:10],  # Limit for LLM
                    "analysis": export_data.get("current_ai_analysis", {})
                },
                "instructions": [
                    "Analyze the user's query and selected topics",
                    "Review available projects for relevance",
                    "Create 3-5 personalized project recommendations",
                    "Each recommendation must include: project_id, title, confidence_score, reasoning, key_topics, estimated_complexity",
                    "Focus on educational value and practical application",
                    "Consider the user's skill level and learning goals"
                ],
                "output_format": {
                    "recommendations": [
                        {
                            "project_id": "string",
                            "title": "string",
                            "confidence_score": "0.0-1.0",
                            "reasoning": "string",
                            "key_topics": ["string"],
                            "estimated_complexity": "beginner|intermediate|advanced",
                            "learning_objectives": ["string"]
                        }
                    ],
                    "metadata": {
                        "reviewer": "string",
                        "timestamp": "ISO string",
                        "quality_score": "0.0-1.0"
                    }
                }
            }
        return {"error": f"Unsupported agent type: {agent_type}"}

    def _generate_llm_friendly_prompt(self, export_data: Dict[str, Any], agent_type: str) -> str:
        """Generate LLM-friendly prompt for direct API usage."""
        if agent_type == "project_recommendation_agent":
            context = export_data.get("recommendation_context", {})
            projects = export_data.get("available_projects", [])

            prompt = f"""You are an expert software engineering educator. A user wants to learn through building projects.

USER QUERY: {context.get('user_query', '')}
SELECTED TOPICS: {', '.join(context.get('selected_topics', []))}
AVAILABLE PROJECTS: {len(projects)}

TASK: Recommend 3-5 projects that best match the user's learning goals.

REQUIREMENTS:
1. Focus on practical, buildable projects
2. Match the selected DSA topics
3. Consider progressive difficulty
4. Include clear learning objectives
5. Provide implementation guidance

Return ONLY valid JSON matching this format:
{{
  "recommendations": [
    {{
      "project_id": "unique_id",
      "title": "Project Title",
      "confidence_score": 0.95,
      "reasoning": "Why this project matches their goals",
      "key_topics": ["topic1", "topic2"],
      "estimated_complexity": "intermediate",
      "learning_objectives": ["Learn X", "Master Y"]
    }}
  ]
}}
"""
            return prompt

        return f"Unsupported agent type: {agent_type}"

    async def _write_structured_prompt(self, file_path: Path, prompt_data: Dict[str, Any]) -> None:
        """Write structured prompt data."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)

    async def _create_status_file(self, status_file: Path, session_data: Dict[str, Any], files_created: Dict[str, str]) -> None:
        """Create status file for tracking intervention progress."""
        status_data = {
            "session_id": session_data["session_id"],
            "status": "waiting_for_manual_input",
            "created_at": session_data.get("created_at", ""),
            "agent_type": session_data.get("agent_type", ""),
            "files_created": files_created,
            "expected_output_file": files_created.get("template_file", "").replace("output_template.json", "manual_recommendations.json"),
            "last_updated": session_data.get("created_at", ""),
            "progress": {
                "data_exported": True,
                "prompts_generated": True,
                "instructions_provided": True,
                "manual_work_pending": True,
                "validation_pending": True
            },
            "quality_checks": {
                "format_validation": False,
                "content_quality": False,
                "expert_signature": False
            }
        }

        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)

    async def _create_output_template(self, template_file: Path, agent_type: str) -> None:
        """Create output template file."""
        if agent_type == "project_recommendation_agent":
            template = {
                "session_id": "will_be_filled_by_system",
                "recommendations": [
                    {
                        "project_id": "unique_project_identifier",
                        "title": "Descriptive Project Title",
                        "confidence_score": 0.95,
                        "reasoning": "Detailed explanation of why this project matches the user's goals and selected topics",
                        "key_topics": ["dynamic_programming", "sliding_window"],
                        "estimated_complexity": "intermediate",
                        "learning_objectives": [
                            "Master specific DSA techniques",
                            "Apply algorithms to real-world problems",
                            "Understand performance trade-offs"
                        ]
                    }
                ],
                "metadata": {
                    "manual_reviewer": "Your Name/Expert ID",
                    "review_timestamp": "2024-01-15T10:30:00Z",
                    "review_method": "manual_analysis/cursor/chatgpt/claude",
                    "quality_score": 0.95,
                    "additional_notes": "Any additional insights or recommendations"
                }
            }
        else:
            template = {"error": f"Template not available for agent type: {agent_type}"}

        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

    async def _create_instructions_file(self, instructions_file: Path, session_id: str, files_created: Dict[str, str]) -> None:
        """Create comprehensive instructions file."""
        instructions = f"""# Manual Intervention Instructions - Session {session_id}

## 🎯 Overview
The NoLeet system has paused to request expert human input for project recommendations.
This ensures superior quality recommendations compared to automated AI systems.

## 📂 Files in This Directory

### Input Files:
- `data.json` - Raw data requiring analysis
- `prompt.md` - Human-readable analysis instructions
- `llm_prompt.json` - Structured prompt for external LLMs
- `output_template.json` - Template for your response format

### Output Files (Create These):
- `manual_recommendations.json` - Your expert recommendations (REQUIRED)
- `review_notes.md` - Optional detailed analysis notes

### Status Files:
- `status.json` - Tracks intervention progress
- `INSTRUCTIONS.md` - This file

## 🔄 Workflow Steps

### 1. Review the Data
```bash
# Read the input data
cat data.json

# Review the human-readable prompt
cat prompt.md
```

### 2. Process with External Tools (Choose One)

#### Option A: Cursor/VSCode
```bash
# Open the LLM prompt in Cursor
cursor llm_prompt.json
# Or open the markdown prompt
cursor prompt.md
```

#### Option B: ChatGPT/Claude
```bash
# Copy the content of llm_prompt.json
# Paste into ChatGPT/Claude
# Get AI-assisted recommendations
# Then apply your expert judgment
```

#### Option C: Manual Analysis
```bash
# Review data.json manually
# Apply your domain expertise
# Create recommendations based on user needs
```

### 3. Create Your Response
```bash
# Copy output_template.json to create your response
cp output_template.json manual_recommendations.json

# Edit manual_recommendations.json with your expert recommendations
# Ensure it follows the exact JSON format
```

### 4. Quality Validation
Before saving, ensure your recommendations:
- ✅ Match the user's query and selected topics
- ✅ Include 3-5 high-quality project suggestions
- ✅ Have confidence scores between 0.0-1.0
- ✅ Include detailed reasoning for each recommendation
- ✅ Consider the user's learning goals and skill level

## 📋 Response Format Requirements

Your `manual_recommendations.json` must contain:

```json
{{
  "session_id": "{session_id}",
  "recommendations": [
    {{
      "project_id": "unique_identifier",
      "title": "Descriptive Title",
      "confidence_score": 0.95,
      "reasoning": "Detailed explanation of why this project matches the user's goals and selected topics",
      "key_topics": ["dynamic_programming", "sliding_window"],
      "estimated_complexity": "intermediate",
      "learning_objectives": [
        "Master specific DSA techniques",
        "Apply algorithms to real-world problems",
        "Understand performance trade-offs"
      ]
    }}
  ],
  "metadata": {{
    "manual_reviewer": "Your Name",
    "review_timestamp": "2024-01-15T10:30:00Z",
    "review_method": "manual_analysis/cursor/chatgpt/claude",
    "quality_score": 0.95
  }}
}}
```

## ⚡ Automatic Processing

Once you save `manual_recommendations.json`:
- ✅ System automatically detects the file
- ✅ Validates the JSON format
- ✅ Checks quality requirements
- ✅ Resumes the workflow
- ✅ Delivers recommendations to user

## 🚨 Important Notes

- **File Location**: Save `manual_recommendations.json` in this directory
- **File Name**: Must be exactly `manual_recommendations.json`
- **Format**: Valid JSON only
- **Quality**: System will validate your recommendations
- **Timeout**: Complete within 1 hour to avoid automatic cancellation

## 🆘 Troubleshooting

### File Not Detected
- Ensure file is named exactly `manual_recommendations.json`
- Check JSON syntax with: `python -m json.tool manual_recommendations.json`

### Validation Errors
- Check the status.json file for specific error messages
- Ensure all required fields are present
- Verify confidence scores are between 0.0-1.0

### Need Help
- Review the prompt.md file for detailed instructions
- Check output_template.json for exact format requirements
- Contact system administrator if issues persist

## 🎉 Success Criteria

✅ File `manual_recommendations.json` exists and is valid JSON
✅ Contains 3-5 project recommendations
✅ All recommendations have required fields
✅ Confidence scores are realistic (0.7-1.0 for good recommendations)
✅ Reasoning is detailed and educational
✅ Metadata includes reviewer information

Once complete, the system will automatically continue and deliver your expert recommendations to the user!

---
*Generated by NoLeet Manual Intervention System*
*Session: {session_id}*
"""

        with open(instructions_file, "w", encoding="utf-8") as f:
            f.write(instructions)

    async def _send_export_notifications(self, session_data: Dict[str, Any], files_created: Dict[str, str]) -> None:
        """Send notifications about export completion."""
        session_id = session_data["session_id"]

        if self._config.desktop_notifications:
            try:
                # Try different notification methods
                notification_msg = f"NoLeet: Manual intervention required for session {session_id}"

                # macOS notification
                import subprocess
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{notification_msg}" with title "NoLeet Intervention"'
                ], capture_output=True)

            except Exception as e:
                self._logger.debug(f"Desktop notification failed: {e}")

    async def _write_data_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write data to file in specified format."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if self._config.export_format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif self._config.export_format == "yaml":
            if HAS_YAML and yaml:
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            else:
                # Fallback to JSON if yaml not available
                self._logger.warning("PyYAML not available, falling back to JSON")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # Default to JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    async def _write_prompt_file(self, file_path: Path, content: str) -> None:
        """Write prompt content to markdown file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    async def _create_backup(self, original_file: Path, timestamp: str) -> None:
        """Create backup of export file."""
        try:
            backup_dir = self._config.export_directory / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_file = backup_dir / f"{original_file.stem}_backup_{timestamp.replace(':', '-')}{original_file.suffix}"

            import shutil
            shutil.copy2(original_file, backup_file)

            # Clean old backups
            self._cleanup_old_backups(backup_dir)

        except Exception as e:
            self._logger.error(f"Backup creation failed: {e}")

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Clean up old backup files."""
        try:
            backup_files = list(backup_dir.glob("*.json")) + list(backup_dir.glob("*.yaml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the most recent backups
            if len(backup_files) > self._config.max_backup_versions:
                for old_file in backup_files[self._config.max_backup_versions:]:
                    old_file.unlink()
                    self._logger.debug(f"Cleaned up old backup: {old_file}")

        except Exception as e:
            self._logger.error(f"Backup cleanup failed: {e}")

    def get_export_history(self) -> list[Path]:
        """Get list of recent export files."""
        try:
            export_files = []
            for pattern in ["*.json", "*.yaml", "*.md"]:
                export_files.extend(self._config.export_directory.glob(pattern))

            # Sort by modification time (newest first)
            export_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            return export_files[:20]  # Return last 20 files

        except Exception as e:
            self._logger.error(f"Failed to get export history: {e}")
            return []
