#!/usr/bin/env python3
"""
Monitoring setup script for NoLeet.
Helps initialize and configure the monitoring stack.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringSetup:
    """Setup and manage the NoLeet monitoring stack."""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.monitoring_dir = self.base_dir / "monitoring"

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        required_commands = ['docker', 'docker-compose']

        missing = []
        for cmd in required_commands:
            if not self._command_exists(cmd):
                missing.append(cmd)

        if missing:
            logger.error(f"Missing required commands: {', '.join(missing)}")
            logger.info("Please install Docker and Docker Compose first.")
            return False

        return True

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        try:
            subprocess.run([command, '--version'],
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_directories(self):
        """Create necessary directories for monitoring."""
        directories = [
            'grafana/provisioning/datasources',
            'grafana/provisioning/dashboards',
            'grafana/dashboards',
            'elk/logstash/config',
            'prometheus/rules'
        ]

        for dir_path in directories:
            full_path = self.monitoring_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")

    def setup_grafana_provisioning(self):
        """Setup Grafana provisioning configuration."""
        # Create datasource provisioning
        datasource_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090",
                    "isDefault": True,
                    "editable": True
                }
            ]
        }

        datasource_file = self.monitoring_dir / "grafana/provisioning/datasources/prometheus.yml"
        self._write_yaml(datasource_config, datasource_file)

        # Create dashboard provisioning
        dashboard_config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "noleet-dashboards",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/var/lib/grafana/dashboards"
                    }
                }
            ]
        }

        dashboard_file = self.monitoring_dir / "grafana/provisioning/dashboards/noleet.yml"
        self._write_yaml(dashboard_config, dashboard_file)

    def setup_logstash_config(self):
        """Setup Logstash configuration."""
        logstash_config = """
http.host: "0.0.0.0"
path.config: /usr/share/logstash/pipeline
"""

        config_file = self.monitoring_dir / "elk/logstash/config/logstash.yml"
        with open(config_file, 'w') as f:
            f.write(logstash_config.strip())

    def _write_yaml(self, data: dict, file_path: Path):
        """Write data as YAML file."""
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML is required for setup. Install with: pip install PyYAML")
            return

        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

        logger.info(f"Created configuration file: {file_path}")

    def start_monitoring_stack(self, detached: bool = True):
        """Start the monitoring stack."""
        os.chdir(self.monitoring_dir)

        cmd = ['docker-compose', 'up']
        if detached:
            cmd.append('-d')

        logger.info("Starting monitoring stack...")
        try:
            subprocess.run(cmd, check=True)
            logger.info("Monitoring stack started successfully!")
            self._print_access_info()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start monitoring stack: {e}")
            sys.exit(1)

    def stop_monitoring_stack(self):
        """Stop the monitoring stack."""
        os.chdir(self.monitoring_dir)

        logger.info("Stopping monitoring stack...")
        try:
            subprocess.run(['docker-compose', 'down'], check=True)
            logger.info("Monitoring stack stopped successfully!")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop monitoring stack: {e}")
            sys.exit(1)

    def restart_monitoring_stack(self):
        """Restart the monitoring stack."""
        self.stop_monitoring_stack()
        self.start_monitoring_stack()

    def _print_access_info(self):
        """Print access information for monitoring services."""
        access_info = """
Monitoring stack is now running! Access the services at:

📊 Grafana (Dashboards):     http://localhost:3000
   Username: admin
   Password: admin

📈 Prometheus (Metrics):     http://localhost:9090
🚨 Alertmanager (Alerts):    http://localhost:9093
🔍 Kibana (Logs):           http://localhost:5601
📄 Elasticsearch:           http://localhost:9200

📊 Application Metrics:     http://localhost:8000/metrics
"""

        print(access_info)

    def setup_all(self):
        """Setup all monitoring components."""
        logger.info("Setting up NoLeet monitoring stack...")

        if not self.check_dependencies():
            sys.exit(1)

        self.create_directories()
        self.setup_grafana_provisioning()
        self.setup_logstash_config()

        logger.info("Monitoring setup complete!")
        logger.info("Run 'python setup_monitoring.py start' to start the monitoring stack.")


def main():
    parser = argparse.ArgumentParser(description="NoLeet Monitoring Setup")
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'restart'],
                       help='Action to perform')
    parser.add_argument('--attached', action='store_true',
                       help='Run in attached mode (not detached)')

    args = parser.parse_args()

    setup = MonitoringSetup()

    if args.action == 'setup':
        setup.setup_all()
    elif args.action == 'start':
        setup.start_monitoring_stack(detached=not args.attached)
    elif args.action == 'stop':
        setup.stop_monitoring_stack()
    elif args.action == 'restart':
        setup.restart_monitoring_stack()


if __name__ == '__main__':
    main()
