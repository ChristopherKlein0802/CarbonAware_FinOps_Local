"""
CLI entry point for Carbon-Aware FinOps.
"""

import click
import logging
from datetime import datetime, timedelta

from .automation.shutdown_scheduler import ShutdownScheduler
from .reporting.dashboard import CarbonFinOpsDashboard

logging.basicConfig(level=logging.INFO)

@click.group()
def cli():
    """Carbon-Aware FinOps CLI."""
    pass

@cli.command()
@click.option('--region', default='eu-central-1', help='AWS region')
def schedule():
    """Run scheduling automation."""
    scheduler = ShutdownScheduler(region)
    results = scheduler.execute_schedule()
    click.echo(f"Scheduling complete: {results}")

@cli.command()
@click.option('--days', default=7, help='Number of days for report')
@click.option('--output', default='data/reports/report.html', help='Output file')
def report(days, output):
    """Generate cost and carbon report."""
    dashboard = CarbonFinOpsDashboard()
    # Implementation for report generation
    click.echo(f"Report generated: {output}")

if __name__ == '__main__':
    cli()