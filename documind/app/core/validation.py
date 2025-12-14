"""Input validation utilities for DocuMind."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator, Field
from pydantic.generics import GenericModel
from enum import Enum


class RepositoryPlatform(str, Enum):
    """Supported repository platforms."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"


class AnalysisStatus(str, Enum):
    """Analysis run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentationType(str, Enum):
    """Documentation types."""
    API = "api"
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"


class DocumentationFormat(str, Enum):
    """Documentation formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    PLAINTEXT = "plaintext"


class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class RepositoryCreate(BaseModel):
    """Repository creation schema."""
    name: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., min_length=1, max_length=500)
    clone_url: str = Field(..., min_length=1, max_length=500)
    platform: RepositoryPlatform
    platform_id: Optional[str] = Field(None, max_length=100)
    owner: str = Field(..., min_length=1, max_length=255)
    is_private: bool = False
    is_fork: bool = False
    default_branch: str = Field("main", min_length=1, max_length=100)
    language: Optional[str] = Field(None, max_length=50)
    languages: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    stars: int = Field(0, ge=0)
    forks: int = Field(0, ge=0)
    watchers: int = Field(0, ge=0)
    size_kb: Optional[int] = Field(None, ge=0)
    is_active: bool = True
    analysis_enabled: bool = True
    analysis_config: Optional[Dict[str, Any]] = None
    ignore_patterns: Optional[List[str]] = None

    @validator('url', 'clone_url')
    def validate_url(cls, v):
        """Validate URL format."""
        from app.core.security import is_valid_url
        if not is_valid_url(v):
            raise ValueError('Invalid URL format')
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name format (owner/repo)."""
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Full name must be in format owner/repo')
        return v


class RepositoryUpdate(BaseModel):
    """Repository update schema."""
    description: Optional[str] = Field(None, max_length=1000)
    language: Optional[str] = Field(None, max_length=50)
    languages: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    stars: Optional[int] = Field(None, ge=0)
    forks: Optional[int] = Field(None, ge=0)
    watchers: Optional[int] = Field(None, ge=0)
    size_kb: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    analysis_enabled: Optional[bool] = None
    last_commit_sha: Optional[str] = Field(None, min_length=40, max_length=40)
    analysis_config: Optional[Dict[str, Any]] = None
    ignore_patterns: Optional[List[str]] = None


class CodeEntityBase(BaseModel):
    """Base code entity schema."""
    entity_type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    qualified_name: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=500)
    start_line: int = Field(..., gt=0)
    end_line: Optional[int] = Field(None, gt=0)
    start_column: Optional[int] = Field(None, ge=0)
    end_column: Optional[int] = Field(None, ge=0)
    source_code: Optional[str] = None
    signature: Optional[str] = Field(None, max_length=1000)
    docstring: Optional[str] = None
    language: str = Field(..., min_length=1, max_length=50)
    complexity_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    parameter_count: Optional[int] = Field(None, ge=0)
    return_type: Optional[str] = Field(None, max_length=100)
    is_async: Optional[str] = None
    dependencies: Optional[List[str]] = None
    dependents: Optional[List[str]] = None
    inheritance: Optional[List[str]] = None
    visibility: Optional[str] = None
    decorators: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class DocumentationCreate(BaseModel):
    """Documentation creation schema."""
    repository_id: int = Field(..., gt=0)
    code_entity_id: Optional[int] = Field(None, gt=0)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=5000)
    sections: Optional[Dict[str, Any]] = None
    parameters: Optional[List[Dict[str, str]]] = None
    returns: Optional[Dict[str, str]] = None
    raises: Optional[List[Dict[str, str]]] = None
    examples: Optional[List[Dict[str, str]]] = None
    notes: Optional[List[str]] = None
    doc_type: DocumentationType = DocumentationType.API
    format: DocumentationFormat = DocumentationFormat.MARKDOWN
    language: Optional[str] = Field(None, max_length=50)
    generated_by: str = Field("ai", min_length=1, max_length=50)
    generation_model: Optional[str] = Field(None, max_length=100)
    generation_prompt: Optional[str] = None
    status: str = Field("draft", min_length=1, max_length=20)
    is_auto_generated: bool = True
    needs_review: bool = False


class DocumentationUpdate(BaseModel):
    """Documentation update schema."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=5000)
    sections: Optional[Dict[str, Any]] = None
    parameters: Optional[List[Dict[str, str]]] = None
    returns: Optional[Dict[str, str]] = None
    raises: Optional[List[Dict[str, str]]] = None
    examples: Optional[List[Dict[str, str]]] = None
    notes: Optional[List[str]] = None
    status: Optional[str] = Field(None, min_length=1, max_length=20)
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    completeness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    accuracy_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    readability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    needs_review: Optional[bool] = None


class UserCreate(BaseModel):
    """User creation schema."""
    email: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    role: UserRole = UserRole.USER

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if v is None:
            return v
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{{2,}}$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if v is None:
            return v
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class AnalysisRunCreate(BaseModel):
    """Analysis run creation schema."""
    repository_id: int = Field(..., gt=0)
    trigger_type: str = Field("manual", min_length=1, max_length=50)
    trigger_source: Optional[str] = Field(None, max_length=100)
    target_branch: str = Field("main", min_length=1, max_length=100)
    commit_sha: Optional[str] = Field(None, min_length=40, max_length=40)
    analysis_config: Optional[Dict[str, Any]] = None


class IntegrationCreate(BaseModel):
    """Integration creation schema."""
    repository_id: Optional[int] = Field(None, gt=0)
    service_type: str = Field(..., min_length=1, max_length=50)
    service_name: str = Field(..., min_length=1, max_length=100)
    external_id: Optional[str] = Field(None, max_length=100)
    auth_type: str = Field(..., min_length=1, max_length=20)
    config: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None
    scope: Optional[List[str]] = None
    owner_id: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, gt=0)
    per_page: int = Field(20, gt=0, le=100)


class SearchParams(BaseModel):
    """Search parameters."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class APIResponse(GenericModel, GenericModel):
    """Generic API response wrapper."""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    pagination: Optional[Dict[str, Any]] = None


def validate_file_upload(file, max_size: int = 50 * 1024 * 1024) -> bool:
    """Validate file upload."""
    if file.size > max_size:
        return False

    # Check file type/extension
    allowed_extensions = {'.zip', '.tar.gz', '.py', '.js', '.ts', '.java', '.go', '.rs', '.md'}
    filename = file.filename.lower()

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return False

    return True


def sanitize_search_query(query: str) -> str:
    """Sanitize search query to prevent injection."""
    # Remove dangerous characters
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
    for char in dangerous_chars:
        query = query.replace(char, '')

    # Limit length
    return query[:500].strip()
