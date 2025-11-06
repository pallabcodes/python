"""
FastAPI application for MLOps + Gen AI Platform.

Provides REST API endpoints for all platform capabilities with comprehensive
documentation, validation, and production-ready features.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from ..core.platform import MLOpsPlatform
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.platform import MLOpsPlatform


# Request/Response Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str]


class LLMRequest(BaseModel):
    """LLM generation request."""
    prompt: str = Field(..., description="Input prompt for generation")
    context: Optional[List[str]] = Field(None, description="Optional RAG context")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1000, ge=1, le=4096)
    provider: Optional[str] = Field(None, description="Specific LLM provider")


class LLMResponse(BaseModel):
    """LLM generation response."""
    content: str
    usage: Dict[str, Any]
    processing_time: float


class ExperimentCreateRequest(BaseModel):
    """Experiment creation request."""
    name: str
    description: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class ModelRegisterRequest(BaseModel):
    """Model registration request."""
    name: str
    version: str
    model_path: str
    metadata: Optional[Dict[str, Any]] = None


class AgentCreateRequest(BaseModel):
    """Agent creation request."""
    name: str
    role: str
    goal: str
    tools: List[str]
    config: Optional[Dict[str, Any]] = None


class AgentTaskRequest(BaseModel):
    """Agent task execution request."""
    task: str
    timeout: Optional[float] = 30.0


class RAGSearchRequest(BaseModel):
    """RAG search request."""
    query: str
    top_k: Optional[int] = 5
    filters: Optional[Dict[str, Any]] = None


class FeatureStoreRequest(BaseModel):
    """Feature store request."""
    feature_names: List[str]
    entity_ids: List[str]
    as_of_date: Optional[str] = None


class FineTuneRequest(BaseModel):
    """Model fine-tuning request."""
    model_name: str
    dataset_path: str
    config: Optional[Dict[str, Any]] = None


# Global platform instance
platform: Optional[MLOpsPlatform] = None


# FastAPI Application
app = FastAPI(
    title="MLOps + Gen AI Platform API",
    description="Production API for comprehensive MLOps and Generative AI capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize platform on startup."""
    global platform
    platform = MLOpsPlatform()
    await platform.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown platform on shutdown."""
    global platform
    if platform:
        await platform.shutdown()


# Dependency to get platform instance
def get_platform() -> MLOpsPlatform:
    """Get platform instance."""
    if not platform:
        raise HTTPException(status_code=503, detail="Platform not initialized")
    return platform


# Health Check Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(platform: MLOpsPlatform = Depends(get_platform)):
    """Platform health check."""
    status = platform.get_status()
    return HealthResponse(
        status=status.status,
        version=status.version,
        uptime_seconds=status.uptime_seconds or 0.0,
        components=status.components
    )


@app.get("/health/ready")
async def readiness_check(platform: MLOpsPlatform = Depends(get_platform)):
    """Readiness probe."""
    status = platform.get_status()
    if status.status == "healthy":
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/health/live")
async def liveness_check():
    """Liveness probe."""
    return {"status": "alive"}


# MLOps Endpoints
@app.post("/experiments", tags=["MLOps"])
async def create_experiment(
    request: ExperimentCreateRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Create a new experiment."""
    try:
        experiment_id = await platform._mlops_components["experiment_tracker"].create_experiment({
            "name": request.name,
            "description": request.description,
            "tags": request.tags or {}
        })
        return {"experiment_id": experiment_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")


@app.get("/experiments", tags=["MLOps"])
async def list_experiments(platform: MLOpsPlatform = Depends(get_platform)):
    """List all experiments."""
    try:
        experiments = await platform._mlops_components["model_registry"].list_models()
        return {"experiments": experiments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@app.post("/models/register", tags=["MLOps"])
async def register_model(
    request: ModelRegisterRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Register a new model."""
    try:
        # Create dummy model file for demo
        import os
        os.makedirs("models", exist_ok=True)
        with open(request.model_path, "w") as f:
            f.write("dummy model data")

        from mlops.model_registry import ModelMetadata
        metadata = ModelMetadata(
            name=request.name,
            version=request.version,
            description=f"Model {request.name} v{request.version}",
            model_type="unknown",
            framework="unknown",
            created_at=asyncio.get_event_loop().time(),
            updated_at=asyncio.get_event_loop().time(),
            **(request.metadata or {})
        )

        model_version = await platform._mlops_components["model_registry"].register_model(
            name=request.name,
            model_artifact=request.model_path,
            metadata=metadata
        )
        return {"model_version": model_version, "status": "registered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register model: {str(e)}")


@app.get("/models", tags=["MLOps"])
async def list_models(platform: MLOpsPlatform = Depends(get_platform)):
    """List registered models."""
    try:
        models = await platform._mlops_components["model_registry"].list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@app.post("/features", tags=["MLOps"])
async def get_features(
    request: FeatureStoreRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Retrieve features from feature store."""
    try:
        features = await platform._mlops_components["feature_store"].get_feature_values(
            request.feature_names,
            request.entity_ids
        )
        return {"features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get features: {str(e)}")


# Gen AI Endpoints
@app.post("/generate", response_model=LLMResponse, tags=["Gen AI"])
async def generate_text(
    request: LLMRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Generate text using LLM."""
    start_time = time.time()
    try:
        content = await platform.generate_text(
            prompt=request.prompt,
            context=request.context,
            **({"provider": request.provider} if request.provider else {})
        )

        processing_time = time.time() - start_time
        return LLMResponse(
            content=content,
            usage={},  # Would be populated from actual LLM usage
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/agents", tags=["Gen AI"])
async def create_agent(
    request: AgentCreateRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Create a new AI agent."""
    try:
        from genai.ai_agent_framework import AgentConfig
        config = AgentConfig(
            name=request.name,
            role=request.role,
            goal=request.goal,
            **(request.config or {})
        )

        agent = await platform.create_agent(
            agent_type="reasoning",
            config=config,
            tools=request.tools
        )
        return {"agent_name": request.name, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@app.post("/agents/{agent_name}/execute", tags=["Gen AI"])
async def execute_agent_task(
    agent_name: str,
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Execute a task with an AI agent."""
    try:
        # Execute in background for long-running tasks
        result = await platform._genai_components["agent_framework"].execute_task(
            agent_name,
            request.task,
            timeout=request.timeout
        )
        return {
            "agent": agent_name,
            "task": request.task,
            "result": {
                "success": result.success,
                "final_answer": result.final_answer,
                "iterations": result.iterations_used,
                "execution_time": result.execution_time
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@app.post("/search", tags=["Gen AI"])
async def search_knowledge(
    request: RAGSearchRequest,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Search knowledge base using RAG."""
    try:
        results = await platform.search_knowledge(
            query=request.query,
            top_k=request.top_k,
            **({"filters": request.filters} if request.filters else {})
        )
        return {"query": request.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/finetune", tags=["Gen AI"])
async def finetune_model(
    request: FineTuneRequest,
    background_tasks: BackgroundTasks,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Start model fine-tuning."""
    try:
        # Create fine-tuning job
        job_id = await platform._genai_components["finetuning_pipeline"].create_finetuning_job(
            name=request.model_name,
            config=request.config or {},
            dataset_config={"path": request.dataset_path}
        )

        # Start fine-tuning in background
        background_tasks.add_task(
            platform._genai_components["finetuning_pipeline"].start_finetuning,
            job_id
        )

        return {"job_id": job_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fine-tuning failed: {str(e)}")


@app.get("/finetune/{job_id}", tags=["Gen AI"])
async def get_finetuning_status(
    job_id: str,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Get fine-tuning job status."""
    try:
        status = platform._genai_components["finetuning_pipeline"].get_training_status(job_id)
        return {"job_id": job_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.post("/process", tags=["Gen AI"])
async def process_multimodal(
    content: str,
    content_type: str,
    platform: MLOpsPlatform = Depends(get_platform)
):
    """Process multi-modal content."""
    try:
        result = await platform.process_multimodal(content, content_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# Monitoring Endpoints
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics(platform: MLOpsPlatform = Depends(get_platform)):
    """Get platform metrics."""
    try:
        # Get LLM usage stats
        llm_stats = platform._genai_components["llm_manager"].get_usage_stats()

        # Get model performance
        model_performance = {}
        for model_name in await platform._mlops_components["model_registry"].list_models():
            perf = await platform._mlops_components["model_monitor"].get_model_performance(
                model_name["name"], hours=1
            )
            model_performance[model_name["name"]] = perf

        return {
            "llm_usage": llm_stats,
            "model_performance": model_performance,
            "platform_status": platform.get_status().dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.get("/logs", tags=["Monitoring"])
async def get_logs(lines: int = 100):
    """Get recent application logs."""
    # This would integrate with actual logging system
    return {"logs": f"Last {lines} log lines would be returned here"}


# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
