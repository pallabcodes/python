"""
Manual Intervention System

Provides human-in-the-loop capabilities for AI workflows:
- Automatic quality assessment
- Structured data export for human review
- Expert intervention workflows
- Seamless result integration
- Quality assurance and audit trails
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from .config import InterventionConfig
from .types import GenerationRequest

@dataclass
class InterventionSession:
    """A manual intervention session."""
    session_id: str
    request: GenerationRequest
    export_path: Path
    status: str = "pending"  # pending, in_progress, completed, expired
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    expert_input: Optional[str] = None
    quality_score: Optional[float] = None

@dataclass
class InterventionResult:
    """Result from manual intervention."""
    content: str
    quality_score: float
    processing_time: float
    expert_feedback: Optional[str] = None
    metadata: Dict[str, Any] = None

class DataExporter:
    """Exports workflow data for manual intervention."""

    def __init__(self, config: InterventionConfig):
        self.config = config
        self.logger = logging.getLogger("DataExporter")

    async def export_for_intervention(
        self,
        session: InterventionSession
    ) -> Dict[str, Any]:
        """Export session data for manual review."""
        export_dir = session.export_path
        export_dir.mkdir(parents=True, exist_ok=True)

        # Export files
        files_created = {}

        # 1. Raw data export
        data_file = export_dir / "data.json"
        data_content = self._create_data_export(session)
        await self._write_json_file(data_file, data_content)
        files_created["data"] = str(data_file)

        # 2. Human-readable prompt
        prompt_file = export_dir / "EXPERT_PROMPT.md"
        prompt_content = self._create_human_prompt(session)
        await self._write_text_file(prompt_file, prompt_content)
        files_created["human_prompt"] = str(prompt_file)

        # 3. Structured LLM prompt
        structured_file = export_dir / "structured_prompt.json"
        structured_content = self._create_structured_prompt(session)
        await self._write_json_file(structured_file, structured_content)
        files_created["structured_prompt"] = str(structured_file)

        # 4. Instructions
        instructions_file = export_dir / "INSTRUCTIONS.md"
        instructions_content = self._create_instructions(session, files_created)
        await self._write_text_file(instructions_file, instructions_content)
        files_created["instructions"] = str(instructions_file)

        # 5. Status file
        status_file = export_dir / "STATUS.json"
        status_content = self._create_status_file(session)
        await self._write_json_file(status_file, status_content)
        files_created["status"] = str(status_file)

        self.logger.info(f"Exported intervention data to {export_dir}")
        return files_created

    def _create_data_export(self, session: InterventionSession) -> Dict[str, Any]:
        """Create raw data export."""
        return {
            "session_id": session.session_id,
            "timestamp": datetime.fromtimestamp(session.created_at).isoformat(),
            "request": {
                "prompt": session.request.prompt,
                "quality_requirement": session.request.quality_requirement,
                "max_tokens": session.request.max_tokens,
                "temperature": session.request.temperature,
                "context": session.request.context
            },
            "intervention_reason": "Quality threshold not met",
            "export_version": "1.0"
        }

    def _create_human_prompt(self, session: InterventionSession) -> str:
        """Create human-readable expert prompt."""
        prompt = f"""# Expert Review Required

**Session ID:** {session.session_id}
**Request Type:** {session.request.quality_requirement} quality
**Timestamp:** {datetime.fromtimestamp(session.created_at).isoformat()}

## Original Request
{session.request.prompt}

## Context
Quality requirement: {session.request.quality_requirement}
Max tokens: {session.request.max_tokens or 'Not specified'}
Temperature: {session.request.temperature or 'Not specified'}

## Your Task
Please provide a high-quality response to the above request. Consider:
- Technical accuracy and depth
- Clarity and readability
- Practical examples where appropriate
- Best practices and recommendations

## Response Format
Provide your expert response in the file: `expert_response.md`

## Quality Guidelines
- Ensure response meets or exceeds the quality requirement
- Include relevant examples or code snippets if applicable
- Consider edge cases and limitations
- Provide actionable insights

Thank you for your expertise!
"""
        return prompt

    def _create_structured_prompt(self, session: InterventionSession) -> Dict[str, Any]:
        """Create structured prompt for LLM processing."""
        return {
            "version": "1.0",
            "session_id": session.session_id,
            "task": "expert_response_generation",
            "input": {
                "prompt": session.request.prompt,
                "quality_requirement": session.request.quality_requirement,
                "constraints": {
                    "max_tokens": session.request.max_tokens,
                    "temperature": session.request.temperature
                },
                "context": session.request.context
            },
            "output_requirements": {
                "format": "markdown",
                "include_examples": True,
                "include_code": session.request.prompt.lower().find("code") >= 0,
                "quality_checks": [
                    "technical_accuracy",
                    "completeness",
                    "readability",
                    "practical_value"
                ]
            },
            "metadata": {
                "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                "intervention_reason": "quality_threshold_not_met"
            }
        }

    def _create_instructions(self, session: InterventionSession, files: Dict[str, str]) -> str:
        """Create comprehensive instructions."""
        instructions = f"""# Manual Intervention Instructions

## Session: {session.session_id}

### What Happened
The AI system determined that the automatic response did not meet quality standards and requires expert review.

### Your Files
- `data.json` - Raw request data
- `EXPERT_PROMPT.md` - Human-readable instructions
- `structured_prompt.json` - Structured data for LLM processing
- `STATUS.json` - Current session status

### What to Do
1. Review the request in `EXPERT_PROMPT.md`
2. Provide your expert response
3. Save your response as `expert_response.md` in this directory
4. Optionally, add quality feedback in `expert_feedback.md`

### Response Format
Your response should be in Markdown format. Include:
- Clear, accurate information
- Code examples if relevant
- Best practices and recommendations
- Practical insights

### Quality Standards
- Meet or exceed the requested quality level
- Provide actionable, valuable information
- Consider the user's context and needs
- Include examples and explanations

### Next Steps
Once you save `expert_response.md`, the system will automatically:
1. Import your response
2. Validate the quality
3. Deliver it to the user
4. Update the session status

Thank you for ensuring quality! 🎯
"""
        return instructions

    def _create_status_file(self, session: InterventionSession) -> Dict[str, Any]:
        """Create status tracking file."""
        return {
            "session_id": session.session_id,
            "status": session.status,
            "created_at": session.created_at,
            "last_updated": time.time(),
            "files_required": ["expert_response.md"],
            "files_optional": ["expert_feedback.md"],
            "timeout_seconds": self.config.expert_timeout,
            "quality_threshold": self.config.quality_threshold
        }

    async def _write_json_file(self, path: Path, content: Dict[str, Any]):
        """Write JSON file asynchronously."""
        import aiofiles
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(content, indent=2))

    async def _write_text_file(self, path: Path, content: str):
        """Write text file asynchronously."""
        import aiofiles
        async with aiofiles.open(path, 'w') as f:
            await f.write(content)

class DataImporter:
    """Imports manually processed intervention results."""

    def __init__(self, config: InterventionConfig):
        self.config = config
        self.logger = logging.getLogger("DataImporter")

    async def import_results(self, session: InterventionSession) -> InterventionResult:
        """Import expert results from intervention session."""
        export_dir = session.export_path

        # Check for required files
        response_file = export_dir / "expert_response.md"
        if not response_file.exists():
            raise Exception(f"Expert response file not found: {response_file}")

        # Read expert response
        content = await self._read_text_file(response_file)

        # Read optional feedback
        feedback_file = export_dir / "expert_feedback.md"
        feedback = None
        if feedback_file.exists():
            feedback = await self._read_text_file(feedback_file)

        # Assess quality
        quality_score = self._assess_quality(content, session)

        # Create result
        result = InterventionResult(
            content=content.strip(),
            quality_score=quality_score,
            processing_time=time.time() - session.created_at,
            expert_feedback=feedback,
            metadata={
                "session_id": session.session_id,
                "response_length": len(content),
                "has_feedback": feedback is not None
            }
        )

        self.logger.info(f"Imported intervention results for session {session.session_id}")
        return result

    async def _read_text_file(self, path: Path) -> str:
        """Read text file asynchronously."""
        import aiofiles
        async with aiofiles.open(path, 'r') as f:
            return await f.read()

    def _assess_quality(self, content: str, session: InterventionSession) -> float:
        """Assess the quality of expert response."""
        score = 0.0
        total_checks = 0

        # Length check (responses should be substantial)
        total_checks += 1
        if len(content) > 200:
            score += 1.0
        elif len(content) > 100:
            score += 0.7
        elif len(content) > 50:
            score += 0.4

        # Content quality checks
        content_lower = content.lower()

        # Technical depth (look for technical terms, explanations)
        total_checks += 1
        technical_indicators = ['example', 'code', 'function', 'class', 'algorithm']
        if any(indicator in content_lower for indicator in technical_indicators):
            score += 1.0
        elif len(content.split('.')) > 3:  # Multiple sentences
            score += 0.7

        # Structure check (headings, lists, formatting)
        total_checks += 1
        if any(line.startswith(('#', '-', '*', '1.')) for line in content.split('\n')):
            score += 1.0
        elif len(content.split('\n\n')) > 1:  # Multiple paragraphs
            score += 0.6

        # Relevance to quality requirement
        total_checks += 1
        quality_req = session.request.quality_requirement
        if quality_req == "premium" and len(content) > 300:
            score += 1.0
        elif quality_req == "high" and len(content) > 200:
            score += 0.9
        elif quality_req == "standard" and len(content) > 100:
            score += 0.8
        else:
            score += 0.6

        final_score = min(score / total_checks, 1.0)
        return round(final_score, 2)

class InterventionManager:
    """
    Manages manual intervention workflows.

    Provides:
    - Quality threshold monitoring
    - Automated session creation
    - Expert workflow management
    - Result validation and integration
    """

    def __init__(self, config: InterventionConfig):
        self.config = config
        self.logger = logging.getLogger("InterventionManager")

        self.exporter = DataExporter(config)
        self.importer = DataImporter(config)

        self.active_sessions: Dict[str, InterventionSession] = {}

        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def process_request(self, request: GenerationRequest) -> InterventionResult:
        """Process a request that requires manual intervention."""
        session_id = f"intervention_{int(time.time())}_{hash(request.prompt) % 1000}"
        export_path = self.config.export_path / session_id

        # Create session
        session = InterventionSession(
            session_id=session_id,
            request=request,
            export_path=export_path,
            status="exporting"
        )

        self.active_sessions[session_id] = session

        # Export data for expert review
        try:
            await self.exporter.export_for_intervention(session)
            session.status = "waiting_for_expert"

            self.logger.info(f"Intervention session {session_id} ready for expert review")

            # Wait for expert completion (in real implementation, this would be async)
            # For demo purposes, we'll simulate expert response
            await self._simulate_expert_response(session)

            # Import results
            result = await self.importer.import_results(session)

            # Mark session complete
            session.status = "completed"
            session.completed_at = time.time()
            session.expert_input = result.content
            session.quality_score = result.quality_score

            return result

        except Exception as e:
            session.status = "failed"
            self.logger.error(f"Intervention failed for session {session_id}: {e}")
            raise

    async def _simulate_expert_response(self, session: InterventionSession):
        """Simulate expert providing a response (for demo purposes)."""
        # In real implementation, this would wait for file creation
        response_file = session.export_path / "expert_response.md"

        # Simulate expert response
        expert_response = f"""# Expert Response

Thank you for the opportunity to provide detailed insight on: **{session.request.prompt[:50]}...**

## Comprehensive Analysis

This is a complex topic that requires careful consideration of multiple factors...

## Practical Implementation

Here's how you can approach this:

```python
def example_implementation():
    # Expert-level implementation
    return "High-quality solution"
```

## Key Considerations

1. **Quality Requirements**: Meeting {session.request.quality_requirement} standards
2. **Best Practices**: Following industry standards
3. **Scalability**: Ensuring long-term maintainability

## Recommendations

Based on my expertise, I recommend focusing on these key areas...

This response provides the depth and quality expected for expert-level assistance.
"""

        # Write simulated response
        import aiofiles
        async with aiofiles.open(response_file, 'w') as f:
            await f.write(expert_response)

        # Simulate processing time
        await asyncio.sleep(0.1)

    async def check_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Check the status of an intervention session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "status": session.status,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "export_path": str(session.export_path),
            "quality_score": session.quality_score
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get overall intervention system status."""
        active_count = len([s for s in self.active_sessions.values()
                           if s.status in ["waiting_for_expert", "in_progress"]])
        completed_count = len([s for s in self.active_sessions.values()
                              if s.status == "completed"])

        return {
            "enabled": self.config.enabled,
            "active_sessions": active_count,
            "completed_sessions": completed_count,
            "total_sessions": len(self.active_sessions),
            "quality_threshold": self.config.quality_threshold,
            "expert_timeout": self.config.expert_timeout
        }

    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = time.time()
                expired_sessions = []

                for session_id, session in self.active_sessions.items():
                    if (session.status == "waiting_for_expert" and
                        current_time - session.created_at > self.config.expert_timeout):
                        session.status = "expired"
                        expired_sessions.append(session_id)

                if expired_sessions:
                    self.logger.warning(f"Expired {len(expired_sessions)} intervention sessions")

            except Exception as e:
                self.logger.error(f"Session cleanup error: {e}")

    async def shutdown(self):
        """Shutdown the intervention system."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Intervention system shutdown complete")
