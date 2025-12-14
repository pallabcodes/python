"""Main CLI entry point for Acquisitor."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from app.core.config import settings
from app.services.company_service import CompanyService
from app.services.analysis_service import AnalysisService
from app.services.reporting_service import ReportingService
from app.services.validation_service import ValidationService
from app.db.session import get_db

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Acquisitor: Relative Product Research & Ideation Tool

    Identify acquisition opportunities by building products that solve
    specific pain points for companies like Notion, Canva, etc.
    """
    pass


@cli.group()
def companies():
    """Manage target companies."""
    pass


@cli.group()
def analysis():
    """Run analysis and ideation."""
    pass


@cli.group()
def validation():
    """Manage hypothesis validation and experiments."""
    pass


@companies.command("list")
@click.option("--limit", default=20, help="Number of companies to show")
def list_companies(limit: int):
    """List all target companies."""
    async def _list_companies():
        async for db in get_db():
            service = CompanyService(db)
            companies_list = await service.get_companies(limit=limit)

            if not companies_list:
                console.print("[yellow]No companies found. Add some with 'companies add'[/yellow]")
                return

            table = Table(title="Target Companies")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Domain", style="blue")
            table.add_column("Industry", style="green")
            table.add_column("Pain Points", style="red", justify="right")
            table.add_column("Ideas", style="yellow", justify="right")

            for company in companies_list:
                table.add_row(
                    str(company.id),
                    company.name,
                    company.domain,
                    company.industry or "N/A",
                    str(company.pain_points_count),
                    str(company.product_ideas_count),
                )

            console.print(table)

    asyncio.run(_list_companies())


@companies.command("add")
@click.option("--name", required=True, help="Company name")
@click.option("--domain", required=True, help="Company domain")
@click.option("--industry", help="Industry sector")
@click.option("--description", help="Company description")
def add_company(name: str, domain: str, industry: Optional[str], description: Optional[str]):
    """Add a new target company."""
    async def _add_company():
        from app.schemas.company import CompanyCreate

        company_data = CompanyCreate(
            name=name,
            domain=domain,
            industry=industry,
            description=description,
        )

        async for db in get_db():
            service = CompanyService(db)
            company = await service.create_company(company_data)

            console.print(f"[green]✅ Added company:[/green] {company.name} ({company.domain})")
            console.print(f"[dim]ID: {company.id}[/dim]")

    asyncio.run(_add_company())


@companies.command("research")
@click.argument("company_id", type=int)
def start_research(company_id: int):
    """Start research collection for a company."""
    async def _start_research():
        async for db in get_db():
            service = CompanyService(db)
            success = await service.start_research(company_id)

            if success:
                console.print(f"[green]🚀 Started research for company ID {company_id}[/green]")
                console.print("[dim]Research collection will run in the background[/dim]")
            else:
                console.print(f"[red]❌ Company with ID {company_id} not found[/red]")

    asyncio.run(_start_research())


@analysis.command("run")
@click.argument("company_id", type=int)
def run_full_analysis(company_id: int):
    """Run complete analysis pipeline for a company."""
    async def _run_analysis():
        async for db in get_db():
            service = AnalysisService(db)

            with console.status("[bold green]Running full analysis...") as status:
                try:
                    result = await service.run_full_analysis(company_id)

                    console.print(f"[green]✅ Analysis completed for company {company_id}[/green]")
                    console.print(f"[dim]Pain points found: {result['pain_points_found']}[/dim]")
                    console.print(f"[dim]Product ideas generated: {result['product_ideas_generated']}[/dim]")

                    # Show top insights
                    summary = result.get('analysis_summary', {})
                    insights = summary.get('insights', [])
                    if insights:
                        console.print("\n[bold]Key Insights:[/bold]")
                        for insight in insights[:3]:  # Show top 3
                            console.print(f"• {insight}")

                    # Show top ideas
                    top_ideas = result.get('top_ideas', [])
                    if top_ideas:
                        console.print("\n[bold]Top Product Ideas:[/bold]")
                        for i, idea in enumerate(top_ideas[:3], 1):
                            console.print(f"{i}. {idea['title']} (Fit: {idea['acquisition_fit_score']:.1%})")

                except Exception as e:
                    console.print(f"[red]❌ Analysis failed: {e}[/red]")

    asyncio.run(_run_analysis())


@analysis.command("pain-points")
@click.argument("company_id", type=int)
def analyze_pain_points(company_id: int):
    """Analyze pain points for a company."""
    async def _analyze_pain_points():
        async for db in get_db():
            service = AnalysisService(db)

            with console.status("[bold green]Analyzing pain points...") as status:
                try:
                    result = await service.analyze_pain_points(company_id)

                    console.print(f"[green]✅ Pain point analysis completed[/green]")
                    console.print(f"[dim]Pain points found: {result['pain_points_found']}[/dim]")

                    summary = result.get('summary', {})
                    severity_dist = summary.get('severity_distribution', {})
                    if severity_dist:
                        console.print("\n[bold]Severity Distribution:[/bold]")
                        for level, count in severity_dist.items():
                            console.print(f"• {level.title()}: {count}")

                except Exception as e:
                    console.print(f"[red]❌ Pain point analysis failed: {e}[/red]")

    asyncio.run(_analyze_pain_points())


@analysis.command("ideas")
@click.argument("company_id", type=int)
def generate_ideas(company_id: int):
    """Generate product ideas for a company."""
    async def _generate_ideas():
        async for db in get_db():
            service = AnalysisService(db)

            with console.status("[bold green]Generating product ideas...") as status:
                try:
                    result = await service.generate_product_ideas(company_id)

                    console.print(f"[green]✅ Product ideation completed[/green]")
                    console.print(f"[dim]Ideas generated: {result['ideas_generated']}[/dim]")

                    top_ideas = result.get('top_ideas', [])
                    if top_ideas:
                        console.print("\n[bold]Top Product Ideas:[/bold]")
                        for i, idea in enumerate(top_ideas[:5], 1):
                            console.print(f"{i}. {idea['title']}")
                            console.print(f"   Category: {idea['category']} | Fit: {idea['acquisition_fit_score']:.1%}")

                except Exception as e:
                    console.print(f"[red]❌ Product ideation failed: {e}[/red]")

    asyncio.run(_generate_ideas())


@analysis.command("summary")
@click.argument("company_id", type=int)
def show_analysis_summary(company_id: int):
    """Show comprehensive analysis summary for a company."""
    async def _show_summary():
        async for db in get_db():
            service = AnalysisService(db)

            try:
                summary = await service.get_analysis_summary(company_id)

                if summary.get('status') == 'not_analyzed':
                    console.print(f"[yellow]⚠️  No analysis has been run for company {company_id} yet[/yellow]")
                    console.print("[dim]Run 'acquisitor analysis run {company_id}' first[/dim]")
                    return

                console.print(f"[bold green]📊 Analysis Summary for Company {company_id}[/bold green]")

                # Pain points summary
                pp_data = summary.get('pain_points', {})
                console.print(f"\n[bold]Pain Points:[/bold] {pp_data.get('total', 0)} found")

                severity_dist = pp_data.get('by_severity', {})
                if severity_dist:
                    console.print("Severity breakdown:")
                    for level, count in severity_dist.items():
                        console.print(f"  • {level.title()}: {count}")

                # Product ideas summary
                ideas_data = summary.get('product_ideas', {})
                console.print(f"\n[bold]Product Ideas:[/bold] {ideas_data.get('total', 0)} generated")

                top_ideas = ideas_data.get('top_ideas', [])
                if top_ideas:
                    console.print("\n[bold]Top 3 Ideas:[/bold]")
                    for i, idea in enumerate(top_ideas[:3], 1):
                        console.print(f"{i}. {idea['title']}")
                        console.print(f"   Fit: {idea['acquisition_fit_score']:.1%} | Category: {idea['category']}")

                # Insights
                insights = summary.get('insights', [])
                if insights:
                    console.print("\n[bold]Key Insights:[/bold]")
                    for insight in insights:
                        console.print(f"• {insight}")

            except Exception as e:
                console.print(f"[red]❌ Failed to get analysis summary: {e}[/red]")

    asyncio.run(_show_summary())


@cli.group()
def validation():
    """Manage hypothesis validation and experiments."""
    pass


@validation.command("create-hypothesis")
@click.argument("idea_id", type=int)
@click.option("--title", required=True, help="Hypothesis title")
@click.option("--statement", required=True, help="Hypothesis statement (If X, then Y)")
@click.option("--assumption", required=True, help="Core assumption to test")
@click.option("--outcome", required=True, help="Expected outcome")
@click.option("--criteria", required=True, help="Success criteria (JSON string)")
@click.option("--category", default="product", help="Hypothesis category")
@click.option("--priority", default="medium", type=click.Choice(["critical", "high", "medium", "low"]), help="Priority level")
@click.option("--method", help="Validation method (survey, prototype, etc.)")
def create_hypothesis(
    idea_id: int,
    title: str,
    statement: str,
    assumption: str,
    outcome: str,
    criteria: str,
    category: str,
    priority: str,
    method: str
):
    """Create a hypothesis for validation."""
    import json

    async def _create_hypothesis():
        async for db in get_db():
            service = ValidationService(db)

            try:
                # Parse criteria JSON
                success_criteria = json.loads(criteria)

                hypothesis_data = {
                    "title": title,
                    "hypothesis_statement": statement,
                    "assumption": assumption,
                    "expected_outcome": outcome,
                    "success_criteria": success_criteria,
                    "category": category,
                    "priority": priority,
                    "validation_method": method,
                }

                hypothesis = await service.create_hypothesis_from_idea(idea_id, hypothesis_data)

                console.print(f"[green]✅ Created hypothesis {hypothesis.id}[/green]")
                console.print(f"[dim]Title: {hypothesis.title}[/dim]")
                console.print(f"[dim]Category: {hypothesis.category} | Priority: {hypothesis.priority}[/dim]")

            except json.JSONDecodeError:
                console.print("[red]❌ Invalid JSON for success criteria[/red]")
            except Exception as e:
                console.print(f"[red]❌ Hypothesis creation failed: {e}[/red]")

    asyncio.run(_create_hypothesis())


@validation.command("create-experiment")
@click.argument("hypothesis_id", type=int)
@click.option("--title", required=True, help="Experiment title")
@click.option("--type", required=True, help="Experiment type (survey, prototype, landing_page, etc.)")
@click.option("--description", required=True, help="Experiment description")
@click.option("--sample-size", required=True, type=int, help="Target sample size")
@click.option("--primary-metric", required=True, help="Primary success metric")
@click.option("--methodology", required=True, help="Methodology (JSON string)")
@click.option("--baseline", type=float, help="Baseline value")
@click.option("--target", type=float, help="Target value")
@click.option("--cost", type=float, help="Estimated cost")
def create_experiment(
    hypothesis_id: int,
    title: str,
    type: str,
    description: str,
    sample_size: int,
    primary_metric: str,
    methodology: str,
    baseline: float,
    target: float,
    cost: float
):
    """Create a validation experiment."""
    import json

    async def _create_experiment():
        async for db in get_db():
            service = ValidationService(db)

            try:
                # Parse methodology JSON
                experiment_methodology = json.loads(methodology)

                experiment_data = {
                    "title": title,
                    "experiment_type": type,
                    "description": description,
                    "target_sample_size": sample_size,
                    "primary_metric": primary_metric,
                    "methodology": experiment_methodology,
                    "baseline_value": baseline,
                    "target_value": target,
                    "estimated_cost": cost,
                }

                experiment = await service.create_validation_experiment(hypothesis_id, experiment_data)

                console.print(f"[green]✅ Created experiment {experiment.id}[/green]")
                console.print(f"[dim]Title: {experiment.title}[/dim]")
                console.print(f"[dim]Type: {experiment.experiment_type} | Sample Size: {experiment.target_sample_size}[/dim]")

            except json.JSONDecodeError:
                console.print("[red]❌ Invalid JSON for methodology[/red]")
            except Exception as e:
                console.print(f"[red]❌ Experiment creation failed: {e}[/red]")

    asyncio.run(_create_experiment())


@validation.command("record-result")
@click.argument("experiment_id", type=int)
@click.option("--type", required=True, type=click.Choice(["quantitative", "qualitative", "mixed"]), help="Result type")
@click.option("--source", required=True, help="Data source (survey_response, user_feedback, etc.)")
@click.option("--metric-name", help="Metric name (for quantitative)")
@click.option("--metric-value", type=float, help="Metric value (for quantitative)")
@click.option("--metric-unit", help="Metric unit (percentage, count, etc.)")
@click.option("--qualitative-data", help="Qualitative data (JSON string)")
@click.option("--sentiment", type=float, help="Sentiment score (-1.0 to 1.0)")
@click.option("--confidence-low", type=float, help="Confidence interval low")
@click.option("--confidence-high", type=float, help="Confidence interval high")
@click.option("--notes", help="Analyst notes")
def record_experiment_result(
    experiment_id: int,
    type: str,
    source: str,
    metric_name: str,
    metric_value: float,
    metric_unit: str,
    qualitative_data: str,
    sentiment: float,
    confidence_low: float,
    confidence_high: float,
    notes: str
):
    """Record a result for a validation experiment."""
    import json

    async def _record_result():
        async for db in get_db():
            service = ValidationService(db)

            try:
                result_data = {
                    "result_type": type,
                    "data_source": source,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metric_unit": metric_unit,
                    "sentiment_score": sentiment,
                    "confidence_interval_low": confidence_low,
                    "confidence_interval_high": confidence_high,
                    "analyst_notes": notes,
                }

                # Parse qualitative data if provided
                if qualitative_data:
                    try:
                        result_data["qualitative_data"] = json.loads(qualitative_data)
                    except json.JSONDecodeError:
                        console.print("[yellow]⚠️  Could not parse qualitative data as JSON, storing as text[/yellow]")
                        result_data["qualitative_data"] = qualitative_data

                result = await service.record_experiment_result(experiment_id, result_data)

                console.print(f"[green]✅ Recorded result for experiment {experiment_id}[/green]")
                if metric_name and metric_value is not None:
                    console.print(f"[dim]Metric: {metric_name} = {metric_value} {metric_unit or ''}[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Result recording failed: {e}[/red]")

    asyncio.run(_record_result())


@validation.command("update-status")
@click.argument("hypothesis_id", type=int)
@click.option("--status", required=True, type=click.Choice(["proposed", "testing", "validated", "invalidated", "paused"]), help="New status")
@click.option("--score", type=float, help="Validation score (0.0-1.0)")
@click.option("--findings", help="Key findings (JSON array string)")
def update_hypothesis_status(hypothesis_id: int, status: str, score: float, findings: str):
    """Update hypothesis status and validation results."""
    import json

    async def _update_status():
        async for db in get_db():
            service = ValidationService(db)

            try:
                key_findings = None
                if findings:
                    key_findings = json.loads(findings)
                    if not isinstance(key_findings, list):
                        raise ValueError("Findings must be a JSON array")

                hypothesis = await service.update_hypothesis_status(
                    hypothesis_id, status, score, key_findings
                )

                console.print(f"[green]✅ Updated hypothesis {hypothesis_id}[/green]")
                console.print(f"[dim]Status: {hypothesis.status}[/dim]")
                if hypothesis.validation_score is not None:
                    console.print(f"[dim]Validation Score: {hypothesis.validation_score:.2%}[/dim]")

            except json.JSONDecodeError:
                console.print("[red]❌ Invalid JSON for key findings[/red]")
            except Exception as e:
                console.print(f"[red]❌ Status update failed: {e}[/red]")

    asyncio.run(_update_status())


@validation.command("summary")
@click.argument("hypothesis_id", type=int)
def show_validation_summary(hypothesis_id: int):
    """Show comprehensive validation summary for a hypothesis."""
    async def _show_summary():
        async for db in get_db():
            service = ValidationService(db)

            try:
                summary = await service.get_hypothesis_validation_summary(hypothesis_id)

                hypothesis_data = summary["hypothesis"]
                console.print(f"[bold green]📊 Validation Summary for Hypothesis {hypothesis_id}[/bold green]")
                console.print(f"[bold]{hypothesis_data['title']}[/bold]")
                console.print(f"[dim]{hypothesis_data['statement']}[/dim]")
                console.print(f"Status: {hypothesis_data['status']} | Category: {hypothesis_data['category']}")
                if hypothesis_data['validation_score'] is not None:
                    console.print(f"Validation Score: {hypothesis_data['validation_score']:.2%}")

                # Experiments summary
                exp_data = summary["experiments"]
                console.print(f"\n[bold]Experiments:[/bold] {exp_data['total']} total")
                console.print(f"• Completed: {exp_data['completed']}")
                console.print(f"• Running: {exp_data['running']}")
                console.print(f"• Planned: {exp_data['planned']}")

                # Results summary
                results = summary["results_summary"]
                if results["overall_confidence"] > 0:
                    console.print(f"\n[bold]Validation Results:[/bold]")
                    console.print(f"Overall Confidence: {results['overall_confidence']:.2%}")
                    console.print(f"Supporting Evidence: {results['supporting_evidence']}")
                    console.print(f"Contradicting Evidence: {results['contradicting_evidence']}")

                    # Key metrics
                    if results["key_metrics"]:
                        console.print("\n[bold]Key Metrics:[/bold]")
                        for metric, data in results["key_metrics"].items():
                            console.print(f"• {metric}: {data['average']:.2f} (n={data['count']})")

                # Recommendations
                recommendations = summary["recommendations"]
                if recommendations:
                    console.print(f"\n[bold]Recommendations:[/bold]")
                    for rec in recommendations:
                        console.print(f"• {rec}")

            except Exception as e:
                console.print(f"[red]❌ Summary retrieval failed: {e}[/red]")

    asyncio.run(_show_summary())


@validation.command("overview")
@click.argument("company_id", type=int)
def show_company_validation_overview(company_id: int):
    """Show validation overview for a company."""
    async def _show_overview():
        from app.api.v1.endpoints.validation import get_company_validation_overview
        from fastapi import Depends
        from app.db.session import get_db

        async for db in get_db():
            try:
                # Call the API endpoint function directly
                overview = await get_company_validation_overview(company_id, db)

                console.print(f"[bold green]📋 Validation Overview for Company {company_id}[/bold green]")

                # Summary stats
                console.print(f"[bold]Summary:[/bold] {overview['total_hypotheses']} hypotheses")

                # Status breakdown
                status_data = overview["status_breakdown"]
                if status_data:
                    console.print("\n[bold]Status Breakdown:[/bold]")
                    for status, count in status_data.items():
                        console.print(f"• {status.title()}: {count}")

                # Category breakdown
                cat_data = overview["category_breakdown"]
                if cat_data:
                    console.print("\n[bold]Category Breakdown:[/bold]")
                    for category, count in cat_data.items():
                        console.print(f"• {category.title()}: {count}")

                # Priority breakdown
                pri_data = overview["priority_breakdown"]
                if pri_data:
                    console.print("\n[bold]Priority Breakdown:[/bold]")
                    for priority, count in pri_data.items():
                        console.print(f"• {priority.title()}: {count}")

                # Top hypotheses
                hypotheses = overview["hypotheses"][:5]  # Show top 5
                if hypotheses:
                    console.print(f"\n[bold]Recent Hypotheses:[/bold]")
                    for hyp in hypotheses:
                        score = f" ({hyp['validation_score']:.1%})" if hyp['validation_score'] else ""
                        console.print(f"• [{hyp['status']}] {hyp['title'][:60]}{score}")

            except Exception as e:
                console.print(f"[red]❌ Overview retrieval failed: {e}[/red]")

    asyncio.run(_show_overview())


@cli.group()
def reporting():
    """Generate reports and analytics."""
    pass


@reporting.command("dashboard")
def show_dashboard():
    """Show the main dashboard in the terminal."""
    async def _show_dashboard():
        async for db in get_db():
            service = ReportingService(db)

            try:
                data = await service.get_dashboard_data()

                console.print(f"[bold green]📊 Acquisitor Dashboard[/bold green]")
                console.print("=" * 50)

                # Summary
                summary = data.get("summary", {})
                console.print(f"\n[bold]System Overview:[/bold]")
                console.print(f"• Companies tracked: {summary.get('companies', 0)}")
                console.print(f"• Pain points identified: {summary.get('pain_points', 0)}")
                console.print(f"• Product ideas generated: {summary.get('product_ideas', 0)}")
                console.print(f"• Hypotheses created: {summary.get('hypotheses', 0)}")

                # Top insights
                insights = data.get("top_insights", [])
                if insights:
                    console.print(f"\n[bold]Key Insights:[/bold]")
                    for insight in insights:
                        console.print(f"• {insight}")

                # Validation pipeline
                validation_pipeline = data.get("validation_pipeline", {})
                hyp_status = validation_pipeline.get("hypotheses_by_status", {})
                exp_status = validation_pipeline.get("experiments_by_status", {})

                if hyp_status:
                    console.print(f"\n[bold]Validation Pipeline:[/bold]")
                    console.print("Hypotheses:")
                    for status, count in hyp_status.items():
                        console.print(f"  • {status.title()}: {count}")

                    console.print("Experiments:")
                    for status, count in exp_status.items():
                        console.print(f"  • {status.title()}: {count}")

                # Recent activity
                recent_activity = data.get("recent_activity", [])
                if recent_activity:
                    console.print(f"\n[bold]Recent Activity:[/bold]")
                    for activity in recent_activity[:5]:
                        timestamp = activity.get("timestamp", "")[:19]
                        console.print(f"• [{timestamp}] {activity.get('description', '')}")

                console.print(f"\n[dim]💡 Tip: Use 'acquisitor reporting dashboard --json' for JSON data, or build Next.js frontend[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Dashboard generation failed: {e}[/red]")

    asyncio.run(_show_dashboard())


@reporting.command("company")
@click.argument("company_id", type=int)
def show_company_report(company_id: int):
    """Show detailed report for a company."""
    async def _show_company_report():
        async for db in get_db():
            service = ReportingService(db)

            try:
                report = await service.get_company_report(company_id)

                company = report.get("company", {})
                statistics = report.get("statistics", {})
                pain_analysis = report.get("pain_point_analysis", {})
                ideation_analysis = report.get("ideation_analysis", {})

                console.print(f"[bold green]📋 Company Report: {company.get('name', '')}[/bold green]")
                console.print(f"[dim]{company.get('domain', '')} • {company.get('industry', '')}[/dim]")
                console.print("=" * 60)

                # Statistics
                console.print(f"\n[bold]Statistics:[/bold]")
                console.print(f"• Pain Points: {statistics.get('pain_points_count', 0)}")
                console.print(f"• Product Ideas: {statistics.get('product_ideas_count', 0)}")
                console.print(f"• Hypotheses: {statistics.get('hypotheses_count', 0)}")

                # Pain point insights
                if pain_analysis.get("total", 0) > 0:
                    console.print(f"\n[bold]Pain Point Analysis:[/bold]")
                    avg_severity = pain_analysis.get("average_severity", 0)
                    console.print(f"• Average severity: {avg_severity:.1f}/10")

                    severity_dist = pain_analysis.get("by_severity", {})
                    if severity_dist:
                        console.print("• Severity breakdown:")
                        for level, count in severity_dist.items():
                            console.print(f"  - {level.title()}: {count}")

                    insights = pain_analysis.get("insights", [])
                    if insights:
                        console.print("• Key insights:")
                        for insight in insights:
                            console.print(f"  - {insight}")

                # Product ideation insights
                if ideation_analysis.get("total", 0) > 0:
                    console.print(f"\n[bold]Product Ideation:[/bold]")
                    avg_fit = ideation_analysis.get("average_acquisition_fit", 0)
                    console.print(f"• Average acquisition fit: {avg_fit:.1%}")

                    top_ideas = ideation_analysis.get("top_ideas", [])
                    if top_ideas:
                        console.print("• Top opportunities:")
                        for i, idea in enumerate(top_ideas[:3], 1):
                            title = idea.get("title", "")
                            fit = idea.get("acquisition_fit_score", 0)
                            console.print(f"  {i}. {title[:50]}... ({fit:.1%} fit)")

                    insights = ideation_analysis.get("insights", [])
                    if insights:
                        console.print("• Insights:")
                        for insight in insights:
                            console.print(f"  - {insight}")

                console.print(f"\n[dim]💡 Tip: Visit http://localhost:8000/reporting/companies/{company_id}/report for the full web report[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Company report generation failed: {e}[/red]")

    asyncio.run(_show_company_report())


@reporting.command("validation")
def show_validation_report():
    """Show validation pipeline report."""
    async def _show_validation_report():
        async for db in get_db():
            service = ReportingService(db)

            try:
                report = await service.get_validation_report()

                console.print(f"[bold green]🔬 Validation Pipeline Report[/bold green]")
                console.print("=" * 50)

                # Success rates
                success_rates = report.get("success_rates", {})
                console.print(f"\n[bold]Success Metrics:[/bold]")
                console.print(f"• Validation success rate: {success_rates.get('success_rate', 0):.1%}")
                console.print(f"• Total validated: {success_rates.get('total_validated', 0)}")
                console.print(f"• Average validation score: {success_rates.get('average_validation_score', 0):.2f}")

                # Hypothesis status
                hypothesis_status = report.get("hypothesis_status", {})
                if hypothesis_status:
                    console.print(f"\n[bold]Hypothesis Status:[/bold]")
                    for status, count in hypothesis_status.items():
                        console.print(f"• {status.title()}: {count}")

                # Experiment status
                experiment_status = report.get("experiment_status", {})
                if experiment_status:
                    console.print(f"\n[bold]Experiment Status:[/bold]")
                    for status, count in experiment_status.items():
                        console.print(f"• {status.title()}: {count}")

                # Recent results
                recent_results = report.get("recent_results", [])
                if recent_results:
                    console.print(f"\n[bold]Recent Validation Results:[/bold]")
                    for result in recent_results[:5]:
                        status = result.get("status", "")
                        score = result.get("validation_score", 0)
                        title = result.get("title", "")[:40]
                        score_str = f" ({score:.1f})" if score else ""
                        console.print(f"• [{status}] {title}...{score_str}")

                console.print(f"\n[dim]💡 Tip: Visit http://localhost:8000/reporting/validation/report for the full web report[/dim]")

            except Exception as e:
                console.print(f"[red]❌ Validation report generation failed: {e}[/red]")

    asyncio.run(_show_validation_report())


@cli.command()
def server():
    """Start the Acquisitor web server."""
    import uvicorn
    from app.main import app

    console.print("[green]🚀 Starting Acquisitor server...[/green]")
    console.print(f"[dim]API docs: http://localhost:8000/docs[/dim]")
    console.print(f"[dim]Health check: http://localhost:8000/health[/dim]")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
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


if __name__ == "__main__":
    cli()
