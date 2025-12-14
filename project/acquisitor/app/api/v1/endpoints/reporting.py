"""Reporting API endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.reporting_service import ReportingService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard data as JSON."""
    reporting_service = ReportingService(db)

    try:
        return await reporting_service.get_dashboard_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")


@router.get("/companies/{company_id}/report")
async def get_company_report_data(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get company report data as JSON."""
    reporting_service = ReportingService(db)

    try:
        return await reporting_service.get_company_report(company_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Company report data retrieval failed: {str(e)}")


@router.get("/validation/report")
async def get_validation_report_data(
    db: AsyncSession = Depends(get_db),
):
    """Get validation pipeline report data as JSON."""
    reporting_service = ReportingService(db)

    try:
        return await reporting_service.get_validation_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation report data retrieval failed: {str(e)}")

    """Generate HTML for the dashboard."""
    summary = data.get("summary", {})
    recent_activity = data.get("recent_activity", [])
    top_insights = data.get("top_insights", [])
    validation_pipeline = data.get("validation_pipeline", {})

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Acquisitor Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <div class="min-h-screen">
            <!-- Header -->
            <header class="bg-white shadow">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex justify-between items-center py-6">
                        <h1 class="text-3xl font-bold text-gray-900">Acquisitor Dashboard</h1>
                        <span class="text-sm text-gray-500">Last updated: {summary.get('last_updated', '')[:19]}</span>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <!-- Summary Cards -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">C</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Companies</dt>
                                        <dd class="text-lg font-medium text-gray-900">{summary.get('companies', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">P</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Pain Points</dt>
                                        <dd class="text-lg font-medium text-gray-900">{summary.get('pain_points', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">I</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Product Ideas</dt>
                                        <dd class="text-lg font-medium text-gray-900">{summary.get('product_ideas', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">H</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Hypotheses</dt>
                                        <dd class="text-lg font-medium text-gray-900">{summary.get('hypotheses', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Recent Activity -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Activity</h3>
                            <div class="space-y-3">
    """

    for activity in recent_activity[:10]:
        activity_type = activity.get("type", "")
        icon_class = "text-blue-500" if "hypothesis" in activity_type else "text-green-500"
        html += f"""
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0">
                                        <div class="w-2 h-2 bg-{icon_class} rounded-full mt-2"></div>
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <p class="text-sm text-gray-900">{activity.get('description', '')}</p>
                                        <p class="text-xs text-gray-500">{activity.get('timestamp', '')[:19]}</p>
                                    </div>
                                </div>
        """

    html += """
                            </div>
                        </div>
                    </div>

                    <!-- Top Insights -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Key Insights</h3>
                            <div class="space-y-3">
    """

    for insight in top_insights:
        html += f"""
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0">
                                        <div class="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                                    </div>
                                    <div class="min-w-0 flex-1">
                                        <p class="text-sm text-gray-900">{insight}</p>
                                    </div>
                                </div>
        """

    html += """
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Validation Pipeline Status -->
                <div class="mt-8 bg-white shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Validation Pipeline</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    """

    # Hypotheses status
    hyp_status = validation_pipeline.get("hypotheses_by_status", {})
    html += """
                            <div>
                                <h4 class="text-md font-medium text-gray-900 mb-3">Hypotheses</h4>
                                <div class="space-y-2">
    """
    for status, count in hyp_status.items():
        html += f"""
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600 capitalize">{status}</span>
                                        <span class="text-sm font-medium text-gray-900">{count}</span>
                                    </div>
        """

    # Experiments status
    exp_status = validation_pipeline.get("experiments_by_status", {})
    html += """
                                </div>
                            </div>
                            <div>
                                <h4 class="text-md font-medium text-gray-900 mb-3">Experiments</h4>
                                <div class="space-y-2">
    """
    for status, count in exp_status.items():
        html += f"""
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600 capitalize">{status}</span>
                                        <span class="text-sm font-medium text-gray-900">{count}</span>
                                    </div>
        """

    html += """
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </body>
    </html>
    """

    return html


async def _generate_company_report_html(data: Dict) -> str:
    """Generate HTML for company report."""
    company = data.get("company", {})
    statistics = data.get("statistics", {})
    pain_analysis = data.get("pain_point_analysis", {})
    ideation_analysis = data.get("ideation_analysis", {})

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Company Report - {company.get('name', '')}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <div class="min-h-screen">
            <!-- Header -->
            <header class="bg-white shadow">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="py-6">
                        <h1 class="text-3xl font-bold text-gray-900">{company.get('name', '')} - Analysis Report</h1>
                        <p class="mt-1 text-sm text-gray-500">{company.get('domain', '')} • {company.get('industry', '')}</p>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <!-- Statistics -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-red-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">P</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Pain Points</dt>
                                        <dd class="text-lg font-medium text-gray-900">{statistics.get('pain_points_count', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">I</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Product Ideas</dt>
                                        <dd class="text-lg font-medium text-gray-900">{statistics.get('product_ideas_count', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">H</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Hypotheses</dt>
                                        <dd class="text-lg font-medium text-gray-900">{statistics.get('hypotheses_count', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Pain Point Analysis -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Pain Point Analysis</h3>
    """

    if pain_analysis.get("total", 0) > 0:
        # Severity breakdown
        severity = pain_analysis.get("by_severity", {})
        html += """
                            <div class="mb-4">
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Severity Distribution</h4>
                                <div class="space-y-2">
        """
        for level, count in severity.items():
            html += f"""
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600 capitalize">{level}</span>
                                        <span class="text-sm font-medium text-gray-900">{count}</span>
                                    </div>
            """

        # Category breakdown
        categories = pain_analysis.get("by_category", {})
        html += """
                                </div>
                            </div>
                            <div class="mb-4">
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Category Distribution</h4>
                                <div class="space-y-2">
        """
        for category, count in categories.items():
            html += f"""
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600 capitalize">{category.replace('_', ' ')}</span>
                                        <span class="text-sm font-medium text-gray-900">{count}</span>
                                    </div>
            """

        # Insights
        insights = pain_analysis.get("insights", [])
        if insights:
            html += """
                                </div>
                            </div>
                            <div>
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Key Insights</h4>
                                <ul class="list-disc list-inside space-y-1">
            """
            for insight in insights:
                html += f"""
                                    <li class="text-sm text-gray-600">{insight}</li>
                """
    else:
        html += """
                            <p class="text-sm text-gray-500">No pain points analyzed yet.</p>
        """

    html += """
                        </div>
                    </div>

                    <!-- Product Ideation Analysis -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Product Ideation</h3>
    """

    if ideation_analysis.get("total", 0) > 0:
        # Category breakdown
        categories = ideation_analysis.get("by_category", {})
        html += """
                            <div class="mb-4">
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Ideas by Category</h4>
                                <div class="space-y-2">
        """
        for category, count in categories.items():
            html += f"""
                                    <div class="flex justify-between items-center">
                                        <span class="text-sm text-gray-600 capitalize">{category}</span>
                                        <span class="text-sm font-medium text-gray-900">{count}</span>
                                    </div>
            """

        # Top ideas
        top_ideas = ideation_analysis.get("top_ideas", [])
        if top_ideas:
            html += """
                                </div>
                            </div>
                            <div>
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Top Acquisition Opportunities</h4>
                                <div class="space-y-3">
            """
            for idea in top_ideas:
                fit_score = idea.get("acquisition_fit_score", 0)
                html += f"""
                                    <div class="border border-gray-200 rounded-md p-3">
                                        <div class="flex justify-between items-start">
                                            <div class="flex-1">
                                                <h5 class="text-sm font-medium text-gray-900">{idea.get('title', '')}</h5>
                                                <p class="text-xs text-gray-500 mt-1">{idea.get('category', '')} • {', '.join(idea.get('target_users', []))}</p>
                                            </div>
                                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                {fit_score:.1%}
                                            </span>
                                        </div>
                                    </div>
                """

        # Insights
        insights = ideation_analysis.get("insights", [])
        if insights:
            html += """
                                </div>
                            </div>
                            <div class="mt-4">
                                <h4 class="text-sm font-medium text-gray-900 mb-2">Insights</h4>
                                <ul class="list-disc list-inside space-y-1">
            """
            for insight in insights:
                html += f"""
                                    <li class="text-sm text-gray-600">{insight}</li>
                """
    else:
        html += """
                            <p class="text-sm text-gray-500">No product ideas generated yet.</p>
        """

    html += """
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </body>
    </html>
    """

    return html


async def _generate_validation_report_html(data: Dict) -> str:
    """Generate HTML for validation report."""
    hypothesis_status = data.get("hypothesis_status", {})
    experiment_status = data.get("experiment_status", {})
    success_rates = data.get("success_rates", {})
    recent_results = data.get("recent_results", [])

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Validation Pipeline Report</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50">
        <div class="min-h-screen">
            <!-- Header -->
            <header class="bg-white shadow">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="py-6">
                        <h1 class="text-3xl font-bold text-gray-900">Validation Pipeline Report</h1>
                        <p class="mt-1 text-sm text-gray-500">Hypothesis testing and experiment tracking</p>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                <!-- Success Rates -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">✓</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Success Rate</dt>
                                        <dd class="text-lg font-medium text-gray-900">{success_rates.get('success_rate', 0):.1%}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">V</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Validated</dt>
                                        <dd class="text-lg font-medium text-gray-900">{success_rates.get('total_validated', 0)}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">S</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Avg Score</dt>
                                        <dd class="text-lg font-medium text-gray-900">{success_rates.get('average_validation_score', 0):.2f}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                                        <span class="text-white font-bold">E</span>
                                    </div>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Experiments</dt>
                                        <dd class="text-lg font-medium text-gray-900">{sum(experiment_status.values())}</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Hypothesis Status -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Hypothesis Status</h3>
                            <div class="space-y-3">
    """

    for status, count in hypothesis_status.items():
        status_color = {
            "proposed": "bg-gray-100 text-gray-800",
            "testing": "bg-blue-100 text-blue-800",
            "validated": "bg-green-100 text-green-800",
            "invalidated": "bg-red-100 text-red-800",
            "paused": "bg-yellow-100 text-yellow-800",
        }.get(status, "bg-gray-100 text-gray-800")

        html += f"""
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-gray-900 capitalize">{status}</span>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_color}">
                                        {count}
                                    </span>
                                </div>
        """

    html += """
                            </div>
                        </div>
                    </div>

                    <!-- Experiment Status -->
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Experiment Status</h3>
                            <div class="space-y-3">
    """

    for status, count in experiment_status.items():
        status_color = {
            "planned": "bg-gray-100 text-gray-800",
            "running": "bg-blue-100 text-blue-800",
            "completed": "bg-green-100 text-green-800",
            "cancelled": "bg-red-100 text-red-800",
        }.get(status, "bg-gray-100 text-gray-800")

        html += f"""
                                <div class="flex items-center justify-between">
                                    <span class="text-sm font-medium text-gray-900 capitalize">{status}</span>
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_color}">
                                        {count}
                                    </span>
                                </div>
        """

    html += """
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Validation Results -->
                <div class="mt-8 bg-white shadow rounded-lg">
                    <div class="px-4 py-5 sm:p-6">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Validation Results</h3>
    """

    if recent_results:
        html += """
                        <div class="overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-200">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hypothesis</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Validated</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
        """

        for result in recent_results:
            status_color = "text-green-600" if result.get("status") == "validated" else "text-red-600"
            html += f"""
                                    <tr>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{result.get('title', '')[:50]}...</td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {status_color} bg-current bg-opacity-10">
                                                {result.get('status', '').title()}
                                            </span>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {result.get('validation_score', 0):.2f if result.get('validation_score') else 'N/A'}
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {result.get('validated_at', '')[:10] if result.get('validated_at') else 'N/A'}
                                        </td>
                                    </tr>
            """

        html += """
                                </tbody>
                            </table>
                        </div>
        """
    else:
        html += """
                        <p class="text-sm text-gray-500">No validation results yet.</p>
        """

    html += """
                    </div>
                </div>
            </main>
        </div>
    </body>
    </html>
    """

    return html
