"""
Advanced Hybrid Concurrency Patterns.

This module provides cutting-edge concurrency patterns that extend beyond basic
hybrid approaches to include distributed systems, actor models, reactive programming,
and domain-specific optimizations.

Key areas covered:
- Advanced synchronization patterns for distributed systems
- Actor model implementations with message passing
- Reactive programming with streams and backpressure
- Custom concurrency primitives beyond standard library
- Performance profiling and monitoring tools
- Configuration-driven concurrency approaches
- Container-aware and distributed concurrency
- ML-specific concurrency patterns and optimizations
"""

try:
    from .advanced_sync import (
        DistributedLock,
        TransactionalMemory,
        LockFreeQueue,
        CrossModelBarrier,
        AtomicCounter,
        ReadWriteLock
    )
except ImportError:
    # Handle optional dependencies
    DistributedLock = None
    TransactionalMemory = None
    LockFreeQueue = None
    CrossModelBarrier = None
    AtomicCounter = None
    ReadWriteLock = None

try:
    from .distributed_concurrency import (
        CeleryHybridExecutor,
        DaskDistributedExecutor,
        KubernetesAwareExecutor,
        ServiceMeshCoordinator
    )
except ImportError:
    CeleryHybridExecutor = None
    DaskDistributedExecutor = None
    KubernetesAwareExecutor = None
    ServiceMeshCoordinator = None

try:
    from .actor_model import (
        ActorSystem,
        PykkaActor,
        SupervisorActor,
        MessageQueue,
        FaultTolerantActor
    )
except ImportError:
    ActorSystem = None
    PykkaActor = None
    SupervisorActor = None
    MessageQueue = None
    FaultTolerantActor = None

try:
    from .reactive_programming import (
        ReactiveStream,
        RxPyObservable,
        AsyncReactiveStream,
        BackpressureHandler,
        StreamProcessor
    )
except ImportError:
    ReactiveStream = None
    RxPyObservable = None
    AsyncReactiveStream = None
    BackpressureHandler = None
    StreamProcessor = None

try:
    from .custom_primitives import (
        PriorityQueue,
        WeightedSemaphore,
        AdaptiveRateLimiter,
        SmartCircuitBreaker,
        ContextAwareLock,
        BufferedChannel
    )
except ImportError:
    PriorityQueue = None
    WeightedSemaphore = None
    AdaptiveRateLimiter = None
    SmartCircuitBreaker = None
    ContextAwareLock = None
    BufferedChannel = None

try:
    from .performance_profiling import (
        ConcurrencyProfiler,
        RealTimeMonitor,
        BottleneckDetector,
        PerformanceDashboard,
        TracingManager
    )
except ImportError:
    ConcurrencyProfiler = None
    RealTimeMonitor = None
    BottleneckDetector = None
    PerformanceDashboard = None
    TracingManager = None

try:
    from .config_driven import (
        ConcurrencyConfig,
        AdaptiveExecutor,
        RuntimeSwitcher,
        ConfigurableHybrid
    )
except ImportError:
    ConcurrencyConfig = None
    AdaptiveExecutor = None
    RuntimeSwitcher = None
    ConfigurableHybrid = None

try:
    from .container_aware import (
        DockerCommunicator,
        KubernetesCoordinator,
        ServiceDiscovery,
        ContainerLifecycleManager
    )
except ImportError:
    DockerCommunicator = None
    KubernetesCoordinator = None
    ServiceDiscovery = None
    ContainerLifecycleManager = None

try:
    from .ml_specific import (
        GPUConcurrencyManager,
        ModelInferencePipeline,
        DistributedTrainingCoordinator,
        DataLoaderOptimizer,
        AcceleratorManager
    )
except ImportError:
    GPUConcurrencyManager = None
    ModelInferencePipeline = None
    DistributedTrainingCoordinator = None
    DataLoaderOptimizer = None
    AcceleratorManager = None

__all__ = [
    # Advanced Synchronization
    "DistributedLock", "TransactionalMemory", "LockFreeQueue",
    "CrossModelBarrier", "AtomicCounter", "ReadWriteLock",

    # Distributed Concurrency
    "CeleryHybridExecutor", "DaskDistributedExecutor",
    "KubernetesAwareExecutor", "ServiceMeshCoordinator",

    # Actor Model
    "ActorSystem", "PykkaActor", "SupervisorActor",
    "MessageQueue", "FaultTolerantActor",

    # Reactive Programming
    "ReactiveStream", "RxPyObservable", "AsyncReactiveStream",
    "BackpressureHandler", "StreamProcessor",

    # Custom Primitives
    "PriorityQueue", "WeightedSemaphore", "AdaptiveRateLimiter",
    "SmartCircuitBreaker", "ContextAwareLock", "BufferedChannel",

    # Performance Profiling
    "ConcurrencyProfiler", "RealTimeMonitor", "BottleneckDetector",
    "PerformanceDashboard", "TracingManager",

    # Configuration-Driven
    "ConcurrencyConfig", "AdaptiveExecutor", "RuntimeSwitcher",
    "ConfigurableHybrid",

    # Container-Aware
    "DockerCommunicator", "KubernetesCoordinator",
    "ServiceDiscovery", "ContainerLifecycleManager",

    # ML-Specific
    "GPUConcurrencyManager", "ModelInferencePipeline",
    "DistributedTrainingCoordinator", "DataLoaderOptimizer",
    "AcceleratorManager"
]
