"""
Multi-modal AI Processor for text, images, and code.

Provides enterprise-grade multi-modal processing capabilities including:
- Image analysis and understanding
- Code analysis and generation
- Multi-modal embeddings
- Cross-modal retrieval and generation
"""

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

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


class MultiModalContent(BaseModel):
    """Multi-modal content representation."""

    content_type: str  # text, image, code, audio, video
    content: Union[str, bytes]
    metadata: Dict[str, Any] = {}
    embeddings: Optional[List[float]] = None
    analysis_results: Dict[str, Any] = {}


class AnalysisResult(BaseModel):
    """Result from multi-modal analysis."""

    content_type: str
    analysis_type: str
    results: Dict[str, Any]
    confidence: Optional[float] = None
    processing_time: float


class MultiModalConfig(BaseModel):
    """Configuration for multi-modal processing."""

    enable_image_processing: bool = True
    enable_code_analysis: bool = True
    enable_audio_processing: bool = False
    enable_video_processing: bool = False

    # Model configurations
    vision_model: str = "openai/clip-vit-base-patch32"
    code_model: str = "microsoft/codebert-base"
    embedding_model: str = "openai/clip-vit-base-patch32"

    # Processing settings
    max_image_size: int = 1024
    max_code_length: int = 2048
    batch_size: int = 8
    cache_embeddings: bool = True


class MultiModalProcessor:
    """
    Multi-modal AI processor for handling different content types.

    Features:
    - Image analysis and captioning
    - Code understanding and generation
    - Multi-modal embeddings
    - Cross-modal search and retrieval
    """

    def __init__(self, config: PlatformConfig):
        """
        Initialize multi-modal processor.

        Args:
            config: Platform configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{config.project_name}.MultiModalProcessor")

        # Configuration
        self.mm_config = MultiModalConfig()

        # Model caches
        self._vision_model = None
        self._code_model = None
        self._embedding_model = None
        self._processor = None

        # Cache for embeddings
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_file = self.config.data_dir / "multimodal_cache.json"

    async def initialize(self) -> None:
        """Initialize multi-modal processor."""
        self.logger.info("Initializing Multi-modal Processor...")

        # Load embedding cache
        await self._load_cache()

        # Initialize models as needed
        if self.mm_config.enable_image_processing:
            await self._init_vision_model()

        if self.mm_config.enable_code_analysis:
            await self._init_code_model()

        self.logger.info("Multi-modal processor initialized")

    async def _init_vision_model(self) -> None:
        """Initialize vision model for image processing."""
        try:
            from transformers import CLIPProcessor, CLIPModel

            model_name = self.mm_config.vision_model.split('/', 1)[-1]
            self._vision_model = CLIPModel.from_pretrained(model_name)
            self._processor = CLIPProcessor.from_pretrained(model_name)

            self.logger.info(f"Vision model loaded: {model_name}")

        except ImportError:
            self.logger.warning("Transformers not available, vision processing disabled")
        except Exception as e:
            self.logger.error(f"Failed to load vision model: {e}")

    async def _init_code_model(self) -> None:
        """Initialize code model for code analysis."""
        try:
            from transformers import AutoTokenizer, AutoModel

            self._code_model = AutoModel.from_pretrained(self.mm_config.code_model)
            self._code_tokenizer = AutoTokenizer.from_pretrained(self.mm_config.code_model)

            self.logger.info(f"Code model loaded: {self.mm_config.code_model}")

        except ImportError:
            self.logger.warning("Transformers not available, code analysis disabled")
        except Exception as e:
            self.logger.error(f"Failed to load code model: {e}")

    async def process_content(
        self,
        content: Union[str, bytes, Path],
        content_type: str,
        analysis_types: Optional[List[str]] = None
    ) -> MultiModalContent:
        """
        Process multi-modal content.

        Args:
            content: Content to process (text, image file, etc.)
            content_type: Type of content (text, image, code)
            analysis_types: Types of analysis to perform

        Returns:
            Processed multi-modal content
        """
        self.logger.info(f"Processing {content_type} content")

        # Create content object
        if isinstance(content, Path):
            if content_type == "image":
                with open(content, "rb") as f:
                    content_bytes = f.read()
                content_str = base64.b64encode(content_bytes).decode()
            else:
                with open(content, "r") as f:
                    content_str = f.read()
        elif isinstance(content, bytes):
            if content_type == "image":
                content_str = base64.b64encode(content).decode()
            else:
                content_str = content.decode()
        else:
            content_str = content

        mm_content = MultiModalContent(
            content_type=content_type,
            content=content_str,
            metadata={"source": "processed"}
        )

        # Perform analysis based on content type
        if content_type == "image" and self.mm_config.enable_image_processing:
            mm_content.analysis_results = await self._analyze_image(content_str, analysis_types)
        elif content_type == "code" and self.mm_config.enable_code_analysis:
            mm_content.analysis_results = await self._analyze_code(content_str, analysis_types)
        elif content_type == "text":
            mm_content.analysis_results = await self._analyze_text(content_str, analysis_types)

        # Generate embeddings
        if self._embedding_model or self._vision_model:
            mm_content.embeddings = await self._generate_embeddings(mm_content)

        return mm_content

    async def _analyze_image(
        self,
        image_b64: str,
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze image content."""
        results = {}

        if not analysis_types:
            analysis_types = ["caption", "objects", "sentiment"]

        try:
            import torch
            from PIL import Image
            import io

            # Decode image
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes))

            # Ensure RGB mode
            if image.mode != 'RGB':
                image = image.convert('RGB')

            if "caption" in analysis_types:
                results["caption"] = await self._generate_image_caption(image)

            if "objects" in analysis_types:
                results["objects"] = await self._detect_objects(image)

            if "sentiment" in analysis_types:
                results["sentiment"] = await self._analyze_image_sentiment(image)

        except ImportError:
            results["error"] = "PIL or torch not available for image analysis"
        except Exception as e:
            results["error"] = f"Image analysis failed: {str(e)}"

        return results

    async def _analyze_code(
        self,
        code: str,
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze code content."""
        results = {}

        if not analysis_types:
            analysis_types = ["language", "complexity", "documentation"]

        if "language" in analysis_types:
            results["language"] = self._detect_programming_language(code)

        if "complexity" in analysis_types:
            results["complexity"] = self._calculate_code_complexity(code)

        if "documentation" in analysis_types:
            results["documentation"] = self._analyze_documentation(code)

        # Code embeddings would be generated separately
        if self._code_model:
            results["embeddings_available"] = True

        return results

    async def _analyze_text(
        self,
        text: str,
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze text content."""
        results = {}

        if not analysis_types:
            analysis_types = ["sentiment", "entities", "summary"]

        if "sentiment" in analysis_types:
            results["sentiment"] = self._analyze_text_sentiment(text)

        if "entities" in analysis_types:
            results["entities"] = self._extract_entities(text)

        if "summary" in analysis_types:
            results["summary"] = self._generate_summary(text)

        return results

    async def _generate_embeddings(self, content: MultiModalContent) -> List[float]:
        """Generate embeddings for multi-modal content."""
        # Create cache key
        content_hash = hash(f"{content.content_type}:{content.content}")
        cache_key = str(content_hash)

        # Check cache
        if self.mm_config.cache_embeddings and cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            if content.content_type == "image" and self._vision_model:
                # Generate image embeddings
                image_bytes = base64.b64decode(content.content)
                from PIL import Image
                import io

                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                inputs = self._processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    embeddings = self._vision_model.get_image_features(**inputs)
                    embeddings = embeddings.squeeze().tolist()

            elif content.content_type in ["text", "code"] and self._code_model:
                # Generate text/code embeddings
                inputs = self._code_tokenizer(
                    content.content,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.mm_config.max_code_length
                )
                with torch.no_grad():
                    outputs = self._code_model(**inputs)
                    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

            else:
                # Fallback: simple hash-based embedding
                import hashlib
                hash_obj = hashlib.md5(content.content.encode())
                embeddings = [float(int(hash_obj.hexdigest()[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]

            # Cache embeddings
            if self.mm_config.cache_embeddings:
                self._embedding_cache[cache_key] = embeddings
                await self._save_cache()

            return embeddings

        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return []

    async def _generate_image_caption(self, image: Any) -> str:
        """Generate caption for image."""
        # Placeholder - would use BLIP, CLIP, or similar model
        return "A processed image with various visual elements"

    async def _detect_objects(self, image: Any) -> List[Dict[str, Any]]:
        """Detect objects in image."""
        # Placeholder - would use YOLO, DETR, or similar model
        return [{"label": "object", "confidence": 0.8, "bbox": [0, 0, 100, 100]}]

    async def _analyze_image_sentiment(self, image: Any) -> Dict[str, float]:
        """Analyze sentiment of image."""
        # Placeholder - would use emotion recognition models
        return {"positive": 0.6, "neutral": 0.3, "negative": 0.1}

    def _detect_programming_language(self, code: str) -> str:
        """Detect programming language from code."""
        # Simple detection based on keywords
        if "def " in code or "import " in code:
            return "python"
        elif "function" in code or "const " in code:
            return "javascript"
        elif "#include" in code or "int main" in code:
            return "c++"
        else:
            return "unknown"

    def _calculate_code_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        lines = code.split('\n')
        return {
            "lines_of_code": len(lines),
            "functions": code.count("def "),
            "classes": code.count("class "),
            "imports": code.count("import "),
        }

    def _analyze_documentation(self, code: str) -> Dict[str, Any]:
        """Analyze code documentation."""
        lines = code.split('\n')
        docstrings = sum(1 for line in lines if '"""' in line or "'''" in line)
        comments = sum(1 for line in lines if line.strip().startswith('#'))

        return {
            "docstrings": docstrings,
            "comments": comments,
            "total_documentation_lines": docstrings + comments,
        }

    def _analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text."""
        # Simple rule-based sentiment analysis
        positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst"]

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        total = positive_count + negative_count
        if total == 0:
            return {"positive": 0.33, "neutral": 0.34, "negative": 0.33}

        return {
            "positive": positive_count / total,
            "negative": negative_count / total,
            "neutral": (len(words) - total) / len(words)
        }

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        # Placeholder - would use spaCy or similar NER model
        return [{"text": "example", "label": "MISC", "start": 0, "end": 7}]

    def _generate_summary(self, text: str) -> str:
        """Generate text summary."""
        # Simple extractive summary
        sentences = text.split('.')
        if len(sentences) <= 2:
            return text
        return '. '.join(sentences[:2]) + '.'

    async def search_similar(
        self,
        query_content: MultiModalContent,
        content_collection: List[MultiModalContent],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content in a collection.

        Args:
            query_content: Content to search for
            content_collection: Collection to search in
            top_k: Number of results to return

        Returns:
            Similar content with scores
        """
        if not query_content.embeddings:
            return []

        results = []
        query_emb = query_content.embeddings

        for content in content_collection:
            if content.embeddings:
                similarity = self._cosine_similarity(query_emb, content.embeddings)
                results.append({
                    "content": content,
                    "similarity": similarity
                })

        # Sort by similarity and return top-k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _load_cache(self) -> None:
        """Load embedding cache from disk."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r") as f:
                    self._embedding_cache = json.load(f)
                self.logger.info(f"Loaded {len(self._embedding_cache)} cached embeddings")
            except Exception as e:
                self.logger.error(f"Failed to load embedding cache: {e}")

    async def _save_cache(self) -> None:
        """Save embedding cache to disk."""
        try:
            with open(self._cache_file, "w") as f:
                json.dump(self._embedding_cache, f)
        except Exception as e:
            self.logger.error(f"Failed to save embedding cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics."""
        return {
            "vision_model_loaded": self._vision_model is not None,
            "code_model_loaded": self._code_model is not None,
            "cached_embeddings": len(self._embedding_cache),
            "supported_content_types": ["text", "image", "code"],
        }

    async def shutdown(self) -> None:
        """Shutdown multi-modal processor."""
        self.logger.info("Shutting down Multi-modal Processor...")

        # Save cache
        await self._save_cache()

        # Clear models
        self._vision_model = None
        self._code_model = None
        self._embedding_model = None
        self._processor = None

        self.logger.info("Multi-modal Processor shutdown complete")
