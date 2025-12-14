#!/usr/bin/env python3
"""
Acquisitor Complete Workflow Demo

This script demonstrates the complete Acquisitor workflow:
1. Add target companies
2. Collect research data
3. Analyze pain points
4. Generate product ideas
5. Create and validate hypotheses
6. Generate reports

Usage: python demo_workflow.py
"""

import asyncio
import json
from datetime import datetime

from app.db.session import get_db
from app.services.company_service import CompanyService
from app.services.analysis_service import AnalysisService
from app.services.validation_service import ValidationService
from app.services.reporting_service import ReportingService


async def demo_workflow():
    """Run the complete Acquisitor workflow demo."""
    print("🚀 Starting Acquisitor Complete Workflow Demo")
    print("=" * 60)

    async for db in get_db():
        company_service = CompanyService(db)
        analysis_service = AnalysisService(db)
        validation_service = ValidationService(db)
        reporting_service = ReportingService(db)

        try:
            # Step 1: Add target companies
            print("\n📌 Step 1: Adding Target Companies")
            print("-" * 40)

            companies_data = [
                {
                    "name": "Notion",
                    "domain": "notion.so",
                    "industry": "productivity",
                    "description": "All-in-one workspace for notes, docs, and projects"
                },
                {
                    "name": "Canva",
                    "domain": "canva.com",
                    "industry": "design",
                    "description": "Online design platform with drag-and-drop editor"
                }
            ]

            company_ids = []
            for company_data in companies_data:
                # Check if company already exists
                existing = await company_service.get_company_by_domain(company_data["domain"])
                if existing:
                    company_ids.append(existing.id)
                    print(f"✓ Using existing company: {existing.name}")
                else:
                    company = await company_service.create_company(company_data)
                    company_ids.append(company.id)
                    print(f"✓ Added company: {company.name}")

            # Step 2: Simulate research data collection
            print("\n📊 Step 2: Research Data Collection")
            print("-" * 40)

            # For demo purposes, we'll simulate research data
            # In real usage, this would be done via the CLI/API
            print("✓ Research collection would run here (simulated)")
            print("  - Reddit scraping: productivity pain points")
            print("  - GitHub issues: API limitations, bugs")
            print("  - Medium articles: industry insights")
            print("  - Twitter sentiment: user feedback")

            # Step 3: Run analysis pipeline
            print("\n🧠 Step 3: AI-Powered Analysis")
            print("-" * 40)

            for company_id in company_ids:
                print(f"\nAnalyzing company ID {company_id}...")
                try:
                    # Run full analysis (this would normally have research data)
                    analysis_result = await analysis_service.run_full_analysis(company_id)
                    print(f"✓ Analysis completed: {analysis_result['pain_points_found']} pain points, {analysis_result['product_ideas_generated']} ideas")

                    # Show top insights
                    summary = analysis_result.get('analysis_summary', {})
                    insights = summary.get('insights', [])
                    if insights:
                        print("  Key insights:")
                        for insight in insights[:2]:
                            print(f"    • {insight}")

                except Exception as e:
                    print(f"⚠️  Analysis failed (expected without research data): {e}")

            # Step 4: Create sample hypotheses
            print("\n🎯 Step 4: Hypothesis Creation")
            print("-" * 40)

            # Create sample hypothesis for Notion
            notion_id = company_ids[0]
            hypothesis_data = {
                "title": "Workspace collaboration barriers",
                "description": "Users struggle with real-time collaboration in complex workspaces",
                "hypothesis_statement": "If we build a superior real-time collaboration layer, then users will switch from Notion",
                "assumption": "Real-time collaboration is the biggest pain point for Notion users",
                "expected_outcome": "80% of surveyed users cite collaboration as top issue",
                "success_criteria": ["collaboration_ranking": ">3/5", "switching_intent": ">70%"],
                "category": "product",
                "priority": "high",
                "validation_method": "survey"
            }

            try:
                hypothesis = await validation_service.create_hypothesis_from_idea(1, hypothesis_data)  # Assuming idea ID 1 exists
                print(f"✓ Created hypothesis: {hypothesis.title}")
                hypothesis_id = hypothesis.id

                # Create validation experiment
                experiment_data = {
                    "title": "Notion User Collaboration Survey",
                    "experiment_type": "survey",
                    "description": "Survey 100 Notion users about collaboration pain points",
                    "target_sample_size": 100,
                    "primary_metric": "collaboration_importance",
                    "methodology": {
                        "platform": "surveymonkey",
                        "questions": ["collaboration ranking", "switching intent", "current tools"],
                        "demographics": ["user_type", "workspace_size"]
                    },
                    "estimated_cost": 500.0
                }

                experiment = await validation_service.create_validation_experiment(hypothesis_id, experiment_data)
                print(f"✓ Created experiment: {experiment.title}")

                # Simulate experiment result
                result_data = {
                    "result_type": "quantitative",
                    "data_source": "survey_response",
                    "metric_name": "collaboration_importance",
                    "metric_value": 4.2,
                    "metric_unit": "rating",
                    "confidence_interval_low": 3.8,
                    "confidence_interval_high": 4.6,
                    "analyst_notes": "Strong evidence that collaboration is a major pain point"
                }

                result = await validation_service.record_experiment_result(experiment.id, result_data)
                print(f"✓ Recorded experiment result: {result.metric_name} = {result.metric_value}")

                # Update hypothesis status
                await validation_service.update_hypothesis_status(
                    hypothesis_id,
                    "validated",
                    validation_score=0.85,
                    key_findings=["Collaboration rated 4.2/5", "70% express switching intent"]
                )
                print("✓ Updated hypothesis status to validated")

            except Exception as e:
                print(f"⚠️  Hypothesis creation failed (expected without product ideas): {e}")

            # Step 5: Generate reports
            print("\n📈 Step 5: Report Generation")
            print("-" * 40)

            # Dashboard data
            try:
                dashboard_data = await reporting_service.get_dashboard_data()
                summary = dashboard_data.get("summary", {})
                print("✓ Dashboard data generated:"                print(f"  - {summary.get('companies', 0)} companies")
                print(f"  - {summary.get('pain_points', 0)} pain points")
                print(f"  - {summary.get('product_ideas', 0)} ideas")
                print(f"  - {summary.get('hypotheses', 0)} hypotheses")
            except Exception as e:
                print(f"⚠️  Dashboard generation failed: {e}")

            # Company report
            try:
                for company_id in company_ids[:1]:  # Just first company for demo
                    report = await reporting_service.get_company_report(company_id)
                    company = report.get("company", {})
                    print(f"✓ Generated report for {company.get('name', 'Unknown Company')}")
            except Exception as e:
                print(f"⚠️  Company report failed: {e}")

            # Validation report
            try:
                validation_report = await reporting_service.get_validation_report()
                success_rates = validation_report.get("success_rates", {})
                print("✓ Validation report generated:"                print(f"  - Success rate: {success_rates.get('success_rate', 0):.1%}")
                print(f"  - Total validated: {success_rates.get('total_validated', 0)}")
            except Exception as e:
                print(f"⚠️  Validation report failed: {e}")

            # Step 6: Display next steps
            print("\n🎯 Step 6: Next Steps & Recommendations")
            print("-" * 40)

            print("1. 🔍 Research Collection:")
            print("   - Run: acquisitor companies research <company_id>")
            print("   - This collects real data from Reddit, GitHub, Medium, Twitter")

            print("\n2. 📊 Full Analysis:")
            print("   - Run: acquisitor analysis run <company_id>")
            print("   - AI analyzes pain points and generates product ideas")

            print("\n3. ✅ Validation Pipeline:")
            print("   - Create hypotheses: acquisitor validation create-hypothesis <idea_id>")
            print("   - Design experiments: acquisitor validation create-experiment <hypothesis_id>")
            print("   - Track results: acquisitor validation record-result <experiment_id>")

            print("\n4. 📈 Reporting:")
            print("   - Dashboard: acquisitor reporting dashboard")
            print("   - Company reports: acquisitor reporting company <company_id>")
            print("   - Validation status: acquisitor reporting validation")

            print("\n5. 🌐 Web Interface:")
            print("   - Start server: acquisitor server")
            print("   - Dashboard: http://localhost:8000/reporting/dashboard")
            print("   - API docs: http://localhost:8000/docs")

            print("\n💡 Pro Tips:")
            print("   - Focus on companies with 50+ pain points for best results")
            print("   - Look for 'critical' and 'high' severity pain points")
            print("   - Prioritize ideas with >70% acquisition fit scores")
            print("   - Validate assumptions with low-cost experiments first")

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🎯 Acquisitor: AI-Powered Relative Product Ideation")
    print("   Finding acquisition opportunities through pain point analysis")
    print()

    asyncio.run(demo_workflow())

    print("\n✨ Demo completed! Ready to find your next acquisition target?")
    print("   Run: acquisitor --help")
