# Manual Intervention System

## Overview

The Manual Intervention System enables sophisticated human-AI collaboration in NoLeet workflows. When enabled, workflows can pause at strategic points, allowing human experts to review AI-generated data, apply domain knowledge, and provide enhanced recommendations before continuing automated processing.

## Key Features

- **Intelligent Pause/Resume**: Workflows pause at configured intervention points
- **Data Export/Import**: Seamless data exchange with external tools
- **Flexible Configuration**: Enable/disable intervention per agent type
- **External Tool Integration**: Works with Cursor, ChatGPT, and other tools
- **Production-Ready**: Comprehensive error handling and logging

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Workflow      │───▶│ Manual           │───▶│   External      │
│   Execution     │    │ Intervention     │    │   Processing    │
│                 │◀───│ Manager          │◀───│   (Cursor,      │
└─────────────────┘    └──────────────────┘    │   ChatGPT, etc.)│
                                               └─────────────────┘
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data          │    │   Resume         │    │   Enhanced      │
│   Export        │───▶│   Workflow       │───▶│   Results       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Enable Manual Intervention

```bash
# Enable manual intervention for project recommendations
noleet intervention config --enable --agents project_recommendation_agent

# Set export directory and timeout
noleet intervention config --export-dir ~/.noleet/intervention --timeout 1800
```

### 2. Run Workflow with Intervention

```bash
# This will pause for manual input
noleet find --topics dynamic_programming sliding_window
```

### 3. Check Paused Workflows

```bash
# See which workflows are waiting
noleet intervention status
```

### 4. Manual Processing

The system exports data to JSON/Markdown files. Use your preferred tools:

```bash
# Check exported files
ls ~/.noleet/intervention/

# Process with external tools (example)
cursor ~/.noleet/intervention/project_recommendation_data_*.md
```

Create a manual response file (e.g., `manual_recommendations_session123.json`):

```json
{
  "recommendations": [
    {
      "project_id": "expert_choice_1",
      "title": "Advanced DP Optimization Engine",
      "confidence_score": 0.95,
      "reasoning": "Expert analysis combining multiple research papers",
      "key_topics": ["dynamic_programming", "optimization"],
      "estimated_complexity": "advanced"
    }
  ],
  "metadata": {
    "manual_reviewer": "Your Name",
    "review_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 5. Resume Workflow

```bash
# Resume with manual input
noleet intervention resume <session_id>
```

## Configuration

### Configuration File

Create `~/.noleet/intervention_config.json`:

```json
{
  "enabled": true,
  "intervention_points": ["project_recommendation_agent"],
  "export_format": "json",
  "export_directory": "~/.noleet/intervention",
  "max_wait_time_seconds": 3600,
  "polling_interval_seconds": 30,
  "auto_resume_on_file_change": true,
  "create_backups": true
}
```

### Environment Variables

```bash
export NOLEET_MANUAL_INTERVENTION_ENABLED=true
export NOLEET_INTERVENTION_POINTS="project_recommendation_agent,question_analysis_agent"
export NOLEET_EXPORT_DIR="/path/to/export/dir"
export NOLEET_INTERVENTION_TIMEOUT=1800
```

## CLI Commands

### Status and Monitoring

```bash
# Show paused workflows
noleet intervention status

# Show intervention statistics
noleet intervention stats
```

### Workflow Management

```bash
# Resume a specific session
noleet intervention resume <session_id>

# Cancel intervention
noleet intervention cancel <session_id>
```

### Configuration

```bash
# Enable/disable intervention
noleet intervention config --enable
noleet intervention config --disable

# Configure agents and settings
noleet intervention config --agents project_recommendation_agent question_analysis_agent
noleet intervention config --export-dir /custom/path --timeout 7200
```

## Integration with External Tools

### Cursor Integration

1. Export data: `noleet intervention status` shows export paths
2. Open in Cursor: `cursor /path/to/exported/data.md`
3. Process and create response file
4. Resume: `noleet intervention resume <session_id>`

### ChatGPT/Claude Integration

1. Copy exported prompt content
2. Paste into ChatGPT/Claude
3. Request analysis and recommendations
4. Save response as JSON file
5. Place in intervention directory
6. Resume workflow

### Custom Scripts

```python
from noleet.manual_intervention.manual_intervention_manager import ManualInterventionManager

# Custom processing logic
manager = ManualInterventionManager()
sessions = manager.get_active_sessions()

for session_id, session_data in sessions.items():
    # Your custom logic here
    # Process data, apply business rules, etc.
    pass
```

## Agent-Specific Interventions

### Project Recommendation Agent

**Exported Data:**
- User query and selected topics
- Available projects from repository
- AI-generated analysis results

**Manual Enhancement:**
- Apply domain expertise to project selection
- Consider user skill level and learning goals
- Incorporate recent research or industry trends
- Add custom project suggestions

**Expected Output Format:**
```json
{
  "recommendations": [
    {
      "project_id": "string",
      "title": "string",
      "confidence_score": 0.0-1.0,
      "reasoning": "string",
      "key_topics": ["topic1", "topic2"],
      "estimated_complexity": "beginner|intermediate|advanced",
      "learning_objectives": ["obj1", "obj2"]
    }
  ],
  "metadata": {
    "manual_reviewer": "string",
    "review_timestamp": "ISO timestamp",
    "additional_notes": "string"
  }
}
```

### Question Analysis Agent

**Exported Data:**
- Question title and content
- Source information
- Current AI difficulty assessment
- Topic classification results

**Manual Enhancement:**
- Fine-tune difficulty assessment
- Validate topic classifications
- Add educational context
- Suggest alternative approaches

### Research Matching Agent

**Exported Data:**
- Target project requirements
- Available research papers
- Current matching scores
- Algorithm mappings

**Manual Enhancement:**
- Identify novel paper combinations
- Assess implementation feasibility
- Consider algorithmic trade-offs
- Suggest research integrations

## Advanced Usage

### Custom Intervention Logic

```python
from noleet.manual_intervention.manual_intervention_manager import ManualInterventionManager

class CustomInterventionManager(ManualInterventionManager):
    async def custom_processing_logic(self, session_data):
        # Your custom logic here
        # Apply business rules, ML models, external APIs, etc.
        pass
```

### Batch Processing

```python
# Process multiple paused sessions
paused = orchestrator.get_paused_workflows()
for workflow_sessions in paused["workflows"].values():
    for session in workflow_sessions:
        # Process each session
        resume_result = orchestrator.resume_workflow(session["session_id"])
```

### Integration with CI/CD

```bash
#!/bin/bash
# CI/CD integration example

# Run automated tests
noleet intervention config --disable
# ... run tests ...

# Enable for production recommendations
noleet intervention config --enable --agents project_recommendation_agent
```

## Monitoring and Troubleshooting

### Logging

All intervention activities are logged. Check:
- `~/.noleet/logs/intervention.log`
- Application logs for pause/resume events

### Common Issues

**Workflow doesn't pause:**
- Check if intervention is enabled: `noleet intervention config`
- Verify agent is in intervention_points list
- Check workflow execution mode

**Resume fails:**
- Verify manual input file exists and is valid JSON
- Check file naming pattern matches `manual_*.json`
- Validate JSON structure matches expected format

**Timeout issues:**
- Increase `max_wait_time_seconds` in config
- Check for file system permissions
- Monitor disk space in export directory

### Performance Considerations

- Export directory should have sufficient disk space
- Large datasets may require compression
- Consider cleanup policies for old intervention files
- Monitor polling interval vs. system resources

## Production Deployment

### Docker Integration

```dockerfile
# Add to your Dockerfile
COPY intervention_config.json /app/.noleet/
RUN mkdir -p /app/.noleet/intervention

# Environment variables
ENV NOLEET_MANUAL_INTERVENTION_ENABLED=true
ENV NOLEET_INTERVENTION_POINTS=project_recommendation_agent
```

### Kubernetes Config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: noleet-intervention-config
data:
  intervention_config.json: |
    {
      "enabled": true,
      "intervention_points": ["project_recommendation_agent"],
      "max_wait_time_seconds": 3600
    }
```

### Monitoring

```python
# Integration with monitoring systems
from noleet.manual_intervention.manual_intervention_manager import ManualInterventionManager

def monitor_interventions():
    manager = ManualInterventionManager()
    stats = manager.get_statistics()

    # Send to monitoring system
    # prometheus, datadog, etc.
    pass
```

## Security Considerations

- Intervention files may contain sensitive data
- Implement proper file permissions
- Consider encryption for sensitive exports
- Audit manual intervention logs
- Rate limit intervention requests

## Future Enhancements

- **Web Interface**: Browser-based manual intervention UI
- **Collaborative Review**: Multi-user intervention workflows
- **AI Assistance**: AI-powered suggestions during manual review
- **Template System**: Predefined intervention templates
- **Audit Trail**: Complete history of manual changes
- **A/B Testing**: Compare automated vs. manual results

---

## Demo

Run the included demo to see manual intervention in action:

```bash
python -m noleet.examples.manual_intervention_demo
```

This demonstrates the complete workflow from pause to resume with manual input.
