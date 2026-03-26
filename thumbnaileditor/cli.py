from pathlib import Path

import click

from .config import config
from .project import discover_projects, load_project
from .render import render_thumbnail


@click.group()
def cli():
    """Thumbnail editor for FullControlMTG videos."""


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Validate config without rendering.")
@click.option("--output", "-o", default=None, help="Override output file path.")
def render(project_path: str, dry_run: bool, output: str | None):
    """Render a thumbnail for a single PROJECT_PATH folder."""
    project_dir, project_config = load_project(project_path)
    click.echo(f"Project : {project_dir.name}")
    click.echo(f"Title   : {project_config.title}")
    click.echo(f"Cards   : {len(project_config.foreground_cards)} foreground card(s)")

    if dry_run:
        click.echo("Dry run — skipping render.")
        return

    image = render_thumbnail(project_config, config)

    out_path = Path(output) if output else _default_output_path(project_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, format="PNG")
    click.echo(f"Saved   : {out_path}")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Validate all configs without rendering.")
def batch(dry_run: bool):
    """Render thumbnails for all projects in the configured projects folder."""
    projects = discover_projects(config.projects_folder)

    if not projects:
        click.echo(f"No projects found in {config.projects_folder}")
        return

    click.echo(f"Found {len(projects)} project(s)")
    for project_dir in projects:
        try:
            _, project_config = load_project(project_dir)
            click.echo(f"\n[{project_dir.name}]")

            if dry_run:
                click.echo(f"  Title : {project_config.title} — OK")
                continue

            image = render_thumbnail(project_config, config)
            out_path = _default_output_path(project_dir)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(out_path, format="PNG")
            click.echo(f"  Saved : {out_path}")

        except Exception as e:
            click.echo(f"  ERROR : {e}", err=True)


def _default_output_path(project_dir: Path) -> Path:
    return Path(config.output_folder) / f"{project_dir.name}.png"
