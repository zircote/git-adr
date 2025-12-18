"""Implementation of `git adr metrics` command.

Calculates and displays ADR health metrics.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, cast

import typer
from rich.console import Console

from git_adr.commands._shared import setup_command_context
from git_adr.core import GitError
from git_adr.core.adr import ADRStatus
from git_adr.core.index import IndexManager

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager

console = Console()
err_console = Console(stderr=True)


def run_metrics(
    format_: str = "json",
    output: str | None = None,
) -> None:
    """Export ADR metrics for dashboards.

    Args:
        format_: Export format (json, prometheus, csv).
        output: Output file path (default: stdout).

    Raises:
        typer.Exit: On error.
    """
    try:
        # Initialize command context with index manager
        ctx = setup_command_context(require_index=True)
        index_manager = cast(IndexManager, ctx.index_manager)

        # Rebuild index
        index_manager.rebuild()

        # Get all ADRs
        all_adrs = ctx.notes_manager.list_all()

        if not all_adrs:
            console.print("[dim]No ADRs found[/dim]")
            return

        # Calculate metrics
        metrics_data = _calculate_metrics(all_adrs, ctx.notes_manager)

        if format_ == "json":
            import json

            result = json.dumps(metrics_data, indent=2)
        elif format_ == "prometheus":
            result = _format_prometheus(metrics_data)
        elif format_ == "csv":
            result = _format_csv(metrics_data)
        else:
            result = json.dumps(metrics_data, indent=2)

        if output:
            Path(output).write_text(result)
            console.print(f"[green]✓[/green] Metrics written to {output}")
        else:
            console.print(result)

    except GitError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _calculate_metrics(all_adrs: list, notes_manager: NotesManager) -> dict:
    """Calculate ADR health metrics."""
    total = len(all_adrs)
    now = datetime.now()
    today = now.date()

    # Status distribution
    status_counts: Counter[str] = Counter()
    for adr in all_adrs:
        status_counts[adr.metadata.status.value] += 1

    # Calculate health score (0-100)
    # Factors:
    # - Ratio of accepted/deprecated vs draft/proposed (stability)
    # - ADRs with linked commits (traceability)
    # - Recent activity (freshness)
    # - Supersession chain integrity

    stable_statuses = {
        ADRStatus.ACCEPTED.value,
        ADRStatus.DEPRECATED.value,
        ADRStatus.SUPERSEDED.value,
    }
    stable_count = sum(status_counts.get(s, 0) for s in stable_statuses)
    stability_score = (stable_count / total * 100) if total > 0 else 0

    # Traceability: ADRs with linked commits
    linked_count = sum(1 for adr in all_adrs if adr.metadata.linked_commits)
    traceability_score = (linked_count / total * 100) if total > 0 else 0

    # Freshness: ADRs created or updated in last 90 days
    cutoff = (now - timedelta(days=90)).date()
    recent_count = sum(1 for adr in all_adrs if adr.metadata.date >= cutoff)
    freshness_score = min((recent_count / max(total / 4, 1)) * 100, 100)

    # Supersession integrity: all superseded ADRs have superseded_by set
    superseded_adrs = [a for a in all_adrs if a.metadata.status == ADRStatus.SUPERSEDED]
    supersession_ok = sum(1 for a in superseded_adrs if a.metadata.superseded_by)
    supersession_score = (
        (supersession_ok / len(superseded_adrs) * 100) if superseded_adrs else 100
    )

    # Overall health score (weighted average)
    health_score = (
        stability_score * 0.3
        + traceability_score * 0.25
        + freshness_score * 0.25
        + supersession_score * 0.2
    )

    # Velocity metrics
    velocity_7d = sum(
        1 for adr in all_adrs if adr.metadata.date >= today - timedelta(days=7)
    )
    velocity_30d = sum(
        1 for adr in all_adrs if adr.metadata.date >= today - timedelta(days=30)
    )
    velocity_90d = sum(
        1 for adr in all_adrs if adr.metadata.date >= today - timedelta(days=90)
    )

    # Monthly rate calculation
    monthly_rate = velocity_30d  # ADRs per 30 days is already monthly

    return {
        "total_adrs": total,
        "health_score": round(health_score, 1),
        "stability_score": round(stability_score, 1),
        "traceability_score": round(traceability_score, 1),
        "freshness_score": round(freshness_score, 1),
        "supersession_score": round(supersession_score, 1),
        "status_distribution": dict(status_counts),
        "adrs_with_links": linked_count,
        "recent_adrs_90d": recent_count,
        "superseded_count": len(superseded_adrs),
        "superseded_with_reference": supersession_ok,
        "velocity_7d": velocity_7d,
        "velocity_30d": velocity_30d,
        "velocity_90d": velocity_90d,
        "monthly_rate": monthly_rate,
    }


def _format_prometheus(metrics: dict) -> str:
    """Format metrics in Prometheus exposition format."""
    lines = [
        "# HELP adr_total Total number of ADRs",
        "# TYPE adr_total gauge",
        f"adr_total {metrics['total_adrs']}",
        "",
        "# HELP adr_health_score Overall health score (0-100)",
        "# TYPE adr_health_score gauge",
        f"adr_health_score {metrics['health_score']}",
        "",
        "# HELP adr_stability_score Stability score (0-100)",
        "# TYPE adr_stability_score gauge",
        f"adr_stability_score {metrics['stability_score']}",
        "",
        "# HELP adr_traceability_score Traceability score (0-100)",
        "# TYPE adr_traceability_score gauge",
        f"adr_traceability_score {metrics['traceability_score']}",
        "",
        "# HELP adr_freshness_score Freshness score (0-100)",
        "# TYPE adr_freshness_score gauge",
        f"adr_freshness_score {metrics['freshness_score']}",
        "",
        "# HELP adr_with_links ADRs with linked commits",
        "# TYPE adr_with_links gauge",
        f"adr_with_links {metrics['adrs_with_links']}",
        "",
        "# HELP adr_velocity_7d ADRs created in last 7 days",
        "# TYPE adr_velocity_7d gauge",
        f"adr_velocity_7d {metrics.get('velocity_7d', 0)}",
        "",
        "# HELP adr_velocity_30d ADRs created in last 30 days",
        "# TYPE adr_velocity_30d gauge",
        f"adr_velocity_30d {metrics.get('velocity_30d', 0)}",
        "",
        "# HELP adr_monthly_rate Average ADRs per month",
        "# TYPE adr_monthly_rate gauge",
        f"adr_monthly_rate {metrics.get('monthly_rate', 0)}",
    ]

    # Status breakdown
    for status, count in metrics.get("status_distribution", {}).items():
        lines.append(f'adr_by_status{{status="{status}"}} {count}')

    return "\n".join(lines)


def _format_csv(metrics: dict) -> str:
    """Format metrics as CSV."""
    lines = [
        "metric,value",
        f"total_adrs,{metrics['total_adrs']}",
        f"health_score,{metrics['health_score']}",
        f"stability_score,{metrics['stability_score']}",
        f"traceability_score,{metrics['traceability_score']}",
        f"freshness_score,{metrics['freshness_score']}",
        f"supersession_score,{metrics['supersession_score']}",
        f"adrs_with_links,{metrics['adrs_with_links']}",
        f"recent_adrs_90d,{metrics['recent_adrs_90d']}",
        f"velocity_7d,{metrics.get('velocity_7d', 0)}",
        f"velocity_30d,{metrics.get('velocity_30d', 0)}",
        f"velocity_90d,{metrics.get('velocity_90d', 0)}",
        f"monthly_rate,{metrics.get('monthly_rate', 0)}",
    ]
    return "\n".join(lines)
