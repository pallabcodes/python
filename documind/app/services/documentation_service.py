"""Documentation service for managing generated documentation."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundError
from app.models.documentation import Documentation
from app.models.code_entity import CodeEntity


class DocumentationService:
    """Service for managing documentation generation and retrieval."""

    def __init__(self, db: AsyncSession):
        """Initialize documentation service."""
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def get_documentation(self, doc_id: int) -> Documentation:
        """Get documentation by ID."""
        query = select(Documentation).where(Documentation.id == doc_id)
        result = await self.db.execute(query)
        documentation = result.scalar_one_or_none()

        if not documentation:
            raise NotFoundError("Documentation", doc_id)

        return documentation

    async def get_entity_documentation(self, entity_id: int) -> Optional[Documentation]:
        """Get documentation for a code entity."""
        query = select(Documentation).where(Documentation.code_entity_id == entity_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_repository_documentation(
        self,
        repo_id: int,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Documentation]:
        """List documentation for a repository."""
        query = select(Documentation).where(Documentation.repository_id == repo_id)

        if doc_type:
            query = query.where(Documentation.doc_type == doc_type)

        if status:
            query = query.where(Documentation.status == status)

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_documentation(
        self,
        repo_id: int,
        query: str,
        doc_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Documentation]:
        """Search documentation by content."""
        # Basic text search (would be enhanced with full-text search in production)
        search_query = select(Documentation).where(
            Documentation.repository_id == repo_id,
            (Documentation.title.contains(query) |
             Documentation.content.contains(query) |
             Documentation.summary.contains(query))
        )

        if doc_type:
            search_query = search_query.where(Documentation.doc_type == doc_type)

        search_query = search_query.limit(limit)
        result = await self.db.execute(search_query)
        return result.scalars().all()

    async def update_documentation(
        self,
        doc_id: int,
        updates: Dict
    ) -> Documentation:
        """Update documentation."""
        documentation = await self.get_documentation(doc_id)

        # Allowed update fields
        allowed_fields = [
            'title', 'content', 'summary', 'sections', 'parameters',
            'returns', 'raises', 'examples', 'notes', 'status',
            'quality_score', 'completeness_score', 'accuracy_score',
            'readability_score', 'needs_review'
        ]

        for field in allowed_fields:
            if field in updates:
                setattr(documentation, field, updates[field])

        await self.db.commit()
        await self.db.refresh(documentation)

        self.logger.info(f"Updated documentation {doc_id}")
        return documentation

    async def delete_documentation(self, doc_id: int) -> None:
        """Delete documentation."""
        documentation = await self.get_documentation(doc_id)

        await self.db.delete(documentation)
        await self.db.commit()

        self.logger.info(f"Deleted documentation {doc_id}")

    async def get_documentation_stats(self, repo_id: int) -> Dict:
        """Get documentation statistics for a repository."""
        from sqlalchemy import func

        # Total docs
        query = select(func.count(Documentation.id)).where(Documentation.repository_id == repo_id)
        result = await self.db.execute(query)
        total_docs = result.scalar()

        # Docs by type
        query = select(
            Documentation.doc_type,
            func.count(Documentation.id)
        ).where(Documentation.repository_id == repo_id).group_by(Documentation.doc_type)
        result = await self.db.execute(query)
        docs_by_type = dict(result.all())

        # Docs by status
        query = select(
            Documentation.status,
            func.count(Documentation.id)
        ).where(Documentation.repository_id == repo_id).group_by(Documentation.status)
        result = await self.db.execute(query)
        docs_by_status = dict(result.all())

        # Quality stats
        query = select(
            func.avg(Documentation.quality_score),
            func.avg(Documentation.completeness_score),
            func.avg(Documentation.accuracy_score),
            func.avg(Documentation.readability_score)
        ).where(Documentation.repository_id == repo_id)
        result = await self.db.execute(query)
        quality_stats = result.first()

        return {
            'repository_id': repo_id,
            'total_documentations': total_docs,
            'by_type': docs_by_type,
            'by_status': docs_by_status,
            'quality_metrics': {
                'average_quality': float(quality_stats[0]) if quality_stats[0] else 0,
                'average_completeness': float(quality_stats[1]) if quality_stats[1] else 0,
                'average_accuracy': float(quality_stats[2]) if quality_stats[2] else 0,
                'average_readability': float(quality_stats[3]) if quality_stats[3] else 0,
            },
        }

    async def regenerate_documentation(
        self,
        doc_id: int,
        model: Optional[str] = None
    ) -> Documentation:
        """Regenerate documentation using AI."""
        documentation = await self.get_documentation(doc_id)

        # Get the associated code entity
        if not documentation.code_entity_id:
            raise ValueError("Documentation not associated with a code entity")

        query = select(CodeEntity).where(CodeEntity.id == documentation.code_entity_id)
        result = await self.db.execute(query)
        code_entity = result.scalar_one_or_none()

        if not code_entity:
            raise NotFoundError("CodeEntity", documentation.code_entity_id)

        # Regenerate documentation
        from doc_generator import DocGenerator
        doc_generator = DocGenerator()

        new_documentation = await doc_generator.generate_documentation(
            code_entity,
            model=model
        )

        # Update existing documentation
        update_fields = [
            'content', 'summary', 'sections', 'parameters', 'returns',
            'raises', 'examples', 'notes', 'generated_by', 'generation_model',
            'quality_score', 'completeness_score', 'accuracy_score', 'readability_score'
        ]

        for field in update_fields:
            if hasattr(new_documentation, field):
                setattr(documentation, field, getattr(new_documentation, field))

        await self.db.commit()
        await self.db.refresh(documentation)

        self.logger.info(f"Regenerated documentation {doc_id}")
        return documentation

    async def export_documentation(
        self,
        repo_id: int,
        format: str = 'markdown',
        include_private: bool = False
    ) -> Dict:
        """Export documentation for a repository."""
        # Get all published documentation
        status_filter = ['published']
        if include_private:
            status_filter.append('draft')

        docs = await self.list_repository_documentation(
            repo_id, status=status_filter
        )

        # Format documentation
        if format == 'markdown':
            exported = await self._export_as_markdown(docs)
        elif format == 'json':
            exported = await self._export_as_json(docs)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        return {
            'repository_id': repo_id,
            'format': format,
            'total_docs': len(docs),
            'exported_at': 'now',  # Would be actual timestamp
            'data': exported,
        }

    async def _export_as_markdown(self, docs: List[Documentation]) -> str:
        """Export documentation as markdown."""
        lines = ["# Documentation Export\n"]

        for doc in docs:
            lines.append(f"## {doc.title}\n")
            if doc.summary:
                lines.append(f"{doc.summary}\n")
            if doc.content:
                lines.append(f"{doc.content}\n")
            lines.append("---\n")

        return "\n".join(lines)

    async def _export_as_json(self, docs: List[Documentation]) -> List[Dict]:
        """Export documentation as JSON."""
        return [
            {
                'id': doc.id,
                'title': doc.title,
                'summary': doc.summary,
                'content': doc.content,
                'type': doc.doc_type,
                'status': doc.status,
                'quality_score': doc.quality_score,
            }
            for doc in docs
        ]
