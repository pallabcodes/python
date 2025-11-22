"""Sample projects demonstrating the NoLeet concept."""

from noleet.core.models import Topic
from noleet.curation.builder import ProjectBuilder


def create_sample_projects() -> list:
    """
    Create sample projects for demonstration.
    
    Returns:
        List of sample Project instances
    """
    builder = ProjectBuilder()
    projects = []
    
    project = builder.create_project(
        project_id="real_time_analytics_engine",
        title="Real-Time Analytics Engine with Adaptive Windowing",
        description=(
            "Build a production-grade real-time analytics engine that processes "
            "streaming data with adaptive windowing strategies. This project combines "
            "dynamic programming for optimal resource allocation, sliding window techniques "
            "for efficient data processing, and merge intervals for handling overlapping "
            "time windows. The system adapts to changing workloads and optimizes memory "
            "usage while maintaining low latency."
        ),
        short_description=(
            "Production-grade real-time analytics engine with adaptive windowing "
            "and optimal resource allocation"
        ),
        tasks=[
            builder.create_task(
                task_id="task_1",
                title="Design Core Data Structures",
                description=(
                    "Design and implement efficient data structures for storing "
                    "time-series data and managing sliding windows. You'll need to "
                    "create a custom data structure that can efficiently merge "
                    "overlapping intervals and maintain window state."
                ),
                dsa_involvements=[
                    builder.create_dsa_involvement(Topic.MERGE_INTERVALS, 40.0),
                    builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 30.0)
                ],
                subtasks=[
                    builder.create_subtask(
                        subtask_id="subtask_1_1",
                        title="Implement Interval Merging Logic",
                        description=(
                            "Create a function that takes a list of time intervals "
                            "and merges overlapping ones. This is crucial for "
                            "combining data from multiple sources."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.MERGE_INTERVALS, 80.0)
                        ],
                        order=0
                    ),
                    builder.create_subtask(
                        subtask_id="subtask_1_2",
                        title="Build Sliding Window Data Structure",
                        description=(
                            "Design a data structure that maintains a sliding window "
                            "of the last N time units. It should support efficient "
                            "additions and removals as time progresses."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 85.0)
                        ],
                        order=1
                    )
                ],
                order=0
            ),
            builder.create_task(
                task_id="task_2",
                title="Implement Dynamic Resource Allocation",
                description=(
                    "Use dynamic programming to optimize resource allocation based "
                    "on workload patterns. The system should predict future resource "
                    "needs and allocate accordingly to minimize costs while maintaining "
                    "performance SLAs."
                ),
                dsa_involvements=[
                    builder.create_dsa_involvement(Topic.DYNAMIC_PROGRAMMING, 70.0),
                    builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 20.0)
                ],
                subtasks=[
                    builder.create_subtask(
                        subtask_id="subtask_2_1",
                        title="Design DP State Transition",
                        description=(
                            "Define the state space for resource allocation decisions. "
                            "Each state represents a configuration of resources, and "
                            "transitions represent allocation changes."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.DYNAMIC_PROGRAMMING, 90.0)
                        ],
                        order=0
                    ),
                    builder.create_subtask(
                        subtask_id="subtask_2_2",
                        title="Implement Optimization Algorithm",
                        description=(
                            "Write the DP algorithm that finds the optimal resource "
                            "allocation strategy over a time horizon, considering "
                            "costs and performance constraints."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.DYNAMIC_PROGRAMMING, 85.0)
                        ],
                        order=1
                    ),
                    builder.create_subtask(
                        subtask_id="subtask_2_3",
                        title="Integrate with Sliding Window",
                        description=(
                            "Connect the DP optimizer with the sliding window to "
                            "make decisions based on recent workload patterns."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.DYNAMIC_PROGRAMMING, 40.0),
                            builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 50.0)
                        ],
                        order=2
                    )
                ],
                order=1
            ),
            builder.create_task(
                task_id="task_3",
                title="Build Query Processing Engine",
                description=(
                    "Create a query engine that efficiently processes analytics "
                    "queries over sliding windows. Use merge intervals to combine "
                    "results from multiple time windows."
                ),
                dsa_involvements=[
                    builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 50.0),
                    builder.create_dsa_involvement(Topic.MERGE_INTERVALS, 30.0)
                ],
                subtasks=[
                    builder.create_subtask(
                        subtask_id="subtask_3_1",
                        title="Implement Window-Based Aggregation",
                        description=(
                            "Create functions that aggregate data within sliding "
                            "windows, supporting operations like sum, average, max, min."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 75.0)
                        ],
                        order=0
                    ),
                    builder.create_subtask(
                        subtask_id="subtask_3_2",
                        title="Merge Results from Multiple Windows",
                        description=(
                            "When a query spans multiple time windows, merge the "
                            "results efficiently using interval merging techniques."
                        ),
                        dsa_involvements=[
                            builder.create_dsa_involvement(Topic.MERGE_INTERVALS, 70.0),
                            builder.create_dsa_involvement(Topic.SLIDING_WINDOW, 20.0)
                        ],
                        order=1
                    )
                ],
                order=2
            )
        ],
        required_topics=[
            Topic.DYNAMIC_PROGRAMMING,
            Topic.SLIDING_WINDOW,
            Topic.MERGE_INTERVALS
        ],
        primary_topics=[
            Topic.DYNAMIC_PROGRAMMING,
            Topic.SLIDING_WINDOW,
            Topic.MERGE_INTERVALS
        ],
        difficulty="advanced",
        estimated_hours=40,
        research_references=[
            builder.create_research_reference(
                title="Adaptive Windowing for Stream Processing",
                authors=["Research Team"],
                url="https://example.com/adaptive-windowing",
                description=(
                    "Paper on adaptive windowing strategies for stream processing "
                    "systems with dynamic resource allocation"
                ),
                algorithms=["Adaptive Window Sizing", "DP-based Resource Allocation"],
                custom_modifications=(
                    "Combined with merge intervals for handling overlapping windows "
                    "and custom sliding window implementation optimized for analytics"
                )
            )
        ],
        tags=["real-time", "analytics", "streaming", "production"]
    )
    projects.append(project)
    
    return projects

