"""AI-powered pain point analyzer for research data."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AnalysisError
from app.models.pain_point import PainPoint
from app.models.research_data import ResearchData


class PainPointAnalyzer:
    """Analyzes research data to extract and categorize pain points."""

    def __init__(self, db: AsyncSession):
        """Initialize pain point analyzer."""
        self.db = db
        self.logger = logging.getLogger(__name__)

        # Pain point indicators
        self.pain_indicators = {
            'frustration': ['frustrated', 'annoying', 'irritating', 'painful', 'terrible'],
            'difficulty': ['difficult', 'hard', 'complicated', 'complex', 'challenging'],
            'problems': ['problem', 'issue', 'bug', 'broken', 'not working'],
            'limitations': ['limited', 'missing', 'lack of', 'no way to', 'impossible'],
            'inefficiency': ['slow', 'inefficient', 'waste of time', 'tedious', 'repetitive'],
            'cost_issues': ['expensive', 'costly', 'pricey', 'overpriced', 'waste of money'],
            'missing_features': ['missing', 'need', 'should have', 'wish', 'want'],
            'usability_issues': ['confusing', 'unclear', 'hard to use', 'not intuitive']
        }

        # Severity scoring
        self.severity_keywords = {
            'critical': ['unusable', 'broken', 'doesn\'t work', 'completely broken'],
            'high': ['very frustrating', 'extremely annoying', 'major issue', 'serious problem'],
            'medium': ['somewhat annoying', 'minor issue', 'could be better'],
            'low': ['slightly inconvenient', 'small issue', 'minor annoyance']
        }

    async def analyze_company_pain_points(self, company_id: int) -> List[PainPoint]:
        """Analyze all research data for a company and extract pain points."""
        try:
            # Get research data for company
            research_data = await self._get_company_research_data(company_id)

            if not research_data:
                self.logger.info(f"No research data found for company {company_id}")
                return []

            self.logger.info(f"Analyzing {len(research_data)} research items for pain points")

            # Extract pain points from each data item
            all_pain_points = []
            for data_item in research_data:
                pain_points = await self._extract_pain_points_from_data(data_item)
                all_pain_points.extend(pain_points)

            # Deduplicate and consolidate similar pain points
            consolidated_pain_points = await self._consolidate_pain_points(all_pain_points)

            # Save pain points to database
            saved_pain_points = await self._save_pain_points(company_id, consolidated_pain_points)

            self.logger.info(f"Extracted {len(saved_pain_points)} pain points for company {company_id}")
            return saved_pain_points

        except Exception as e:
            self.logger.error(f"Failed to analyze pain points for company {company_id}: {e}")
            raise AnalysisError("pain_point_analysis", f"Pain point analysis failed: {e}")

    async def _get_company_research_data(self, company_id: int) -> List[ResearchData]:
        """Get all research data for a company."""
        from sqlalchemy import select

        query = select(ResearchData).where(ResearchData.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _extract_pain_points_from_data(self, data_item: ResearchData) -> List[Dict]:
        """Extract pain points from a single research data item."""
        pain_points = []
        content = data_item.content or ""

        # Skip if content is too short
        if len(content) < 50:
            return pain_points

        # Look for pain point indicators
        for category, indicators in self.pain_indicators.items():
            for indicator in indicators:
                # Find sentences containing the indicator
                sentences = self._extract_sentences_with_keyword(content, indicator)
                for sentence in sentences:
                    pain_point = await self._analyze_pain_point_sentence(
                        sentence, category, data_item
                    )
                    if pain_point:
                        pain_points.append(pain_point)

        return pain_points

    def _extract_sentences_with_keyword(self, text: str, keyword: str) -> List[str]:
        """Extract sentences containing a specific keyword."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        # Find sentences with keyword
        matching_sentences = []
        for sentence in sentences:
            if keyword.lower() in sentence.lower() and len(sentence.strip()) > 20:
                matching_sentences.append(sentence.strip())

        return matching_sentences

    async def _analyze_pain_point_sentence(
        self, sentence: str, category: str, data_item: ResearchData
    ) -> Optional[Dict]:
        """Analyze a sentence to extract pain point information."""
        try:
            # Calculate severity
            severity = self._calculate_severity(sentence)

            # Calculate frequency (based on context and repetition)
            frequency = self._estimate_frequency(sentence, data_item)

            # Calculate impact
            impact = self._calculate_impact(severity, frequency)

            # Extract keywords
            keywords = self._extract_keywords(sentence)

            # Generate title and description
            title = self._generate_pain_point_title(sentence, category)
            description = sentence

            return {
                'title': title,
                'description': description,
                'category': category,
                'severity': severity,
                'frequency': frequency,
                'impact': impact,
                'source_type': data_item.source_type,
                'source_url': data_item.source_url,
                'source_title': data_item.source_title,
                'source_author': data_item.source_author,
                'source_date': data_item.source_date,
                'keywords': keywords,
                'evidence_links': [data_item.source_url] if data_item.source_url else [],
                'validation_score': self._calculate_validation_score(severity, data_item),
            }

        except Exception as e:
            self.logger.warning(f"Failed to analyze sentence '{sentence[:50]}...': {e}")
            return None

    def _calculate_severity(self, sentence: str) -> float:
        """Calculate pain point severity (1.0-10.0)."""
        severity_score = 5.0  # Default medium severity

        sentence_lower = sentence.lower()

        # Check severity keywords
        for level, keywords in self.severity_keywords.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    if level == 'critical':
                        severity_score = max(severity_score, 9.0)
                    elif level == 'high':
                        severity_score = max(severity_score, 7.0)
                    elif level == 'medium':
                        severity_score = max(severity_score, 5.0)
                    elif level == 'low':
                        severity_score = min(severity_score, 3.0)

        # Boost for multiple pain indicators
        pain_indicators_found = 0
        for indicators in self.pain_indicators.values():
            for indicator in indicators:
                if indicator in sentence_lower:
                    pain_indicators_found += 1

        if pain_indicators_found > 1:
            severity_score += min(pain_indicators_found * 0.5, 2.0)

        return min(severity_score, 10.0)

    def _estimate_frequency(self, sentence: str, data_item: ResearchData) -> str:
        """Estimate how frequently this pain point occurs."""
        sentence_lower = sentence.lower()

        # Check for frequency indicators
        if any(word in sentence_lower for word in ['always', 'constantly', 'every time', 'all the time']):
            return 'constant'
        elif any(word in sentence_lower for word in ['often', 'frequently', 'regularly', 'many times']):
            return 'frequent'
        elif any(word in sentence_lower for word in ['sometimes', 'occasionally', 'from time to time']):
            return 'occasional'
        else:
            # Default based on upvotes/engagement
            engagement = (getattr(data_item, 'upvotes', 0) or 0) + \
                        (getattr(data_item, 'comments_count', 0) or 0)
            if engagement > 50:
                return 'frequent'
            elif engagement > 10:
                return 'occasional'
            else:
                return 'rare'

    def _calculate_impact(self, severity: float, frequency: str) -> str:
        """Calculate business impact level."""
        # Simple impact calculation
        frequency_multiplier = {
            'constant': 1.0,
            'frequent': 0.8,
            'occasional': 0.5,
            'rare': 0.2
        }.get(frequency, 0.5)

        impact_score = severity * frequency_multiplier

        if impact_score >= 7.0:
            return 'critical'
        elif impact_score >= 5.0:
            return 'high'
        elif impact_score >= 3.0:
            return 'medium'
        else:
            return 'low'

    def _extract_keywords(self, sentence: str) -> List[str]:
        """Extract relevant keywords from the sentence."""
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b\w+\b', sentence.lower())

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]

        return keywords[:10]  # Limit keywords

    def _generate_pain_point_title(self, sentence: str, category: str) -> str:
        """Generate a concise title for the pain point."""
        # Try to extract the main issue
        sentence = sentence.strip()

        # Remove common prefixes
        prefixes_to_remove = ['i think', 'it would be', 'it\'s', 'i\'m', 'the problem is', 'the issue is']
        for prefix in prefixes_to_remove:
            if sentence.lower().startswith(prefix):
                sentence = sentence[len(prefix):].strip()

        # Take first meaningful part
        if len(sentence) > 80:
            # Find a good break point
            break_chars = ['.', ',', ';', ':']
            for char in break_chars:
                if char in sentence[:80]:
                    title = sentence[:sentence.find(char, 0, 80) + 1].strip()
                    break
            else:
                title = sentence[:77] + '...'
        else:
            title = sentence

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        return title

    def _calculate_validation_score(self, severity: float, data_item: ResearchData) -> float:
        """Calculate confidence score for this pain point."""
        base_score = 0.5

        # Boost for higher severity
        base_score += (severity / 10.0) * 0.2

        # Boost for engagement
        engagement = (getattr(data_item, 'upvotes', 0) or 0) + \
                    (getattr(data_item, 'comments_count', 0) or 0)
        if engagement > 0:
            base_score += min(engagement / 100.0, 0.2)

        # Boost for reputable sources
        reputable_sources = ['github', 'medium']
        if data_item.source_type in reputable_sources:
            base_score += 0.1

        return min(base_score, 1.0)

    async def _consolidate_pain_points(self, pain_points: List[Dict]) -> List[Dict]:
        """Consolidate similar pain points."""
        if not pain_points:
            return []

        consolidated = []
        used_indices = set()

        for i, pp1 in enumerate(pain_points):
            if i in used_indices:
                continue

            similar_points = [pp1]

            # Find similar pain points
            for j, pp2 in enumerate(pain_points[i+1:], i+1):
                if j in used_indices:
                    continue

                if self._are_pain_points_similar(pp1, pp2):
                    similar_points.append(pp2)
                    used_indices.add(j)

            # Consolidate similar points
            if len(similar_points) > 1:
                consolidated_pp = self._merge_similar_pain_points(similar_points)
                consolidated.append(consolidated_pp)
            else:
                consolidated.append(pp1)

        return consolidated

    def _are_pain_points_similar(self, pp1: Dict, pp2: Dict) -> bool:
        """Check if two pain points are similar."""
        # Simple similarity based on keyword overlap
        keywords1 = set(pp1.get('keywords', []))
        keywords2 = set(pp2.get('keywords', []))

        if not keywords1 or not keywords2:
            return False

        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        similarity = intersection / union if union > 0 else 0

        # Also check title similarity
        title1_words = set(pp1['title'].lower().split())
        title2_words = set(pp2['title'].lower().split())
        title_similarity = len(title1_words.intersection(title2_words)) / len(title1_words.union(title2_words))

        return similarity > 0.3 or title_similarity > 0.5

    def _merge_similar_pain_points(self, pain_points: List[Dict]) -> Dict:
        """Merge similar pain points into one."""
        if not pain_points:
            return {}

        # Use the highest severity one as base
        base_pp = max(pain_points, key=lambda x: x['severity'])

        # Combine evidence links
        all_links = []
        for pp in pain_points:
            all_links.extend(pp.get('evidence_links', []))
        base_pp['evidence_links'] = list(set(all_links))

        # Average severity (weighted by validation score)
        total_weight = sum(pp.get('validation_score', 0.5) for pp in pain_points)
        weighted_severity = sum(
            pp['severity'] * pp.get('validation_score', 0.5)
            for pp in pain_points
        )
        base_pp['severity'] = weighted_severity / total_weight if total_weight > 0 else base_pp['severity']

        # Boost validation score for consensus
        base_pp['validation_score'] = min(base_pp.get('validation_score', 0.5) + 0.2, 1.0)

        return base_pp

    async def _save_pain_points(self, company_id: int, pain_points: List[Dict]) -> List[PainPoint]:
        """Save pain points to database."""
        saved_pain_points = []

        for pp_data in pain_points:
            # Create pain point object
            pain_point = PainPoint(
                company_id=company_id,
                **pp_data
            )

            self.db.add(pain_point)
            saved_pain_points.append(pain_point)

        await self.db.commit()

        # Refresh to get IDs
        for pp in saved_pain_points:
            await self.db.refresh(pp)

        return saved_pain_points
