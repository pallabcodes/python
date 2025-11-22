"""Builder for creating and curating projects."""

from typing import List
import logging

from noleet.core.models import (
    Project, Task, Subtask, DSAInvolvement, ResearchReference, Topic
)


class ProjectBuilder:
    """Builder for creating projects with proper structure."""
    
    def __init__(self) -> None:
        """Initialize project builder."""
        self._logger = logging.getLogger(__name__)
    
    def create_project(
        self,
        project_id: str,
        title: str,
        description: str,
        short_description: str,
        tasks: List[Task],
        required_topics: List[Topic],
        primary_topics: List[Topic],
        difficulty: str = "intermediate",
        estimated_hours: int = 0,
        research_references: List[ResearchReference] = None,
        github_template: str = None,
        tags: List[str] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            project_id: Unique project identifier
            title: Project title
            description: Full project description
            short_description: Brief description for listings
            tasks: List of tasks in the project
            required_topics: Topics required for this project
            primary_topics: Primary topics this project focuses on
            difficulty: Difficulty level (beginner/intermediate/advanced)
            estimated_hours: Estimated hours to complete
            research_references: Research papers/repos used
            github_template: GitHub template repository URL
            tags: Project tags
            
        Returns:
            Created Project instance
        """
        project = Project(
            id=project_id,
            title=title,
            description=description,
            short_description=short_description,
            tasks=tasks or [],
            required_topics=set(required_topics or []),
            primary_topics=set(primary_topics or []),
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            research_references=research_references or [],
            github_template=github_template,
            tags=tags or []
        )
        
        self._logger.info(
            f"Created project: {project_id}",
            extra={
                "project_id": project_id,
                "title": title,
                "task_count": len(tasks),
                "topics": [t.value for t in primary_topics]
            }
        )
        
        return project
    
    def create_task(
        self,
        task_id: str,
        title: str,
        description: str,
        subtasks: List[Subtask] = None,
        dsa_involvements: List[DSAInvolvement] = None,
        order: int = 0
    ) -> Task:
        """
        Create a task.
        
        Args:
            task_id: Unique task identifier
            title: Task title
            description: Task description in plain English
            subtasks: List of subtasks
            dsa_involvements: DSA concepts involved
            order: Task order in project
            
        Returns:
            Created Task instance
        """
        return Task(
            id=task_id,
            title=title,
            description=description,
            subtasks=subtasks or [],
            dsa_involvements=dsa_involvements or [],
            order=order
        )
    
    def create_subtask(
        self,
        subtask_id: str,
        title: str,
        description: str,
        dsa_involvements: List[DSAInvolvement] = None,
        order: int = 0
    ) -> Subtask:
        """
        Create a subtask.
        
        Args:
            subtask_id: Unique subtask identifier
            title: Subtask title
            description: Subtask description in plain English
            dsa_involvements: DSA concepts involved
            order: Subtask order in task
            
        Returns:
            Created Subtask instance
        """
        return Subtask(
            id=subtask_id,
            title=title,
            description=description,
            dsa_involvements=dsa_involvements or [],
            order=order
        )
    
    def create_dsa_involvement(self, topic: Topic, percentage: float) -> DSAInvolvement:
        """
        Create DSA involvement record.
        
        Args:
            topic: DSA topic
            percentage: Involvement percentage (0-100)
            
        Returns:
            Created DSAInvolvement instance
        """
        return DSAInvolvement(topic=topic, percentage=percentage)
    
    def create_research_reference(
        self,
        title: str,
        authors: List[str],
        url: str = None,
        github_repo: str = None,
        description: str = "",
        algorithms: List[str] = None,
        custom_modifications: str = ""
    ) -> ResearchReference:
        """
        Create research reference.
        
        Args:
            title: Paper/repo title
            authors: List of authors
            url: URL to paper/repo
            github_repo: GitHub repository URL
            description: Description of the research
            algorithms: Algorithms used from this research
            custom_modifications: Custom modifications made
            
        Returns:
            Created ResearchReference instance
        """
        return ResearchReference(
            title=title,
            authors=authors,
            url=url,
            github_repo=github_repo,
            description=description,
            algorithms=algorithms or [],
            custom_modifications=custom_modifications
        )

