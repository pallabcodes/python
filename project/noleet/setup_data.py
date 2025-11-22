"""Setup script to initialize NoLeet with sample data."""

import logging
from pathlib import Path

from noleet.examples.sample_projects import create_sample_projects
from noleet.storage.repository import ProjectRepository


def setup_initial_data(data_dir: Path) -> None:
    """
    Initialize NoLeet with sample projects.
    
    Args:
        data_dir: Directory to store project data
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Setting up NoLeet data in {data_dir}")
    
    repository = ProjectRepository(data_dir)
    projects = create_sample_projects()
    
    repository.save_projects(projects)
    
    logger.info(f"Successfully initialized {len(projects)} sample projects")


if __name__ == "__main__":
    import sys
    
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / ".noleet" / "data"
    setup_initial_data(data_dir)

