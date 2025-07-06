"""
UCKN Command Line Interface
"""

import click
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich import box
from pathlib import Path
import json
import sys

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="uckn")
def main():
    """Universal Claude Code Knowledge Network (UCKN) CLI"""
    pass


@main.command()
@click.option("--template", default="python-ml", help="Project template to use")
@click.argument("project_name", required=False)
def init(template: str, project_name: str):
    """Initialize a new UCKN-enabled project"""
    if not project_name:
        project_name = Path.cwd().name

    console.print(f"🚀 Initializing UCKN project: {project_name}")
    console.print(f"📋 Using template: {template}")

    # TODO: Implement project initialization
    console.print("✅ Project initialized successfully!")


@main.command()
@click.argument("path", default=".")
def analyze(path: str):
    """Analyze project for technology stack and patterns"""
    console.print(f"🔍 Analyzing project at: {path}")

    # TODO: Implement project analysis
    table = Table(title="Technology Stack Analysis")
    table.add_column("Component", style="cyan")
    table.add_column("Detected", style="green")
    table.add_column("Version", style="yellow")

    table.add_row("Language", "Python", "3.11")
    table.add_row("Package Manager", "Pixi", "0.30.0")
    table.add_row("Testing", "pytest", "7.4.0")

    console.print(table)


@main.command()
@click.argument("query")
@click.option("--limit", default=10, help="Number of results to return")
def search(query: str, limit: int):
    """Search knowledge patterns"""
    console.print(f"🔍 Searching for: {query}")

    # TODO: Implement pattern search
    console.print("📚 Found 3 relevant patterns:")
    console.print("1. Python CI/CD setup with Poetry")
    console.print("2. PyTest configuration best practices")
    console.print("3. GitHub Actions for Python projects")


@main.command()
@click.option(
    "--source",
    required=True,
    help="Source knowledge directory (e.g. .claude/knowledge)",
)
@click.option(
    "--target",
    required=False,
    help="Target UCKN knowledge directory (e.g. .uckn/knowledge)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Perform a dry run without writing to the database",
)
@click.option(
    "--validate-only",
    is_flag=True,
    default=False,
    help="Only validate patterns, do not migrate",
)
@click.option(
    "--report-only",
    is_flag=True,
    default=False,
    help="Only generate a migration report, do not migrate or validate",
)
def migrate(
    source: str, target: str, dry_run: bool, validate_only: bool, report_only: bool
):
    """Migrate existing knowledge patterns to UCKN format"""
    from uckn.core.molecules.pattern_migrator import PatternMigrator

    import logging

    logger = logging.getLogger("uckn.migrate")
    logger.setLevel(logging.INFO)

    if not target:
        # Default: sibling of source, named .uckn/knowledge
        from pathlib import Path

        target = str(Path(source).parent / ".uckn" / "knowledge")

    console.print(
        f"📦 Migrating patterns from [bold]{source}[/bold] to [bold]{target}[/bold]"
    )
    if dry_run:
        console.print("[yellow]Dry run mode: No data will be written.[/yellow]")
    if validate_only:
        console.print("[yellow]Validation only: No data will be migrated.[/yellow]")
    if report_only:
        console.print("[yellow]Report only: Only a report will be generated.[/yellow]")

    migrator = PatternMigrator(
        source_dir=source,
        target_dir=target,
        dry_run=dry_run,
        validate_only=validate_only,
        report_only=report_only,
        logger=logger,
        console=console,
    )

    if report_only:
        report = migrator.report_only_mode()
    elif validate_only:
        report = migrator.validate()
    else:
        report = migrator.migrate()
    report.print_report(console=console)
    if report.failed or report.errors:
        console.print(
            "[red]Some patterns failed to migrate or validate. See report above.[/red]"
        )
    else:
        console.print("[green]✅ Migration/validation completed successfully![/green]")


# --- Analytics CLI Integration ---


def get_pattern_analytics():
    try:
        from uckn.core.molecules.pattern_analytics import PatternAnalytics
        from uckn.storage.chromadb_connector import ChromaDBConnector

        chroma_connector = ChromaDBConnector()
        return PatternAnalytics(chroma_connector)
    except ImportError as e:
        console.print(
            f"[red]PatternAnalytics molecule not found: {e}. Please ensure it is installed.[/red]"
        )
        sys.exit(1)


def print_json_or_table(data, json_flag, table_title=None, columns=None, row_fn=None):
    if json_flag:
        console.print(JSON.from_data(data))
    else:
        if columns and row_fn:
            table = Table(title=table_title, box=box.SIMPLE)
            for col, style in columns:
                table.add_column(col, style=style)
            for row in data:
                table.add_row(*row_fn(row))
            console.print(table)
        else:
            console.print(data)


@click.group()
def analytics():
    """Analytics commands for UCKN patterns"""
    pass


@analytics.command("pattern")
@click.argument("pattern_id")
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def analytics_pattern(pattern_id, json_flag):
    """Show metrics for a specific pattern"""
    analytics = get_pattern_analytics()
    try:
        metrics = analytics.get_pattern_metrics(pattern_id)
        if not metrics:
            console.print(
                f"[yellow]No metrics found for pattern: {pattern_id}[/yellow]"
            )
            return
        if json_flag:
            console.print(JSON.from_data(metrics))
        else:
            table = Table(title=f"Pattern Metrics: {pattern_id}", box=box.SIMPLE)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for key, value in metrics.items():
                table.add_row(str(key), str(value))
            console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching pattern metrics: {e}[/red]")


@analytics.command("top")
@click.option("--limit", default=10, help="Number of top patterns to show")
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def analytics_top(limit, json_flag):
    """Show top performing patterns"""
    analytics = get_pattern_analytics()
    try:
        top_patterns = analytics.get_top_performing_patterns(top_n=limit)
        if not top_patterns:
            console.print("[yellow]No top patterns found.[/yellow]")
            return
        print_json_or_table(
            top_patterns,
            json_flag,
            table_title="Top Performing Patterns",
            columns=[
                ("Pattern ID", "cyan"),
                ("Quality Score", "green"),
                ("Applications", "yellow"),
                ("Last Applied", "magenta"),
            ],
            row_fn=lambda p: (
                str(p.get("pattern_id", "")),
                f"{p.get('quality_score', 0):.2f}",
                str(p.get("application_count", 0)),
                "N/A",  # last_applied not available in current implementation
            ),
        )
    except Exception as e:
        console.print(f"[red]Error fetching top patterns: {e}[/red]")


@analytics.command("problematic")
@click.option("--threshold", default=0.5, help="Success rate threshold")
@click.option("--min-applications", default=1, help="Minimum number of applications")
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def analytics_problematic(threshold, min_applications, json_flag):
    """Show problematic patterns"""
    analytics = get_pattern_analytics()
    try:
        problematic = analytics.get_problematic_patterns(
            threshold=threshold, min_applications=min_applications
        )
        if not problematic:
            console.print("[green]No problematic patterns found.[/green]")
            return
        print_json_or_table(
            problematic,
            json_flag,
            table_title="Problematic Patterns",
            columns=[
                ("Pattern ID", "cyan"),
                ("Success Rate", "red"),
                ("Applications", "yellow"),
                ("Last Applied", "magenta"),
            ],
            row_fn=lambda p: (
                str(p.get("pattern_id", "")),
                f"{p.get('success_rate', 0):.2f}",
                str(p.get("application_count", 0)),
                "N/A",  # last_applied not available in current implementation
            ),
        )
    except Exception as e:
        console.print(f"[red]Error fetching problematic patterns: {e}[/red]")


@analytics.command("trends")
@click.argument("pattern_id")
@click.option("--days", default=30, help="Number of days for trend analysis")
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def analytics_trends(pattern_id, days, json_flag):
    """Show trend analysis for a pattern"""
    analytics = get_pattern_analytics()
    try:
        trends = analytics.get_trend_analysis(pattern_id, days=days)
        if not trends:
            console.print(
                f"[yellow]No trend data found for pattern: {pattern_id}[/yellow]"
            )
            return
        if json_flag:
            console.print(JSON.from_data(trends))
        else:
            table = Table(
                title=f"Trend Analysis: {pattern_id} (Last {days} days)", box=box.SIMPLE
            )
            table.add_column("Date", style="cyan")
            table.add_column("Applications", style="yellow")
            table.add_column("Success Rate", style="green")
            for entry in trends:
                table.add_row(
                    str(entry.get("date", "")),
                    str(entry.get("count", "")),
                    f"{entry.get('success_rate', 0):.2f}"
                    if entry.get("success_rate") is not None
                    else "N/A",
                )
            console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching trend analysis: {e}[/red]")


@analytics.command("batch-update")
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def analytics_batch_update(json_flag):
    """Batch update all pattern metrics"""
    analytics = get_pattern_analytics()
    try:
        analytics.batch_update_all_pattern_metrics()
        result = {"updated": "completed"}
        if json_flag:
            console.print(JSON.from_data(result))
        else:
            console.print("[green]Batch update completed for all patterns.[/green]")
    except Exception as e:
        console.print(f"[red]Error during batch update: {e}[/red]")


# --- Application Tracking Commands ---


@main.command("track-application")
@click.argument("pattern_id")
@click.option(
    "--context",
    default="{}",
    help='Context JSON (e.g. \'{"technology_stack": ["python"]}\')',
)
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def track_application(pattern_id, context, json_flag):
    """Record a pattern application event"""
    analytics = get_pattern_analytics()
    try:
        context_obj = {}
        if context:
            try:
                context_obj = json.loads(context)
            except Exception as e:
                console.print(f"[red]Invalid context JSON: {e}[/red]")
                return
        application_id = analytics.record_application(pattern_id, context_obj)
        if not application_id:
            console.print("[red]Failed to record application.[/red]")
            return
        result = {
            "application_id": application_id,
            "pattern_id": pattern_id,
            "status": "recorded",
        }
        if json_flag:
            console.print(JSON.from_data(result))
        else:
            console.print(
                f"[green]Application recorded! Application ID: {application_id}[/green]"
            )
    except Exception as e:
        console.print(f"[red]Error recording application: {e}[/red]")


@main.command("record-outcome")
@click.argument("application_id")
@click.argument("outcome")
@click.option(
    "--time", "time_taken", type=float, required=False, help="Time taken (seconds)"
)
@click.option("--json", "json_flag", is_flag=True, help="Output as JSON")
def record_outcome(application_id, outcome, time_taken, json_flag):
    """Record the outcome of a pattern application"""
    analytics = get_pattern_analytics()
    try:
        success = analytics.record_outcome(application_id, outcome, time_taken)
        if not success:
            console.print("[red]Failed to record outcome.[/red]")
            return
        result = {
            "application_id": application_id,
            "outcome": outcome,
            "status": "recorded",
        }
        if json_flag:
            console.print(JSON.from_data(result))
        else:
            console.print(
                f"[green]Outcome '{outcome}' recorded for application {application_id}![/green]"
            )
    except Exception as e:
        console.print(f"[red]Error recording outcome: {e}[/red]")


# Register analytics group
main.add_command(analytics)

if __name__ == "__main__":
    main()
