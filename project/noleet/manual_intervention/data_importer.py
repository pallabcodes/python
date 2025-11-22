"""Data importer for manual intervention results."""

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


class DataImporter:
    """Imports manually processed data back into the workflow."""

    def __init__(self, config: InterventionConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize data importer.

        Args:
            config: Intervention configuration
            logger: Optional logger instance
        """
        self._config = config
        self._logger = logger or logging.getLogger(__name__)

        # Track file modification times to detect changes
        self._file_timestamps: Dict[Path, float] = {}

    async def check_for_manual_input(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if manual input file is available for a session.

        Args:
            session_data: Intervention session data

        Returns:
            Availability status and file path if found
        """
        try:
            export_path = Path(session_data.get("export_path", ""))
            if not export_path.exists():
                return {"available": False, "reason": "export_path_not_found"}

            # Look for manual input files in the same directory
            export_dir = export_path.parent
            manual_pattern = self._config.get_resume_pattern()

            for file_path in export_dir.glob(manual_pattern):
                # Check if file has been modified since last check
                current_mtime = file_path.stat().st_mtime
                last_mtime = self._file_timestamps.get(file_path, 0)

                if current_mtime > last_mtime:
                    self._file_timestamps[file_path] = current_mtime
                    return {
                        "available": True,
                        "file_path": str(file_path),
                        "last_modified": datetime.fromtimestamp(current_mtime).isoformat()
                    }

            return {"available": False, "reason": "no_matching_file"}

        except Exception as e:
            self._logger.error(f"Manual input check failed: {e}")
            return {"available": False, "reason": "check_failed", "error": str(e)}

    async def import_manual_data(self, file_path: str) -> Dict[str, Any]:
        """
        Import manually created data from file.

        Args:
            file_path: Path to manual input file

        Returns:
            Import result with parsed data
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": "file_not_found"}

            # Determine file format and parse
            if path.suffix.lower() == ".json":
                data = await self._parse_json_file(path)
            elif path.suffix.lower() in [".yaml", ".yml"]:
                if HAS_YAML and yaml:
                    data = await self._parse_yaml_file(path)
                else:
                    return {"success": False, "error": "YAML format requires PyYAML library"}
            else:
                return {"success": False, "error": f"unsupported_format: {path.suffix}"}

            # Validate the imported data
            validation_result = self._validate_manual_data(data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "validation_failed",
                    "validation_errors": validation_result["errors"]
                }

            # Process and normalize the data
            processed_data = self._process_manual_data(data)

            self._logger.info(f"Successfully imported manual data from {file_path}")

            return {
                "success": True,
                "data": processed_data,
                "file_path": str(file_path),
                "import_timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self._logger.error(f"Manual data import failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def _parse_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse YAML file."""
        if not HAS_YAML or not yaml:
            raise ValueError("YAML support not available. Install PyYAML to use YAML files.")

        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _validate_manual_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of manually created data with quality checks.

        Args:
            data: Parsed manual data

        Returns:
            Detailed validation result
        """
        errors = []
        warnings = []
        quality_score = 0.0

        # Check for required top-level keys
        if "recommendations" not in data and "analysis" not in data:
            errors.append("Missing required key: 'recommendations' or 'analysis'")
            return {"valid": False, "errors": errors, "warnings": warnings, "quality_score": quality_score}

        # Validate recommendations structure if present
        if "recommendations" in data:
            recommendations = data["recommendations"]
            if not isinstance(recommendations, list):
                errors.append("'recommendations' must be a list")
            else:
                if len(recommendations) < 3:
                    warnings.append("Consider providing at least 3 recommendations for better coverage")
                elif len(recommendations) > 7:
                    warnings.append("Too many recommendations may overwhelm users")

                for i, rec in enumerate(recommendations):
                    if not isinstance(rec, dict):
                        errors.append(f"Recommendation {i} must be a dictionary")
                        continue

                    # Required fields validation
                    required_keys = ["project_id", "title", "confidence_score"]
                    for key in required_keys:
                        if key not in rec:
                            errors.append(f"Recommendation {i} missing required key: {key}")

                    # Confidence score validation
                    if "confidence_score" in rec:
                        score = rec["confidence_score"]
                        if not isinstance(score, (int, float)):
                            errors.append(f"Recommendation {i} confidence_score must be a number")
                        elif not (0.0 <= score <= 1.0):
                            errors.append(f"Recommendation {i} confidence_score must be between 0.0 and 1.0")
                        elif score < 0.6:
                            warnings.append(f"Recommendation {i} has low confidence score ({score})")

                    # Reasoning quality check
                    if "reasoning" in rec:
                        reasoning = rec["reasoning"]
                        if len(str(reasoning)) < 50:
                            warnings.append(f"Recommendation {i} reasoning is too brief")
                        elif len(str(reasoning)) > 500:
                            warnings.append(f"Recommendation {i} reasoning is too long")
                        quality_score += 0.3  # Good reasoning adds quality points
                    else:
                        errors.append(f"Recommendation {i} missing reasoning")

                    # Topics validation
                    if "key_topics" in rec:
                        topics = rec["key_topics"]
                        if not isinstance(topics, list) or len(topics) == 0:
                            warnings.append(f"Recommendation {i} should have key topics")
                        elif len(topics) > 5:
                            warnings.append(f"Recommendation {i} has too many topics")
                    else:
                        warnings.append(f"Recommendation {i} missing key_topics")

                    # Complexity validation
                    if "estimated_complexity" in rec:
                        complexity = str(rec["estimated_complexity"]).lower()
                        valid_levels = ["beginner", "intermediate", "advanced"]
                        if complexity not in valid_levels:
                            warnings.append(f"Recommendation {i} complexity should be one of: {valid_levels}")
                    else:
                        warnings.append(f"Recommendation {i} missing estimated_complexity")

                    # Learning objectives validation
                    if "learning_objectives" in rec:
                        objectives = rec["learning_objectives"]
                        if not isinstance(objectives, list) or len(objectives) == 0:
                            warnings.append(f"Recommendation {i} should have learning objectives")
                        elif len(objectives) > 5:
                            warnings.append(f"Recommendation {i} has too many learning objectives")
                    else:
                        warnings.append(f"Recommendation {i} missing learning_objectives")

        # Validate metadata if present
        if "metadata" in data:
            metadata = data["metadata"]
            if not isinstance(metadata, dict):
                errors.append("'metadata' must be a dictionary")
            else:
                # Check for reviewer information
                if "manual_reviewer" not in metadata:
                    if self._config.require_expert_signature:
                        errors.append("Metadata missing required 'manual_reviewer' field")
                    else:
                        warnings.append("Consider adding reviewer information in metadata")

                # Check timestamp
                if "review_timestamp" not in metadata:
                    warnings.append("Consider adding review timestamp in metadata")

                # Quality score in metadata
                if "quality_score" in metadata:
                    meta_quality = metadata["quality_score"]
                    if isinstance(meta_quality, (int, float)) and 0.0 <= meta_quality <= 1.0:
                        quality_score = max(quality_score, meta_quality)  # Use higher quality score
                    else:
                        warnings.append("Metadata quality_score should be between 0.0 and 1.0")
        else:
            if self._config.require_expert_signature:
                errors.append("Missing required metadata with reviewer information")
            warnings.append("Consider adding metadata with reviewer information")

        # Calculate overall quality score
        if len(errors) == 0:
            base_quality = 1.0
            # Deduct for warnings (minor issues)
            warning_penalty = len(warnings) * 0.05
            quality_score = max(0.0, base_quality - warning_penalty)

            # Ensure meets minimum threshold
            if self._config.validate_manual_input and quality_score < self._config.quality_score_threshold:
                errors.append(f"Quality score {quality_score:.2f} below threshold {self._config.quality_score_threshold}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": quality_score,
            "recommendation_count": len(data.get("recommendations", [])) if "recommendations" in data else 0
        }

    def _process_manual_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and normalize manual data.

        Args:
            data: Raw manual data

        Returns:
            Processed and normalized data
        """
        processed = {
            "manual_input": True,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "raw_data": data
        }

        # Process recommendations
        if "recommendations" in data:
            processed["recommendations"] = self._process_recommendations(data["recommendations"])

        # Process analysis results
        if "analysis" in data:
            processed["analysis"] = self._normalize_analysis(data["analysis"])

        # Extract metadata
        if "metadata" in data:
            processed["metadata"] = data["metadata"]
        else:
            processed["metadata"] = {
                "source": "manual_intervention",
                "created_at": processed["processing_timestamp"]
            }

        return processed

    def _process_recommendations(self, recommendations: list) -> list:
        """Process and normalize recommendations."""
        processed_recs = []

        for rec in recommendations:
            processed_rec = {
                "project_id": rec.get("project_id", ""),
                "title": rec.get("title", ""),
                "confidence_score": float(rec.get("confidence_score", 0.0)),
                "reasoning": rec.get("reasoning", ""),
                "key_topics": rec.get("key_topics", []),
                "estimated_complexity": rec.get("estimated_complexity", "medium"),
                "learning_objectives": rec.get("learning_objectives", []),
                "manual_override": True
            }

            # Normalize complexity
            complexity = processed_rec["estimated_complexity"].lower()
            if complexity not in ["beginner", "intermediate", "advanced"]:
                if complexity in ["easy", "simple"]:
                    processed_rec["estimated_complexity"] = "beginner"
                elif complexity in ["hard", "expert"]:
                    processed_rec["estimated_complexity"] = "advanced"
                else:
                    processed_rec["estimated_complexity"] = "intermediate"

            processed_recs.append(processed_rec)

        # Sort by confidence score (highest first)
        processed_recs.sort(key=lambda x: x["confidence_score"], reverse=True)

        return processed_recs

    def _normalize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize analysis results."""
        normalized = {}

        # Normalize difficulty
        if "difficulty" in analysis:
            diff = analysis["difficulty"]
            if isinstance(diff, dict):
                normalized["difficulty"] = {
                    "level": diff.get("level", "medium").lower(),
                    "confidence": float(diff.get("confidence", 0.5)),
                    "reasoning": diff.get("reasoning", "")
                }
            else:
                # Handle string difficulty
                level = str(diff).lower()
                normalized["difficulty"] = {
                    "level": level if level in ["easy", "medium", "hard"] else "medium",
                    "confidence": 0.8,
                    "reasoning": "Manually specified"
                }

        # Normalize topics
        if "topics" in analysis:
            topics = analysis["topics"]
            if isinstance(topics, list):
                normalized["topics"] = topics
            else:
                normalized["topics"] = [str(topics)]

        # Normalize quality
        if "quality_assessment" in analysis:
            quality = analysis["quality_assessment"]
            if isinstance(quality, dict):
                normalized["quality"] = {
                    "overall_score": float(quality.get("overall_score", 0.5)),
                    "strengths": quality.get("strengths", []),
                    "weaknesses": quality.get("weaknesses", []),
                    "improvement_suggestions": quality.get("improvement_suggestions", [])
                }

        return normalized

    def get_import_history(self) -> list[Dict[str, Any]]:
        """Get history of imported files."""
        try:
            # This would track imported files in a more sophisticated system
            # For now, return basic info about tracked files
            history = []
            for file_path, timestamp in self._file_timestamps.items():
                history.append({
                    "file_path": str(file_path),
                    "last_imported": datetime.fromtimestamp(timestamp).isoformat(),
                    "size_bytes": file_path.stat().st_size if file_path.exists() else 0
                })

            # Sort by most recent first
            history.sort(key=lambda x: x["last_imported"], reverse=True)
            return history[:20]  # Return last 20 imports

        except Exception as e:
            self._logger.error(f"Failed to get import history: {e}")
            return []

    def validate_file_format(self, file_path: str) -> Dict[str, Any]:
        """
        Validate that a file can be parsed correctly.

        Args:
            file_path: Path to file to validate

        Returns:
            Validation result
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"valid": False, "error": "file_not_found"}

            # Try to parse the file
            if path.suffix.lower() == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            elif path.suffix.lower() in [".yaml", ".yml"]:
                if HAS_YAML and yaml:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                else:
                    return {"valid": False, "error": "YAML format requires PyYAML library"}
            else:
                return {"valid": False, "error": f"unsupported_format: {path.suffix}"}

            # Validate the data structure
            validation = self._validate_manual_data(data)

            return {
                "valid": validation["valid"],
                "errors": validation["errors"],
                "data_preview": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
            }

        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"invalid_json: {e}"}
        except yaml.YAMLError as e:
            return {"valid": False, "error": f"invalid_yaml: {e}"}
        except Exception as e:
            return {"valid": False, "error": f"parse_error: {e}"}
