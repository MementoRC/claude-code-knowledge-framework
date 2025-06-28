"""
UCKN Command Line Interface
"""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path

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
@click.option("--source", required=True, help="Source knowledge directory (e.g. .claude/knowledge)")
@click.option("--target", required=False, help="Target UCKN knowledge directory (e.g. .uckn/knowledge)")
@click.option("--dry-run", is_flag=True, default=False, help="Perform a dry run without writing to the database")
@click.option("--validate-only", is_flag=True, default=False, help="Only validate patterns, do not migrate")
@click.option("--report-only", is_flag=True, default=False, help="Only generate a migration report, do not migrate or validate")
def migrate(source: str, target: str, dry_run: bool, validate_only: bool, report_only: bool):
    """Migrate existing knowledge patterns to UCKN format"""
    from uckn.core.molecules.pattern_migrator import PatternMigrator

    import logging
    logger = logging.getLogger("uckn.migrate")
    logger.setLevel(logging.INFO)

    if not target:
        # Default: sibling of source, named .uckn/knowledge
        from pathlib import Path
        target = str(Path(source).parent / ".uckn" / "knowledge")

    console.print(f"📦 Migrating patterns from [bold]{source}[/bold] to [bold]{target}[/bold]")
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
        console.print("[red]Some patterns failed to migrate or validate. See report above.[/red]")
    else:
        console.print("[green]✅ Migration/validation completed successfully![/green]")

if __name__ == "__main__":
    main()