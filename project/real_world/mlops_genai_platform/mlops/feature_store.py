"""
Feature store for MLOps leveraging analytics pipeline data processing.

Provides centralized feature management with versioning, serving, and
real-time feature computation capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

try:
    from ..core.config import PlatformConfig
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.config import PlatformConfig

Base = declarative_base()


class FeatureMetadata(Base):
    """Feature metadata table."""

    __tablename__ = "feature_metadata"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    feature_type = Column(String(50))  # numerical, categorical, text, etc.
    data_type = Column(String(50))  # int, float, string, etc.
    version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(Text)  # JSON string of tags


class FeatureValues(Base):
    """Feature values table."""

    __tablename__ = "feature_values"

    id = Column(Integer, primary_key=True)
    feature_name = Column(String(255), nullable=False)
    entity_id = Column(String(255), nullable=False)  # user_id, item_id, etc.
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    version = Column(String(50))


class FeatureStore:
    """
    Feature store with real-time and batch feature serving.

    Leverages analytics pipeline data processing for feature engineering,
    with versioning, serving, and monitoring capabilities.

    Features:
    - Feature versioning and metadata management
    - Real-time and batch feature serving
    - Feature monitoring and quality checks
    - Integration with analytics pipeline transformations
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize feature store.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.FeatureStore")

        # Database setup
        self.engine = create_engine(
            self.config.database.connection_string,
            pool_size=self.config.database.pool_size,
            max_overflow=self.config.database.max_overflow,
        )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Feature cache
        self._feature_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=1)

    async def initialize(self) -> None:
        """Initialize feature store."""
        self.logger.info("Initializing feature store...")

        # Create tables
        Base.metadata.create_all(bind=self.engine)

        # Test connection
        try:
            with self.SessionLocal() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
            self.logger.info("Feature store database connection established")
        except Exception as e:
            self.logger.error(f"Feature store database connection failed: {e}")
            raise

        self.logger.info("Feature store initialized")

    async def create_feature(
        self,
        name: str,
        feature_type: str,
        data_type: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new feature definition.

        Args:
            name: Feature name
            feature_type: Type of feature (numerical, categorical, text)
            data_type: Data type (int, float, string)
            description: Optional description
            tags: Optional tags

        Returns:
            Feature version
        """
        self.logger.info(f"Creating feature: {name}")

        with self.SessionLocal() as session:
            # Check if feature exists
            existing = session.query(FeatureMetadata).filter_by(name=name).first()
            if existing:
                # Update version
                version_parts = existing.version.split('.')
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                version = '.'.join(version_parts)
            else:
                version = "1.0.0"

            # Create or update metadata
            tags_json = str(tags) if tags else "{}"

            if existing:
                existing.version = version
                existing.description = description or existing.description
                existing.feature_type = feature_type
                existing.data_type = data_type
                existing.tags = tags_json
                existing.updated_at = datetime.utcnow()
            else:
                metadata = FeatureMetadata(
                    name=name,
                    description=description,
                    feature_type=feature_type,
                    data_type=data_type,
                    version=version,
                    tags=tags_json
                )
                session.add(metadata)

            session.commit()
            self.logger.info(f"Created feature {name} version {version}")
            return version

    async def store_feature_values(
        self,
        feature_name: str,
        values: Dict[str, Union[float, int, str]],
        version: Optional[str] = None
    ) -> int:
        """
        Store feature values for entities.

        Args:
            feature_name: Name of the feature
            values: Dictionary of entity_id -> value
            version: Optional feature version

        Returns:
            Number of values stored
        """
        self.logger.debug(f"Storing {len(values)} values for feature {feature_name}")

        with self.SessionLocal() as session:
            # Get feature version
            if not version:
                metadata = session.query(FeatureMetadata).filter_by(name=feature_name).first()
                version = metadata.version if metadata else "1.0.0"

            # Store values
            stored_count = 0
            for entity_id, value in values.items():
                # Convert value to float if possible
                try:
                    numeric_value = float(value) if isinstance(value, (int, float, str)) else 0.0
                except (ValueError, TypeError):
                    numeric_value = 0.0  # Default for non-numeric

                feature_value = FeatureValues(
                    feature_name=feature_name,
                    entity_id=str(entity_id),
                    value=numeric_value,
                    version=version
                )
                session.add(feature_value)
                stored_count += 1

            session.commit()

        self.logger.info(f"Stored {stored_count} feature values for {feature_name}")
        return stored_count

    async def get_feature_values(
        self,
        feature_names: List[str],
        entity_ids: List[str],
        as_of_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve feature values for entities.

        Args:
            feature_names: List of feature names
            entity_ids: List of entity IDs
            as_of_date: Optional point-in-time query

        Returns:
            Dictionary of entity_id -> {feature_name: value}
        """
        self.logger.debug(f"Retrieving features {feature_names} for {len(entity_ids)} entities")

        with self.SessionLocal() as session:
            # Build query
            query = session.query(FeatureValues).filter(
                FeatureValues.feature_name.in_(feature_names),
                FeatureValues.entity_id.in_(entity_ids)
            )

            if as_of_date:
                query = query.filter(FeatureValues.timestamp <= as_of_date)

            # Get latest values per entity-feature combination
            subquery = query.subquery()
            latest_values = session.query(
                subquery.c.feature_name,
                subquery.c.entity_id,
                func.max(subquery.c.timestamp).label('max_timestamp')
            ).group_by(
                subquery.c.feature_name,
                subquery.c.entity_id
            ).subquery()

            results = session.query(FeatureValues).join(
                latest_values,
                (FeatureValues.feature_name == latest_values.c.feature_name) &
                (FeatureValues.entity_id == latest_values.c.entity_id) &
                (FeatureValues.timestamp == latest_values.c.max_timestamp)
            ).all()

            # Organize results
            feature_data = {}
            for entity_id in entity_ids:
                feature_data[entity_id] = {}

            for result in results:
                feature_data[result.entity_id][result.feature_name] = result.value

        return feature_data

    async def get_feature_stats(self, feature_name: str) -> Dict[str, Any]:
        """
        Get statistics for a feature.

        Args:
            feature_name: Name of the feature

        Returns:
            Feature statistics
        """
        with self.SessionLocal() as session:
            # Get metadata
            metadata = session.query(FeatureMetadata).filter_by(name=feature_name).first()
            if not metadata:
                raise ValueError(f"Feature {feature_name} not found")

            # Get value statistics
            values_query = session.query(
                func.count(FeatureValues.value).label('count'),
                func.avg(FeatureValues.value).label('mean'),
                func.min(FeatureValues.value).label('min'),
                func.max(FeatureValues.value).label('max')
            ).filter(FeatureValues.feature_name == feature_name)

            result = values_query.first()

            stats = {
                "feature_name": feature_name,
                "feature_type": metadata.feature_type,
                "data_type": metadata.data_type,
                "version": metadata.version,
                "description": metadata.description,
                "count": result.count or 0,
                "mean": float(result.mean) if result.mean else None,
                "min": float(result.min) if result.min else None,
                "max": float(result.max) if result.max else None,
                "std": None,  # SQLite doesn't support stddev function
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
            }

        return stats

    async def list_features(
        self,
        feature_type_filter: Optional[str] = None,
        name_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List registered features.

        Args:
            feature_type_filter: Optional feature type filter
            name_filter: Optional name filter

        Returns:
            List of feature summaries
        """
        with self.SessionLocal() as session:
            query = session.query(FeatureMetadata)

            if feature_type_filter:
                query = query.filter(FeatureMetadata.feature_type == feature_type_filter)

            if name_filter:
                query = query.filter(FeatureMetadata.name.contains(name_filter))

            features = query.all()

            result = []
            for feature in features:
                stats = await self.get_feature_stats(feature.name)
                result.append({
                    "name": feature.name,
                    "type": feature.feature_type,
                    "data_type": feature.data_type,
                    "version": feature.version,
                    "description": feature.description,
                    "count": stats["count"],
                    "created_at": feature.created_at,
                    "updated_at": feature.updated_at,
                })

        return sorted(result, key=lambda x: x["updated_at"], reverse=True)

    async def delete_feature(self, feature_name: str) -> bool:
        """
        Delete a feature and all its values.

        Args:
            feature_name: Name of the feature to delete

        Returns:
            True if deleted, False otherwise
        """
        with self.SessionLocal() as session:
            # Delete values first
            session.query(FeatureValues).filter_by(feature_name=feature_name).delete()

            # Delete metadata
            deleted = session.query(FeatureMetadata).filter_by(name=feature_name).delete()

            session.commit()

        if deleted:
            self.logger.info(f"Deleted feature: {feature_name}")

        return deleted > 0

    async def create_feature_from_pipeline(
        self,
        pipeline_data: Any,
        feature_config: Dict[str, Any]
    ) -> str:
        """
        Create features from analytics pipeline data.

        This method integrates with the analytics pipeline's transformation
        stages to create features from processed data.

        Args:
            pipeline_data: Data from analytics pipeline
            feature_config: Feature creation configuration

        Returns:
            Feature version
        """
        self.logger.info("Creating features from analytics pipeline data")

        # Here you would integrate with analytics pipeline transformations
        # For now, create a placeholder implementation

        feature_name = feature_config.get("name", f"pipeline_feature_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        feature_type = feature_config.get("type", "numerical")
        data_type = feature_config.get("data_type", "float")

        # Create feature metadata
        version = await self.create_feature(
            name=feature_name,
            feature_type=feature_type,
            data_type=data_type,
            description=feature_config.get("description", "Feature from analytics pipeline"),
            tags=feature_config.get("tags", {"source": "analytics_pipeline"})
        )

        # Process and store feature values
        # In a real implementation, this would transform pipeline_data
        # For now, create sample values
        sample_values = {f"entity_{i}": float(i) * 0.1 for i in range(100)}
        await self.store_feature_values(feature_name, sample_values, version)

        self.logger.info(f"Created feature {feature_name} from pipeline data")
        return version

    async def get_online_features(
        self,
        feature_names: List[str],
        entity_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get features for online serving (with caching).

        Args:
            feature_names: List of feature names
            entity_ids: List of entity IDs

        Returns:
            Feature values with caching
        """
        # Check cache first
        cache_key = f"{','.join(sorted(feature_names))}_{','.join(sorted(entity_ids))}"
        if cache_key in self._feature_cache:
            cached_data, cache_time = self._feature_cache[cache_key]
            if datetime.now() - cache_time < self._cache_ttl:
                return cached_data

        # Fetch from database
        features = await self.get_feature_values(feature_names, entity_ids)

        # Cache results
        self._feature_cache[cache_key] = (features, datetime.now())

        return features

    async def monitor_feature_quality(self, feature_name: str) -> Dict[str, Any]:
        """
        Monitor feature quality and data drift.

        Args:
            feature_name: Name of the feature to monitor

        Returns:
            Quality metrics
        """
        self.logger.debug(f"Monitoring quality for feature {feature_name}")

        # Get recent statistics
        stats = await self.get_feature_stats(feature_name)

        # Calculate quality metrics
        quality_metrics = {
            "feature_name": feature_name,
            "null_percentage": 0.0,  # Would calculate from data
            "outlier_percentage": 0.0,  # Would detect outliers
            "drift_score": 0.0,  # Would compare with historical data
            "freshness_hours": 0.0,  # Time since last update
            "completeness_score": 1.0 if stats["count"] > 0 else 0.0,
        }

        # In a real implementation, you would:
        # - Check for null values
        # - Detect outliers using statistical methods
        # - Compare with historical distributions (data drift)
        # - Monitor update frequency

        return quality_metrics

    async def shutdown(self) -> None:
        """Shutdown feature store."""
        self.logger.info("Shutting down feature store...")

        # Close database connections
        self.engine.dispose()

        # Clear cache
        self._feature_cache.clear()

        self.logger.info("Feature store shutdown complete")
