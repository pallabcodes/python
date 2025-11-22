"""Manual intervention manager for human-AI collaboration workflows."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
import time
import hashlib

from .intervention_config import InterventionConfig
from .data_exporter import DataExporter
from .data_importer import DataImporter


class ManualInterventionManager:
    """Manages manual intervention workflows with pause/resume capabilities."""

    def __init__(
        self,
        config: Optional[InterventionConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize manual intervention manager.

        Args:
            config: Intervention configuration
            logger: Optional logger instance
        """
        self._config = config or InterventionConfig()
        self._logger = logger or logging.getLogger(__name__)

        self._exporter = DataExporter(self._config)
        self._importer = DataImporter(self._config)

        # State tracking
        self._active_interventions: Dict[str, Dict[str, Any]] = {}
        self._intervention_history: List[Dict[str, Any]] = []

        # Callbacks
        self._on_pause_callbacks: List[Callable] = []
        self._on_resume_callbacks: List[Callable] = []

        self._logger.info("Manual intervention manager initialized")

    def add_pause_callback(self, callback: Callable) -> None:
        """Add callback to be called when intervention pauses."""
        self._on_pause_callbacks.append(callback)

    def add_resume_callback(self, callback: Callable) -> None:
        """Add callback to be called when intervention resumes."""
        self._on_resume_callbacks.append(callback)

    async def pause_for_manual_intervention(
        self,
        workflow_id: str,
        agent_type: str,
        context_data: Dict[str, Any],
        intervention_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pause workflow and prepare for manual intervention.

        Args:
            workflow_id: Unique workflow identifier
            agent_type: Type of agent requesting intervention
            context_data: Workflow context data
            intervention_data: Data to be manually processed

        Returns:
            Intervention session information
        """
        if not self._config.should_intervene_at(agent_type):
            self._logger.info(f"Manual intervention disabled for {agent_type}")
            return {"action": "continue", "reason": "intervention_disabled"}

        # Create intervention session
        session_id = self._create_session_id(workflow_id, agent_type)
        timestamp = datetime.utcnow().isoformat()

        session_data = {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "agent_type": agent_type,
            "status": "paused",
            "created_at": timestamp,
            "context_data": context_data,
            "intervention_data": intervention_data,
            "export_path": None,
            "resume_path": None,
            "last_check": timestamp
        }

        # Export data for manual processing
        export_result = await self._exporter.export_for_intervention(
            session_data, agent_type, timestamp
        )

        if export_result["success"]:
            session_data["export_path"] = export_result["export_path"]
            session_data["prompt_content"] = export_result.get("prompt_content", "")

            # Store session
            self._active_interventions[session_id] = session_data

            # Trigger pause callbacks
            await self._trigger_pause_callbacks(session_data)

            # Send notification if configured
            self._send_pause_notification(session_data)

            self._logger.info(f"Workflow {workflow_id} paused for manual intervention at {agent_type}")

            return {
                "action": "paused",
                "session_id": session_id,
                "export_path": session_data["export_path"],
                "message": f"Workflow paused for manual intervention. Data exported to {session_data['export_path']}"
            }
        else:
            self._logger.error(f"Failed to export intervention data: {export_result.get('error')}")
            return {
                "action": "continue",
                "reason": "export_failed",
                "error": export_result.get("error")
            }

    async def check_for_resume(self, session_id: str) -> Dict[str, Any]:
        """
        Check if manual intervention session can be resumed.

        Args:
            session_id: Intervention session ID

        Returns:
            Resume status and data
        """
        if session_id not in self._active_interventions:
            return {"can_resume": False, "reason": "session_not_found"}

        session_data = self._active_interventions[session_id]

        # Check timeout
        created_at = datetime.fromisoformat(session_data["created_at"])
        if datetime.utcnow() - created_at > timedelta(seconds=self._config.max_wait_time_seconds):
            session_data["status"] = "timeout"
            self._logger.warning(f"Intervention session {session_id} timed out")
            return {"can_resume": False, "reason": "timeout"}

        # Check for manual input file
        resume_data = await self._importer.check_for_manual_input(session_data)

        if resume_data["available"]:
            # Import the manual data
            import_result = await self._importer.import_manual_data(resume_data["file_path"])

            if import_result["success"]:
                session_data["status"] = "resumed"
                session_data["resume_path"] = resume_data["file_path"]
                session_data["manual_data"] = import_result["data"]
                session_data["resumed_at"] = datetime.utcnow().isoformat()

                # Move to history
                self._intervention_history.append(session_data)
                del self._active_interventions[session_id]

                # Trigger resume callbacks
                await self._trigger_resume_callbacks(session_data)

                self._logger.info(f"Intervention session {session_id} resumed with manual data")

                return {
                    "can_resume": True,
                    "manual_data": import_result["data"],
                    "session_data": session_data
                }
            else:
                self._logger.error(f"Failed to import manual data: {import_result.get('error')}")
                return {"can_resume": False, "reason": "import_failed", "error": import_result.get("error")}

        return {"can_resume": False, "reason": "waiting_for_input"}

    async def wait_for_manual_intervention(
        self,
        session_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Wait for manual intervention to complete.

        Args:
            session_id: Intervention session ID
            progress_callback: Optional callback for progress updates

        Returns:
            Resume data when intervention completes
        """
        self._logger.info(f"Waiting for manual intervention on session {session_id}")

        start_time = time.time()

        while True:
            # Check for resume
            resume_result = await self.check_for_resume(session_id)

            if resume_result["can_resume"]:
                return resume_result

            if resume_result["reason"] in ["timeout", "session_not_found"]:
                return resume_result

            # Progress callback
            if progress_callback:
                elapsed = time.time() - start_time
                progress = min(1.0, elapsed / self._config.max_wait_time_seconds)
                await progress_callback(progress, f"Waiting for manual input... ({elapsed:.0f}s elapsed)")

            # Wait before next check
            await asyncio.sleep(self._config.polling_interval_seconds)

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active intervention sessions."""
        return self._active_interventions.copy()

    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get intervention session history."""
        return self._intervention_history[-limit:]

    def cancel_session(self, session_id: str) -> bool:
        """
        Cancel an active intervention session.

        Args:
            session_id: Session to cancel

        Returns:
            True if cancelled successfully
        """
        if session_id in self._active_interventions:
            session_data = self._active_interventions[session_id]
            session_data["status"] = "cancelled"
            session_data["cancelled_at"] = datetime.utcnow().isoformat()

            # Move to history
            self._intervention_history.append(session_data)
            del self._active_interventions[session_id]

            self._logger.info(f"Intervention session {session_id} cancelled")
            return True

        return False

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific session."""
        if session_id in self._active_interventions:
            return self._active_interventions[session_id].copy()

        # Check history
        for session in self._intervention_history:
            if session["session_id"] == session_id:
                return session.copy()

        return None

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old completed sessions.

        Args:
            max_age_hours: Maximum age in hours for cleanup

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0

        # Clean history
        new_history = []
        for session in self._intervention_history:
            session_time = datetime.fromisoformat(session.get("created_at", session.get("resumed_at", "")))
            if session_time > cutoff_time:
                new_history.append(session)
            else:
                cleaned_count += 1

        self._intervention_history = new_history

        # Clean export files
        if self._config.create_backups:
            self._cleanup_export_files(max_age_hours)

        self._logger.info(f"Cleaned up {cleaned_count} old intervention sessions")
        return cleaned_count

    def _create_session_id(self, workflow_id: str, agent_type: str) -> str:
        """Create unique session ID."""
        timestamp = datetime.utcnow().isoformat()
        content = f"{workflow_id}_{agent_type}_{timestamp}"
        hash_obj = hashlib.md5(content.encode())
        return f"intervention_{hash_obj.hexdigest()[:8]}"

    async def _trigger_pause_callbacks(self, session_data: Dict[str, Any]) -> None:
        """Trigger pause callbacks."""
        for callback in self._on_pause_callbacks:
            try:
                await callback(session_data)
            except Exception as e:
                self._logger.error(f"Pause callback failed: {e}")

    async def _trigger_resume_callbacks(self, session_data: Dict[str, Any]) -> None:
        """Trigger resume callbacks."""
        for callback in self._on_resume_callbacks:
            try:
                await callback(session_data)
            except Exception as e:
                self._logger.error(f"Resume callback failed: {e}")

    def _send_pause_notification(self, session_data: Dict[str, Any]) -> None:
        """Send notification about paused intervention."""
        if not self._config.notify_on_pause or not self._config.notification_command:
            return

        try:
            import subprocess
            message = f"NoLeet: Manual intervention required for {session_data['agent_type']}"
            cmd = self._config.notification_command.replace("{message}", message)
            subprocess.run(cmd, shell=True, capture_output=True)
        except Exception as e:
            self._logger.error(f"Notification failed: {e}")

    def _cleanup_export_files(self, max_age_hours: int) -> None:
        """Cleanup old export files."""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)

            for file_path in self._config.export_directory.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    self._logger.debug(f"Cleaned up old export file: {file_path}")

        except Exception as e:
            self._logger.error(f"Export file cleanup failed: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get intervention statistics."""
        total_sessions = len(self._intervention_history) + len(self._active_interventions)

        completed_sessions = [s for s in self._intervention_history if s.get("status") == "resumed"]
        avg_completion_time = 0

        if completed_sessions:
            completion_times = []
            for session in completed_sessions:
                if "resumed_at" in session and "created_at" in session:
                    created = datetime.fromisoformat(session["created_at"])
                    resumed = datetime.fromisoformat(session["resumed_at"])
                    completion_times.append((resumed - created).total_seconds())

            if completion_times:
                avg_completion_time = sum(completion_times) / len(completion_times)

        return {
            "total_sessions": total_sessions,
            "active_sessions": len(self._active_interventions),
            "completed_sessions": len(completed_sessions),
            "cancelled_sessions": len([s for s in self._intervention_history if s.get("status") == "cancelled"]),
            "timed_out_sessions": len([s for s in self._intervention_history if s.get("status") == "timeout"]),
            "average_completion_time_seconds": avg_completion_time,
            "most_common_agent": self._get_most_common_agent()
        }

    def _get_most_common_agent(self) -> Optional[str]:
        """Get the most commonly intervened agent."""
        all_sessions = list(self._intervention_history) + list(self._active_interventions.values())
        agent_counts = {}

        for session in all_sessions:
            agent = session.get("agent_type")
            if agent:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1

        if agent_counts:
            return max(agent_counts, key=agent_counts.get)

        return None
