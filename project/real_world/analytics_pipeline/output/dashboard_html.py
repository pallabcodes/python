"""
HTML dashboard interface for the analytics pipeline.

This module contains the DashboardInterface class which provides HTML
and JSON interfaces for dashboard visualization.
"""

import json
from typing import Dict, Any
from datetime import datetime

from .dashboard_metrics import MetricsDashboard


class DashboardInterface:
    """Web interface for the dashboard."""

    def __init__(self, dashboard: MetricsDashboard):
        """Initialize dashboard interface.

        Args:
            dashboard: Metrics dashboard instance
        """
        self.dashboard = dashboard

    def get_html_dashboard(self) -> str:
        """Generate HTML dashboard page.

        Returns:
            HTML string for dashboard
        """
        current_metrics = self.dashboard.get_current_metrics() or {}
        active_alerts = self.dashboard.get_active_alerts()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.dashboard.config.title}</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="{self.dashboard.config.refresh_interval}">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .alert {{ border-left: 5px solid; padding: 10px; margin: 10px 0; }}
                .alert-critical {{ border-color: #ff0000; background: #ffe6e6; }}
                .alert-error {{ border-color: #ff6600; background: #fff2e6; }}
                .alert-warning {{ border-color: #ffcc00; background: #fffde6; }}
                .alert-info {{ border-color: #0066ff; background: #e6f2ff; }}
                .status-good {{ color: #00aa00; }}
                .status-bad {{ color: #aa0000; }}
            </style>
        </head>
        <body>
            <h1>{self.dashboard.config.title}</h1>

            <div class="metric">
                <h2>Pipeline Status</h2>
                <p><strong>Status:</strong>
                    <span class="{'status-good' if current_metrics.get('pipeline_running') else 'status-bad'}">
                        {'Running' if current_metrics.get('pipeline_running') else 'Stopped'}
                    </span>
                </p>
                <p><strong>Uptime:</strong> {current_metrics.get('uptime', 0):.1f} seconds</p>
                <p><strong>Total Messages:</strong> {current_metrics.get('total_messages_processed', 0)}</p>
                <p><strong>Error Count:</strong> {current_metrics.get('error_count', 0)}</p>
                <p><strong>Active Stages:</strong> {current_metrics.get('active_stages', 0)}</p>
                <p><strong>Messages/sec:</strong> {current_metrics.get('messages_per_second', 0):.2f}</p>
                <p><strong>Error Rate:</strong> {current_metrics.get('error_rate', 0):.3f}</p>
            </div>

            <div class="metric">
                <h2>Stage Health</h2>
                <p><strong>Healthy Stages:</strong> {current_metrics.get('healthy_stages', 0)} / {current_metrics.get('total_stages', 0)}</p>
            </div>

            <div class="metric">
                <h2>Storage Status</h2>
                <p><strong>Active Connections:</strong> {current_metrics.get('total_storage_connections', 0)}</p>
            </div>
        """

        if active_alerts:
            html += '<div class="metric"><h2>Active Alerts</h2>'
            for alert in active_alerts:
                severity_class = f"alert-{alert['severity']}"
                html += f'''
                <div class="alert {severity_class}">
                    <strong>{alert['name']}</strong>: {alert['message']}
                    <br><small>{datetime.fromtimestamp(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</small>
                </div>
                '''
            html += '</div>'

        html += f"""
            <div class="metric">
                <h2>System Info</h2>
                <p><strong>Last Update:</strong> {datetime.fromtimestamp(self.dashboard.last_update).strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>History Size:</strong> {len(self.dashboard.metrics_history)}</p>
            </div>

            <script>
                // Auto-refresh functionality
                setTimeout(function() {{
                    location.reload();
                }}, {self.dashboard.config.refresh_interval * 1000});
            </script>
        </body>
        </html>
        """

        return html

    def get_json_dashboard(self) -> str:
        """Get dashboard data as JSON.

        Returns:
            JSON string of dashboard data
        """
        return json.dumps(self.dashboard.get_dashboard_data(), indent=2, default=str)

    def get_metrics_chart_data(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """Get chart data for a specific metric.

        Args:
            metric_name: Name of metric to chart
            hours: Hours of history to include

        Returns:
            Chart data dictionary
        """
        history = self.dashboard.get_metrics_history(hours)

        timestamps = []
        values = []

        for snapshot in history:
            metrics = snapshot['metrics']
            if metric_name in metrics:
                timestamps.append(snapshot['timestamp'])
                values.append(metrics[metric_name])

        return {
            'metric': metric_name,
            'timestamps': timestamps,
            'values': values,
            'hours': hours
        }