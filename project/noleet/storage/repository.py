"""Repository for project data storage and retrieval."""

from typing import List, Optional
import json
import logging
from pathlib import Path

from noleet.core.models import Project, Topic


class ProjectRepository:
    """Repository for managing project data."""
    
    def __init__(self, data_dir: Path) -> None:
        """
        Initialize repository.
        
        Args:
            data_dir: Directory containing project data files
        """
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(__name__)
        self._projects_cache: Optional[List[Project]] = None
    
    def load_projects(self) -> List[Project]:
        """
        Load all projects from storage.
        
        Returns:
            List of all projects
        """
        if self._projects_cache is not None:
            return self._projects_cache
        
        projects_file = self._data_dir / "projects.json"
        if not projects_file.exists():
            self._logger.warning(f"Projects file not found: {projects_file}")
            return []
        
        try:
            with open(projects_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            projects = [self._deserialize_project(proj_data) for proj_data in data]
            self._projects_cache = projects
            
            self._logger.info(
                f"Loaded {len(projects)} projects from {projects_file}",
                extra={"project_count": len(projects)}
            )
            
            return projects
            
        except Exception as e:
            self._logger.error(
                f"Failed to load projects: {e}",
                exc_info=True,
                extra={"file": str(projects_file)}
            )
            return []
    
    def save_projects(self, projects: List[Project]) -> None:
        """
        Save projects to storage.
        
        Args:
            projects: List of projects to save
        """
        projects_file = self._data_dir / "projects.json"
        
        try:
            data = [self._serialize_project(project) for project in projects]
            
            with open(projects_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._projects_cache = projects
            
            self._logger.info(
                f"Saved {len(projects)} projects to {projects_file}",
                extra={"project_count": len(projects)}
            )
            
        except Exception as e:
            self._logger.error(
                f"Failed to save projects: {e}",
                exc_info=True,
                extra={"file": str(projects_file)}
            )
            raise
    
    def _serialize_project(self, project: Project) -> dict:
        """Serialize project to dictionary."""
        return {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "short_description": project.short_description,
            "tasks": [self._serialize_task(task) for task in project.tasks],
            "required_topics": [t.value for t in project.required_topics],
            "primary_topics": [t.value for t in project.primary_topics],
            "difficulty": project.difficulty,
            "estimated_hours": project.estimated_hours,
            "research_references": [
                {
                    "title": ref.title,
                    "authors": ref.authors,
                    "url": ref.url,
                    "github_repo": ref.github_repo,
                    "description": ref.description,
                    "algorithms": ref.algorithms,
                    "custom_modifications": ref.custom_modifications
                }
                for ref in project.research_references
            ],
            "github_template": project.github_template,
            "tags": project.tags
        }
    
    def _serialize_task(self, task) -> dict:
        """Serialize task to dictionary."""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "subtasks": [
                {
                    "id": subtask.id,
                    "title": subtask.title,
                    "description": subtask.description,
                    "dsa_involvements": [
                        {
                            "topic": inv.topic.value,
                            "percentage": inv.percentage
                        }
                        for inv in subtask.dsa_involvements
                    ],
                    "order": subtask.order
                }
                for subtask in task.subtasks
            ],
            "dsa_involvements": [
                {
                    "topic": inv.topic.value,
                    "percentage": inv.percentage
                }
                for inv in task.dsa_involvements
            ],
            "order": task.order
        }
    
    def _deserialize_project(self, data: dict) -> Project:
        """Deserialize project from dictionary."""
        from noleet.core.models import (
            Task, Subtask, DSAInvolvement, ResearchReference
        )
        
        tasks = []
        for task_data in data.get("tasks", []):
            subtasks = [
                Subtask(
                    id=st_data["id"],
                    title=st_data["title"],
                    description=st_data["description"],
                    dsa_involvements=[
                        DSAInvolvement(
                            topic=Topic(inv_data["topic"]),
                            percentage=inv_data["percentage"]
                        )
                        for inv_data in st_data.get("dsa_involvements", [])
                    ],
                    order=st_data.get("order", 0)
                )
                for st_data in task_data.get("subtasks", [])
            ]
            
            tasks.append(
                Task(
                    id=task_data["id"],
                    title=task_data["title"],
                    description=task_data["description"],
                    subtasks=subtasks,
                    dsa_involvements=[
                        DSAInvolvement(
                            topic=Topic(inv_data["topic"]),
                            percentage=inv_data["percentage"]
                        )
                        for inv_data in task_data.get("dsa_involvements", [])
                    ],
                    order=task_data.get("order", 0)
                )
            )
        
        research_refs = [
            ResearchReference(
                title=ref_data["title"],
                authors=ref_data.get("authors", []),
                url=ref_data.get("url"),
                github_repo=ref_data.get("github_repo"),
                description=ref_data.get("description", ""),
                algorithms=ref_data.get("algorithms", []),
                custom_modifications=ref_data.get("custom_modifications", "")
            )
            for ref_data in data.get("research_references", [])
        ]
        
        return Project(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            short_description=data.get("short_description", ""),
            tasks=tasks,
            required_topics={Topic(t) for t in data.get("required_topics", [])},
            primary_topics={Topic(t) for t in data.get("primary_topics", [])},
            difficulty=data.get("difficulty", "intermediate"),
            estimated_hours=data.get("estimated_hours", 0),
            research_references=research_refs,
            github_template=data.get("github_template"),
            tags=data.get("tags", [])
        )

