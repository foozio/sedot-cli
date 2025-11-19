from __future__ import annotations

from pathlib import Path
from typing import Annotated

import requests
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .downloader import DownloadResult, VideoDownloader
from .fetchers import ScrapeError, VideoMetadata

console = Console()


def _version_callback(value: bool):
    if value:
        console.print(f"sedot v{__version__}")
        raise typer.Exit()


def _print_metadata(metadata: VideoMetadata):
    table = Table(title="Metadata", show_edge=False, show_header=False, pad_edge=False)
    table.add_row("Platform", metadata.platform)
    table.add_row("Title", metadata.title or "-")
    table.add_row("Caption", (metadata.caption or "-")[:200])
    table.add_row("Video URL", metadata.video_url)
    table.add_row("Filename", metadata.filename)
    console.print(table)


def main(
    urls: Annotated[
        list[str],
        typer.Argument(
            ...,
            help="Instagram/Threads post URLs to download. Provide multiple URLs separated by spaces.",
            metavar="URL",
            min=1,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory where the videos will be stored.",
            metavar="DIR",
        ),
    ] = Path("downloads"),
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", help="Replace files that already exist."),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Only fetch metadata without downloading the video."),
    ] = False,
    show_metadata: Annotated[
        bool,
        typer.Option("--show-metadata", help="Print metadata before downloading."),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show sedot version and exit.",
        ),
    ] = False,
):
    downloader = VideoDownloader()
    success: list[DownloadResult] = []
    failures: list[tuple[str, str]] = []

    for url in urls:
        console.print(f"[bold]Processing[/bold] {url}")
        try:
            metadata = downloader.fetch_metadata(url)
            if dry_run or show_metadata:
                _print_metadata(metadata)
            if dry_run:
                continue
            result = downloader.download(metadata, output_dir=output, overwrite=overwrite)
            console.print(f"[green]Saved to[/green] {result.output_path}")
            success.append(result)
        except FileExistsError as exc:
            console.print(f"[yellow]Skipping:[/yellow] {exc}")
            failures.append((url, str(exc)))
        except ScrapeError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            failures.append((url, str(exc)))
        except requests.HTTPError as exc:
            console.print(f"[red]HTTP error while downloading {url}: {exc}")
            failures.append((url, f"HTTP error {exc.response.status_code if exc.response else ''}"))
        except requests.RequestException as exc:
            console.print(f"[red]Network error while downloading {url}: {exc}")
            failures.append((url, str(exc)))

    console.print()
    if success:
        table = Table(title="Downloads", show_edge=False)
        table.add_column("File")
        table.add_column("Source")
        for result in success:
            table.add_row(str(result.output_path), result.metadata.source_url)
        console.print(table)
    if failures:
        console.print(f"[red]{len(failures)} download(s) failed.[/red]")
    else:
        console.print("[green]All downloads completed successfully.[/green]")


def run():
    typer.run(main)


if __name__ == "__main__":
    run()
