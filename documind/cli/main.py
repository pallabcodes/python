"""Main CLI entry point for DocuMind."""

import asyncio
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.core.config import settings
from app.services.repository_service import RepositoryService
from app.services.analysis_service import AnalysisService
from app.services.documentation_service import DocumentationService
from app.db.session import get_db

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DocuMind: AI-Powered Documentation Assistant

    Automatically generate, maintain, and enhance documentation
    for your codebase using advanced AI and code analysis.
    """
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--name", help="Repository name (auto-detected if not provided)")
@click.option("--platform", default="local", help="Platform: local, github, gitlab")
@click.option("--language", help="Primary language (auto-detected if not provided)")
def init(path: str, name: Optional[str], platform: str, language: Optional[str]):
    """Initialize a repository for DocuMind analysis."""
    async def _init():
        async for db in get_db():
            repo_service = RepositoryService(db)

            try:
                path_obj = Path(path).resolve()

                # Auto-detect repository info
                if not name:
                    name = path_obj.name

                full_name = f"{platform}/{name}"

                # Check if repository already exists
                existing = await repo_service.get_repository_by_full_name(full_name)
                if existing:
                    console.print(f"[yellow]⚠️  Repository already exists: {full_name}[/yellow]")
                    console.print(f"   Use 'documind analyze {existing.id}' to analyze it")
                    return

                # Detect language if not provided
                if not language:
                    language = detect_primary_language(path_obj)

                # Create repository
                repo_data = {
                    "name": name,
                    "full_name": full_name,
                    "url": f"file://{path_obj}",
                    "clone_url": f"file://{path_obj}",
                    "platform": platform,
                    "language": language,
                    "is_active": True,
                    "analysis_enabled": True,
                }

                repository = await repo_service.create_repository(repo_data)

                console.print(f"[green]✅ Initialized repository: {repository.full_name}[/green]")
                console.print(f"[dim]Repository ID: {repository.id}[/dim]")
                console.print(f"[dim]Language: {repository.language}[/dim]")
                console.print(f"[dim]Path: {path_obj}[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Failed to initialize repository: {e}[/red]")

    asyncio.run(_init())


@cli.command()
@click.argument("repo_id", type=int)
@click.option("--path", help="Repository path (uses stored path if not provided)")
@click.option("--config", help="Analysis config file")
@click.option("--force", is_flag=True, help="Force re-analysis of already analyzed entities")
def analyze(repo_id: int, path: Optional[str], config: Optional[str], force: bool):
    """Analyze a repository and generate documentation."""
    async def _analyze():
        async for db in get_db():
            repo_service = RepositoryService(db)
            analysis_service = AnalysisService(db)

            try:
                # Get repository
                repository = await repo_service.get_repository(repo_id)

                # Determine repository path
                if path:
                    repo_path = path
                else:
                    # Extract path from URL (for local repos)
                    if repository.url.startswith("file://"):
                        repo_path = repository.url[7:]  # Remove file:// prefix
                    else:
                        console.print("[red]❌ Repository path not provided and not stored[/red]")
                        return

                if not os.path.exists(repo_path):
                    console.print(f"[red]❌ Repository path does not exist: {repo_path}[/red]")
                    return

                console.print(f"[green]🔍 Analyzing repository: {repository.full_name}[/green]")
                console.print(f"[dim]Path: {repo_path}[/dim]")

                # Load config if provided
                analysis_config = {}
                if config and os.path.exists(config):
                    import json
                    with open(config, 'r') as f:
                        analysis_config = json.load(f)

                # Run analysis
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Analyzing codebase...", total=None)

                    result = await analysis_service.analyze_repository(
                        repo_id, repo_path, analysis_config
                    )

                    progress.update(task, completed=True)

                # Display results
                console.print(f"[green]✅ Analysis completed![/green]")
                console.print(f"[dim]Entities found: {result['entities_found']}[/dim]")
                console.print(f"[dim]Documentation generated: {result['docs_generated']}[/dim]")
                console.print(f"[dim]Files processed: {result['files_processed']}[/dim]")
                console.print(f"[dim]Languages detected: {', '.join(result['languages'])}[/dim]")

                # Show summary stats
                summary = result.get('summary', {})
                if summary.get('documentation_coverage') is not None:
                    coverage = summary['documentation_coverage']
                    console.print(f"[dim]Documentation coverage: {coverage}%[/dim]")

                if summary.get('total_entities', 0) > 0:
                    console.print(f"\n[dim]Entity breakdown:[/dim]")
                    for entity_type, count in summary.get('entity_types', {}).items():
                        console.print(f"  • {entity_type.title()}s: {count}")

            except Exception as e:
                console.print(f"[red]❌ Analysis failed: {e}[/red]")

    asyncio.run(_analyze())


@cli.command()
@click.argument("repo_id", type=int)
@click.option("--type", help="Documentation type: api, guide, tutorial")
@click.option("--status", help="Status: draft, published, archived")
@click.option("--limit", default=20, help="Number of results to show")
def docs(repo_id: int, type: Optional[str], status: Optional[str], limit: int):
    """List and manage documentation for a repository."""
    async def _docs():
        async for db in get_db():
            doc_service = DocumentationService(db)

            try:
                # Get documentation list
                docs = await doc_service.list_repository_documentation(
                    repo_id, doc_type=type, status=status, limit=limit
                )

                if not docs:
                    console.print(f"[yellow]⚠️  No documentation found for repository {repo_id}[/yellow]")
                    return

                # Display documentation table
                table = Table(title=f"Documentation ({len(docs)} items)")
                table.add_column("ID", style="dim")
                table.add_column("Title", style="bold")
                table.add_column("Type", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Quality", style="yellow")

                for doc in docs:
                    quality = f"{doc.quality_score:.1f}" if doc.quality_score else "N/A"
                    table.add_row(
                        str(doc.id),
                        doc.title[:50] + "..." if len(doc.title) > 50 else doc.title,
                        doc.doc_type or "N/A",
                        doc.status,
                        quality
                    )

                console.print(table)

                # Show stats
                stats = await doc_service.get_documentation_stats(repo_id)
                console.print(f"\n[dim]Total documentation: {stats['total_documentations']}[/dim]")
                if stats['quality_metrics']['average_quality'] > 0:
                    console.print(f"[dim]Average quality: {stats['quality_metrics']['average_quality']:.2f}[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Failed to get documentation: {e}[/red]")

    asyncio.run(_docs())


@cli.command()
@click.argument("repo_id", type=int)
@click.argument("query")
@click.option("--type", help="Documentation type filter")
@click.option("--limit", default=10, help="Number of results")
def search(repo_id: int, query: str, type: Optional[str], limit: int):
    """Search documentation in a repository."""
    async def _search():
        async for db in get_db():
            doc_service = DocumentationService(db)

            try:
                results = await doc_service.search_documentation(
                    repo_id, query, doc_type=type, limit=limit
                )

                if not results:
                    console.print(f"[yellow]⚠️  No results found for '{query}'[/yellow]")
                    return

                console.print(f"[green]🔍 Found {len(results)} results for '{query}'[/green]")

                for i, doc in enumerate(results, 1):
                    console.print(f"\n[bold]{i}. {doc.title}[/bold]")
                    console.print(f"   Type: {doc.doc_type} | Status: {doc.status}")
                    if doc.summary:
                        summary = doc.summary[:100] + "..." if len(doc.summary) > 100 else doc.summary
                        console.print(f"   Summary: {summary}")
                    console.print(f"   Quality: {doc.quality_score:.1f}" if doc.quality_score else "   Quality: N/A")

            except Exception as e:
                console.print(f"[red]❌ Search failed: {e}[/red]")

    asyncio.run(_search())


@cli.command()
@click.argument("repo_id", type=int)
@click.option("--format", default="markdown", type=click.Choice(["markdown", "json"]), help="Export format")
@click.option("--include-private", is_flag=True, help="Include draft/private documentation")
def export(repo_id: int, format: str, include_private: bool):
    """Export documentation from a repository."""
    async def _export():
        async for db in get_db():
            doc_service = DocumentationService(db)

            try:
                console.print(f"[green]📤 Exporting documentation...[/green]")

                result = await doc_service.export_documentation(
                    repo_id, format=format, include_private=include_private
                )

                filename = f"docs_export_{repo_id}.{format}"
                with open(filename, 'w', encoding='utf-8') as f:
                    if format == 'json':
                        import json
                        json.dump(result['data'], f, indent=2)
                    else:
                        f.write(result['data'])

                console.print(f"[green]✅ Exported {result['total_docs']} documents to {filename}[/green]")
                console.print(f"[dim]Format: {format}[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Export failed: {e}[/red]")

    asyncio.run(_export())


@cli.command()
@click.argument("repo_id", type=int)
def status(repo_id: int):
    """Show analysis and documentation status for a repository."""
    async def _status():
        async for db in get_db():
            repo_service = RepositoryService(db)
            analysis_service = AnalysisService(db)
            doc_service = DocumentationService(db)

            try:
                # Get repository info
                repository = await repo_service.get_repository(repo_id)
                analysis_status = await analysis_service.get_analysis_status(repo_id)
                doc_stats = await doc_service.get_documentation_stats(repo_id)
                repo_stats = await repo_service.get_repository_stats(repo_id)

                console.print(f"[bold green]📊 Repository Status: {repository.full_name}[/bold green]")
                console.print("=" * 60)

                # Repository info
                console.print(f"[bold]Repository Info:[/bold]")
                console.print(f"  Platform: {repository.platform}")
                console.print(f"  Language: {repository.language}")
                console.print(f"  Active: {'✅' if repository.is_active else '❌'}")
                console.print(f"  Analysis Enabled: {'✅' if repository.analysis_enabled else '❌'}")
                console.print(f"  Last Analysis: {analysis_status.get('last_analysis', 'Never')}")
                console.print()

                # Analysis status
                console.print(f"[bold]Analysis Status:[/bold]")
                console.print(f"  Status: {analysis_status['status']}")
                if analysis_status['latest_run_id']:
                    console.print(f"  Latest Run ID: {analysis_status['latest_run_id']}")
                    console.print(f"  Entities Found: {analysis_status['entities_found']}")
                    console.print(f"  Docs Generated: {analysis_status['docs_generated']}")
                console.print()

                # Documentation stats
                console.print(f"[bold]Documentation Stats:[/bold]")
                console.print(f"  Total Docs: {doc_stats['total_documentations']}")
                console.print(f"  Coverage: {repo_stats['documentation_coverage']}%")
                console.print(f"  Average Quality: {doc_stats['quality_metrics']['average_quality']:.2f}")
                console.print()

                # Entity breakdown
                if repo_stats['entities_by_type']:
                    console.print(f"[bold]Code Entities:[/bold]")
                    for entity_type, count in repo_stats['entities_by_type'].items():
                        console.print(f"  {entity_type.title()}s: {count}")
                    console.print(f"  Total: {repo_stats['total_entities']}")

            except Exception as e:
                console.print(f"[red]❌ Failed to get status: {e}[/red]")

    asyncio.run(_status())


@cli.command()
def repos():
    """List all repositories."""
    async def _repos():
        async for db in get_db():
            repo_service = RepositoryService(db)

            try:
                repositories = await repo_service.list_repositories(active_only=False)

                if not repositories:
                    console.print("[yellow]⚠️  No repositories found[/yellow]")
                    console.print("   Use 'documind init <path>' to initialize a repository")
                    return

                table = Table(title=f"Repositories ({len(repositories)} total)")
                table.add_column("ID", style="dim")
                table.add_column("Name", style="bold")
                table.add_column("Platform", style="cyan")
                table.add_column("Language", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Last Analysis", style="magenta")

                for repo in repositories:
                    status = "Active" if repo.is_active else "Inactive"
                    last_analysis = repo.last_analysis_at.strftime("%Y-%m-%d") if repo.last_analysis_at else "Never"

                    table.add_row(
                        str(repo.id),
                        repo.name,
                        repo.platform,
                        repo.language or "Unknown",
                        status,
                        last_analysis
                    )

                console.print(table)

            except Exception as e:
                console.print(f"[red]❌ Failed to list repositories: {e}[/red]")

    asyncio.run(_repos())


@cli.command()
def server():
    """Start the DocuMind web server."""
    import uvicorn
    from app.main import app

    console.print("[green]🚀 Starting DocuMind Server[/green]")
    console.print(f"[dim]API docs: http://localhost:{settings.PORT}/docs[/dim]")
    console.print(f"[dim]Health check: http://localhost:{settings.PORT}/health[/dim]")

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )


@cli.command()
def init_db():
    """Initialize the database."""
    async def _init_db():
        from app.db.base import Base
        from app.db.session import engine

        console.print("[yellow]🔧 Initializing database...[/yellow]")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        console.print("[green]✅ Database initialized successfully![/green]")

    asyncio.run(_init_db())


def detect_primary_language(repo_path: Path) -> Optional[str]:
    """Detect the primary programming language of a repository."""
    # Simple detection based on file extensions
    extensions = {}
    total_files = 0

    for root, dirs, files in os.walk(repo_path):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.next', 'dist', 'build'}]

        for file in files:
            if '.' in file:
                ext = file.split('.')[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1
                total_files += 1

    if not extensions:
        return None

    # Language mapping
    lang_map = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'java': 'java',
        'go': 'go',
        'rs': 'rust',
        'cpp': 'cpp',
        'c': 'c',
        'php': 'php',
        'rb': 'ruby',
        'swift': 'swift',
        'kt': 'kotlin',
        'scala': 'scala',
    }

    # Find most common language
    max_count = 0
    primary_lang = None

    for ext, count in extensions.items():
        if ext in lang_map and count > max_count:
            max_count = count
            primary_lang = lang_map[ext]

    return primary_lang


if __name__ == "__main__":
    cli()
