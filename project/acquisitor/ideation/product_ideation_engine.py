"""AI-powered product ideation engine for generating relative product ideas."""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AnalysisError
from app.models.pain_point import PainPoint
from app.models.product_idea import ProductIdea


class ProductIdeationEngine:
    """Generates relative product ideas based on pain points."""

    def __init__(self, db: AsyncSession):
        """Initialize product ideation engine."""
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Ideation templates by pain point category
        self.ideation_templates = {
            'frustration': [
                "A simplified {solution} that eliminates {pain} through intelligent automation",
                "A {solution} focused solely on solving {pain} with minimal complexity",
                "An alternative {solution} that makes {pain} disappear through better design",
            ],
            'difficulty': [
                "A guided {solution} that makes {pain} intuitive and effortless",
                "A smart {solution} that anticipates and prevents {pain}",
                "A streamlined {solution} where {pain} is handled automatically",
            ],
            'problems': [
                "A robust {solution} that fundamentally solves {pain} at its source",
                "A reliable {solution} that prevents {pain} from occurring",
                "A comprehensive {solution} that addresses all aspects of {pain}",
            ],
            'limitations': [
                "An enhanced {solution} that removes {pain} through expanded capabilities",
                "A complete {solution} that fills the gaps causing {pain}",
                "A powerful {solution} that overcomes {pain} with advanced features",
            ],
            'inefficiency': [
                "A fast and efficient {solution} that eliminates {pain} through optimization",
                "An automated {solution} that removes {pain} from the workflow",
                "A streamlined {solution} where {pain} is reduced to a single click",
            ],
            'cost_issues': [
                "An affordable {solution} that provides {pain} relief at a fraction of the cost",
                "A cost-effective {solution} that solves {pain} without breaking the bank",
                "A value-driven {solution} that makes {pain} resolution accessible",
            ],
            'missing_features': [
                "A feature-complete {solution} that includes everything needed to avoid {pain}",
                "An enhanced {solution} that adds the missing pieces to eliminate {pain}",
                "A comprehensive {solution} that covers all use cases without {pain}",
            ],
            'usability_issues': [
                "An intuitive {solution} that makes {pain} impossible through better UX",
                "A user-friendly {solution} that guides users away from {pain}",
                "A simple {solution} where {pain} is replaced with delightful experiences",
            ],
        }

        # Product categories for ideation
        self.product_categories = [
            'tool', 'platform', 'service', 'app', 'extension',
            'integration', 'api', 'library', 'framework', 'system'
        ]

    async def generate_product_ideas(self, company_id: int) -> List[ProductIdea]:
        """Generate relative product ideas for a company based on its pain points."""
        try:
            # Get pain points for the company
            pain_points = await self._get_company_pain_points(company_id)

            if not pain_points:
                self.logger.info(f"No pain points found for company {company_id}")
                return []

            self.logger.info(f"Generating product ideas from {len(pain_points)} pain points")

            # Generate ideas for each pain point
            all_ideas = []
            for pain_point in pain_points:
                ideas = await self._generate_ideas_for_pain_point(pain_point)
                all_ideas.extend(ideas)

            # Deduplicate and rank ideas
            unique_ideas = await self._deduplicate_and_rank_ideas(all_ideas)

            # Save ideas to database
            saved_ideas = await self._save_product_ideas(company_id, unique_ideas)

            # Update company statistics
            await self._update_company_idea_count(company_id, len(saved_ideas))

            self.logger.info(f"Generated {len(saved_ideas)} product ideas for company {company_id}")
            return saved_ideas

        except Exception as e:
            self.logger.error(f"Failed to generate product ideas for company {company_id}: {e}")
            raise AnalysisError("ideation", f"Product ideation failed: {e}")

    async def _get_company_pain_points(self, company_id: int) -> List[PainPoint]:
        """Get pain points for a company, prioritized by severity."""
        from sqlalchemy import select

        query = select(PainPoint).where(PainPoint.company_id == company_id).order_by(PainPoint.severity.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _generate_ideas_for_pain_point(self, pain_point: PainPoint) -> List[Dict]:
        """Generate product ideas for a specific pain point."""
        ideas = []

        # Get ideation templates for this category
        category = pain_point.category
        templates = self.ideation_templates.get(category, self.ideation_templates['problems'])

        # Extract key elements from pain point
        pain_description = self._extract_pain_description(pain_point)
        solution_domain = self._infer_solution_domain(pain_point)

        # Generate ideas using templates
        for template in templates:
            for product_category in self.product_categories[:3]:  # Limit categories
                idea_data = self._create_idea_from_template(
                    template, pain_point, pain_description, solution_domain, product_category
                )
                if idea_data:
                    ideas.append(idea_data)

        # Generate additional custom ideas based on pain point content
        custom_ideas = self._generate_custom_ideas(pain_point)
        ideas.extend(custom_ideas)

        return ideas

    def _extract_pain_description(self, pain_point: PainPoint) -> str:
        """Extract a concise description of the pain from the pain point."""
        description = pain_point.description or pain_point.title

        # Try to extract the core pain
        pain_indicators = [
            'frustrated', 'annoying', 'difficult', 'problem', 'issue',
            'slow', 'complicated', 'missing', 'broken', 'expensive'
        ]

        for indicator in pain_indicators:
            if indicator in description.lower():
                # Extract sentence containing the indicator
                sentences = description.split('.')
                for sentence in sentences:
                    if indicator in sentence.lower():
                        return sentence.strip()

        # Fallback to first sentence
        first_sentence = description.split('.')[0].strip()
        return first_sentence if len(first_sentence) < 100 else first_sentence[:97] + '...'

    def _infer_solution_domain(self, pain_point: PainPoint) -> str:
        """Infer the domain/area where a solution would fit."""
        content = (pain_point.title + " " + (pain_point.description or "")).lower()

        # Domain mappings based on keywords
        domain_mappings = {
            'workflow': ['workflow', 'process', 'task', 'automation'],
            'collaboration': ['team', 'collaboration', 'sharing', 'communication'],
            'productivity': ['productivity', 'efficiency', 'time', 'fast'],
            'design': ['design', 'ui', 'ux', 'interface', 'visual'],
            'development': ['code', 'development', 'api', 'integration'],
            'data': ['data', 'analytics', 'reporting', 'insights'],
            'content': ['content', 'writing', 'creation', 'media'],
            'management': ['management', 'organization', 'planning'],
        }

        for domain, keywords in domain_mappings.items():
            if any(keyword in content for keyword in keywords):
                return domain

        return 'productivity'  # Default domain

    def _create_idea_from_template(
        self,
        template: str,
        pain_point: PainPoint,
        pain_description: str,
        solution_domain: str,
        product_category: str
    ) -> Optional[Dict]:
        """Create a product idea from a template."""
        try:
            # Fill template placeholders
            title = template.format(
                solution=f"{solution_domain} {product_category}",
                pain=pain_description.lower()
            )

            # Capitalize first letter
            title = title[0].upper() + title[1:]

            # Generate description
            description = self._generate_idea_description(title, pain_point)

            # Calculate acquisition potential
            acquisition_potential = self._calculate_acquisition_potential(pain_point, product_category)

            # Generate features and other details
            key_features = self._generate_key_features(pain_point, product_category)
            target_users = self._infer_target_users(pain_point)

            return {
                'title': title,
                'description': description,
                'category': product_category,
                'target_users': target_users,
                'key_features': key_features,
                'value_proposition': self._generate_value_proposition(title, pain_point),
                'acquisition_fit_score': acquisition_potential,
                'technical_complexity': self._estimate_technical_complexity(product_category),
                'development_effort': self._estimate_development_effort(pain_point.severity),
                'mvp_features': key_features[:3],  # First 3 features as MVP
                'pain_point_id': pain_point.id,
                'generated_from_pain': pain_description,
            }

        except Exception as e:
            self.logger.warning(f"Failed to create idea from template '{template}': {e}")
            return None

    def _generate_idea_description(self, title: str, pain_point: PainPoint) -> str:
        """Generate a detailed description for the product idea."""
        base_description = f"{title}. This solution addresses the pain point: '{pain_point.title}'"

        # Add context based on pain point severity
        if pain_point.severity > 7.0:
            base_description += " by solving a critical user frustration that affects many customers."
        elif pain_point.severity > 5.0:
            base_description += " by resolving a significant usability issue that impacts user satisfaction."
        else:
            base_description += " by improving upon a common user experience challenge."

        return base_description

    def _calculate_acquisition_potential(self, pain_point: PainPoint, product_category: str) -> float:
        """Calculate how attractive this idea would be for acquisition."""
        base_score = 0.5

        # Boost for higher severity pain points
        base_score += (pain_point.severity / 10.0) * 0.3

        # Boost for B2B products (more likely to be acquired)
        if product_category in ['platform', 'service', 'api', 'integration']:
            base_score += 0.2

        # Boost for enterprise-focused solutions
        if 'enterprise' in pain_point.title.lower() or 'team' in pain_point.title.lower():
            base_score += 0.1

        return min(base_score, 1.0)

    def _generate_key_features(self, pain_point: PainPoint, product_category: str) -> List[str]:
        """Generate key features for the product idea."""
        features = []

        # Base features based on category
        category_features = {
            'tool': ['Intuitive interface', 'Fast setup', 'Export capabilities'],
            'platform': ['Multi-user support', 'API access', 'Custom integrations'],
            'service': ['Automated processing', 'Real-time updates', 'SLA guarantees'],
            'app': ['Mobile responsive', 'Offline mode', 'Cross-platform sync'],
            'extension': ['Seamless integration', 'Zero configuration', 'Plugin architecture'],
            'integration': ['RESTful APIs', 'Webhook support', 'OAuth authentication'],
            'api': ['Comprehensive documentation', 'Rate limiting', 'SDK support'],
            'library': ['Multiple language support', 'Type definitions', 'Comprehensive tests'],
        }

        features.extend(category_features.get(product_category, ['Core functionality', 'User-friendly design']))

        # Add pain-specific features
        if 'slow' in pain_point.title.lower():
            features.append('Lightning-fast performance')
        if 'complicated' in pain_point.title.lower():
            features.append('Simplified user experience')
        if 'expensive' in pain_point.title.lower():
            features.append('Cost-effective solution')

        return features

    def _infer_target_users(self, pain_point: PainPoint) -> List[str]:
        """Infer target user groups for the product idea."""
        users = ['users']  # Default

        content = pain_point.title + " " + (pain_point.description or "")

        if 'team' in content.lower() or 'collaboration' in content.lower():
            users.append('teams')
        if 'enterprise' in content.lower() or 'company' in content.lower():
            users.append('enterprises')
        if 'developer' in content.lower() or 'api' in content.lower():
            users.append('developers')
        if 'designer' in content.lower() or 'creative' in content.lower():
            users.append('designers')
        if 'manager' in content.lower() or 'admin' in content.lower():
            users.append('managers')

        return list(set(users))

    def _generate_value_proposition(self, title: str, pain_point: PainPoint) -> str:
        """Generate a value proposition for the product idea."""
        return f"Solves the critical problem of {pain_point.title.lower()} with a focused, effective solution that delights users and creates competitive advantage."

    def _estimate_technical_complexity(self, product_category: str) -> str:
        """Estimate technical complexity of building the product."""
        complexity_map = {
            'tool': 'low',
            'app': 'medium',
            'extension': 'low',
            'library': 'medium',
            'api': 'medium',
            'service': 'high',
            'platform': 'high',
            'integration': 'medium',
        }
        return complexity_map.get(product_category, 'medium')

    def _estimate_development_effort(self, pain_severity: float) -> str:
        """Estimate development effort based on pain point severity."""
        if pain_severity > 8.0:
            return '3-6 months'
        elif pain_severity > 6.0:
            return '2-4 months'
        elif pain_severity > 4.0:
            return '1-3 months'
        else:
            return '2-4 weeks'

    def _generate_custom_ideas(self, pain_point: PainPoint) -> List[Dict]:
        """Generate custom ideas based on specific pain point content."""
        custom_ideas = []

        # Look for specific patterns in pain point content
        content = (pain_point.title + " " + (pain_point.description or "")).lower()

        # Integration-related pain points
        if 'integration' in content or 'connect' in content:
            custom_ideas.append({
                'title': f"Seamless integration solution that eliminates {pain_point.title.lower()}",
                'description': f"A robust integration platform that solves {pain_point.title} through automated connections and unified workflows.",
                'category': 'integration',
                'target_users': ['developers', 'teams'],
                'key_features': ['Auto-discovery', 'Unified API', 'Error handling', 'Monitoring'],
                'value_proposition': f"Finally, a solution that makes integrations painless and reliable.",
                'acquisition_fit_score': 0.8,
                'technical_complexity': 'high',
                'development_effort': '3-6 months',
                'mvp_features': ['Basic integration', 'API client', 'Error handling'],
                'pain_point_id': pain_point.id,
                'generated_from_pain': self._extract_pain_description(pain_point),
            })

        # Performance-related pain points
        if 'slow' in content or 'performance' in content:
            custom_ideas.append({
                'title': f"High-performance solution that eliminates {pain_point.title.lower()}",
                'description': f"A lightning-fast alternative that solves {pain_point.title} through advanced optimization and smart caching.",
                'category': 'tool',
                'target_users': ['users', 'teams'],
                'key_features': ['Performance monitoring', 'Auto-optimization', 'Caching layer', 'Parallel processing'],
                'value_proposition': f"Experience blazing-fast performance without the usual compromises.",
                'acquisition_fit_score': 0.7,
                'technical_complexity': 'medium',
                'development_effort': '2-4 months',
                'mvp_features': ['Basic optimization', 'Performance metrics', 'Caching'],
                'pain_point_id': pain_point.id,
                'generated_from_pain': self._extract_pain_description(pain_point),
            })

        return custom_ideas

    async def _deduplicate_and_rank_ideas(self, ideas: List[Dict]) -> List[Dict]:
        """Deduplicate similar ideas and rank them by acquisition potential."""
        if not ideas:
            return []

        # Simple deduplication based on title similarity
        unique_ideas = []
        used_titles = set()

        for idea in ideas:
            title_key = idea['title'].lower()[:50]  # First 50 chars as key

            if title_key not in used_titles:
                unique_ideas.append(idea)
                used_titles.add(title_key)

        # Rank by acquisition potential
        ranked_ideas = sorted(
            unique_ideas,
            key=lambda x: x.get('acquisition_fit_score', 0),
            reverse=True
        )

        return ranked_ideas[:20]  # Limit to top 20 ideas

    async def _save_product_ideas(self, company_id: int, ideas: List[Dict]) -> List[ProductIdea]:
        """Save product ideas to database."""
        saved_ideas = []

        for idea_data in ideas:
            # Create product idea object
            product_idea = ProductIdea(
                company_id=company_id,
                **idea_data
            )

            self.db.add(product_idea)
            saved_ideas.append(product_idea)

        await self.db.commit()

        # Refresh to get IDs
        for idea in saved_ideas:
            await self.db.refresh(idea)

        return saved_ideas

    async def _update_company_idea_count(self, company_id: int, idea_count: int):
        """Update company product ideas count."""
        from sqlalchemy import update

        stmt = (
            update("Company")
            .where("Company".id == company_id)
            .values(product_ideas_count=idea_count)
        )
        await self.db.execute(stmt)
        await self.db.commit()
