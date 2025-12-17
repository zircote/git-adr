"""Index Manager for git-adr.

This module provides fast indexing and querying of ADRs.
The index is built from git notes and cached for performance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

from git_adr.core.adr import ADR, ADRMetadata, ADRStatus

if TYPE_CHECKING:
    from git_adr.core.notes import NotesManager


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """An entry in the ADR index.

    Contains just the metadata needed for listing and filtering,
    without the full ADR content.
    """

    id: str
    title: str
    date: date
    status: ADRStatus
    tags: tuple[str, ...]
    linked_commits: tuple[str, ...]
    supersedes: str | None = None
    superseded_by: str | None = None

    @classmethod
    def from_metadata(cls, metadata: ADRMetadata) -> IndexEntry:
        """Create an index entry from ADR metadata.

        Args:
            metadata: ADR metadata.

        Returns:
            Index entry.
        """
        return cls(
            id=metadata.id,
            title=metadata.title,
            date=metadata.date,
            status=metadata.status,
            tags=tuple(metadata.tags),
            linked_commits=tuple(metadata.linked_commits),
            supersedes=metadata.supersedes,
            superseded_by=metadata.superseded_by,
        )

    @classmethod
    def from_adr(cls, adr: ADR) -> IndexEntry:
        """Create an index entry from a full ADR.

        Args:
            adr: Full ADR.

        Returns:
            Index entry.
        """
        return cls.from_metadata(adr.metadata)


@dataclass
class QueryResult:
    """Result of an index query.

    Contains matching entries and metadata about the query.
    """

    entries: list[IndexEntry]
    total_count: int
    filtered_count: int

    @property
    def has_results(self) -> bool:
        """Check if query returned any results."""
        return len(self.entries) > 0


@dataclass
class SearchMatch:
    """A search result with context.

    Contains the matching ADR entry and highlighted snippets.
    """

    entry: IndexEntry
    snippets: list[str] = field(default_factory=list)
    score: float = 0.0


class IndexManager:
    """Manages the ADR index for fast queries.

    The index is built from git notes and provides efficient
    filtering and searching without reading all ADR content.
    """

    def __init__(self, notes_manager: NotesManager) -> None:
        """Initialize the index manager.

        Args:
            notes_manager: Notes manager for ADR access.
        """
        self._notes = notes_manager
        self._entries: dict[str, IndexEntry] = {}
        self._adr_cache: dict[str, ADR] = {}  # Cache full ADRs for search
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Ensure the index is loaded from notes."""
        if self._loaded:
            return

        self._entries.clear()
        self._adr_cache.clear()

        # Load all ADRs and build index + cache
        adrs = self._notes.list_all()
        for adr in adrs:
            entry = IndexEntry.from_adr(adr)
            self._entries[entry.id] = entry
            self._adr_cache[adr.id] = adr  # Cache full ADR for search

        self._loaded = True

    def get_cached_adr(self, adr_id: str) -> ADR | None:
        """Get a cached ADR by ID.

        This avoids re-fetching ADRs that were already loaded during index build.

        Args:
            adr_id: ADR ID to retrieve.

        Returns:
            Cached ADR instance, or None if not found.
        """
        self._ensure_loaded()
        return self._adr_cache.get(adr_id)

    def invalidate(self) -> None:
        """Invalidate the index cache.

        Call this after adding, updating, or removing ADRs.
        """
        self._loaded = False
        self._entries.clear()
        self._adr_cache.clear()

    def rebuild(self) -> int:
        """Force rebuild of the index.

        Returns:
            Number of entries in the rebuilt index.
        """
        self.invalidate()
        self._ensure_loaded()
        return len(self._entries)

    # =========================================================================
    # Query Operations
    # =========================================================================

    def get(self, adr_id: str) -> IndexEntry | None:
        """Get an index entry by ADR ID.

        Args:
            adr_id: ADR ID.

        Returns:
            Index entry, or None if not found.
        """
        self._ensure_loaded()
        return self._entries.get(adr_id)

    def list_all(
        self,
        *,
        reverse: bool = False,
    ) -> list[IndexEntry]:
        """List all index entries.

        Args:
            reverse: If True, return in reverse chronological order.

        Returns:
            List of all index entries.
        """
        self._ensure_loaded()
        entries = list(self._entries.values())
        entries.sort(key=lambda e: (e.date, e.id), reverse=not reverse)
        return entries

    def query(
        self,
        *,
        status: ADRStatus | str | None = None,
        tag: str | None = None,
        since: date | None = None,
        until: date | None = None,
        has_linked_commits: bool | None = None,
        reverse: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> QueryResult:
        """Query the index with filters.

        Args:
            status: Filter by status.
            tag: Filter by tag.
            since: Filter by date (inclusive).
            until: Filter by date (inclusive).
            has_linked_commits: Filter by presence of linked commits.
            reverse: If True, return in reverse chronological order.
            limit: Maximum number of results.
            offset: Skip this many results.

        Returns:
            Query result with matching entries.
        """
        self._ensure_loaded()

        # Start with all entries
        entries = list(self._entries.values())
        total_count = len(entries)

        # Apply filters
        if status is not None:
            if isinstance(status, str):
                status = ADRStatus.from_string(status)
            entries = [e for e in entries if e.status == status]

        if tag is not None:
            tag_lower = tag.lower()
            entries = [e for e in entries if tag_lower in [t.lower() for t in e.tags]]

        if since is not None:
            entries = [e for e in entries if e.date >= since]

        if until is not None:
            entries = [e for e in entries if e.date <= until]

        if has_linked_commits is not None:
            if has_linked_commits:
                entries = [e for e in entries if e.linked_commits]
            else:
                entries = [e for e in entries if not e.linked_commits]

        filtered_count = len(entries)

        # Sort
        entries.sort(key=lambda e: (e.date, e.id), reverse=not reverse)

        # Apply pagination
        if offset > 0:
            entries = entries[offset:]
        if limit is not None:
            entries = entries[:limit]

        return QueryResult(
            entries=entries,
            total_count=total_count,
            filtered_count=filtered_count,
        )

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search(
        self,
        query: str,
        *,
        status: ADRStatus | str | None = None,
        tag: str | None = None,
        case_sensitive: bool = False,
        regex: bool = False,
        context_lines: int = 2,
        limit: int | None = None,
    ) -> list[SearchMatch]:
        """Full-text search across ADRs.

        Args:
            query: Search query string.
            status: Filter by status.
            tag: Filter by tag.
            case_sensitive: If True, match case exactly.
            regex: If True, treat query as regular expression.
            context_lines: Number of context lines in snippets.
            limit: Maximum number of results.

        Returns:
            List of search matches with snippets.
        """
        self._ensure_loaded()

        # Get filtered entries
        result = self.query(status=status, tag=tag)
        entries = result.entries

        matches: list[SearchMatch] = []

        # Compile search pattern
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(query, flags)
            except re.error:
                # Invalid regex, treat as literal
                pattern = re.compile(re.escape(query), flags)
        else:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(query), flags)

        for entry in entries:
            # Get full ADR content from cache (avoids re-fetching)
            adr = self._adr_cache.get(entry.id)
            if adr is None:
                continue

            # Search in title and content
            full_text = f"{adr.title}\n{adr.content}"
            all_matches = list(pattern.finditer(full_text))

            if not all_matches:
                continue

            # Generate snippets
            snippets = self._generate_snippets(
                full_text,
                all_matches,
                context_lines,
            )

            # Calculate relevance score
            score = self._calculate_score(entry, adr, all_matches)

            matches.append(SearchMatch(entry=entry, snippets=snippets, score=score))

        # Sort by relevance
        matches.sort(key=lambda m: m.score, reverse=True)

        # Apply limit
        if limit is not None:
            matches = matches[:limit]

        return matches

    def _generate_snippets(
        self,
        text: str,
        matches: list[re.Match[str]],
        context_lines: int,
    ) -> list[str]:
        """Generate context snippets around matches.

        Args:
            text: Full text that was searched.
            matches: List of regex matches.
            context_lines: Number of context lines.

        Returns:
            List of snippet strings.
        """
        lines = text.split("\n")
        snippets: list[str] = []
        seen_ranges: set[tuple[int, int]] = set()

        for match in matches[:5]:  # Limit snippets
            # Find line number of match
            match_start = match.start()
            line_num = text[:match_start].count("\n")

            # Calculate context range
            start = max(0, line_num - context_lines)
            end = min(len(lines), line_num + context_lines + 1)

            # Skip if we've already shown this range
            range_key = (start, end)
            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            # Generate snippet with highlighting
            snippet_lines = []
            for i in range(start, end):
                line = lines[i]
                marker = ">" if i == line_num else " "
                snippet_lines.append(f"{marker} {line}")

            snippets.append("\n".join(snippet_lines))

        return snippets

    def _calculate_score(
        self,
        entry: IndexEntry,
        adr: ADR,
        matches: list[re.Match[str]],
    ) -> float:
        """Calculate relevance score for a search match.

        Args:
            entry: Index entry.
            adr: Full ADR.
            matches: List of regex matches.

        Returns:
            Relevance score (higher is better).
        """
        score = 0.0

        # Base score from number of matches
        score += len(matches) * 1.0

        # Boost for title matches
        title_lower = adr.title.lower()
        for match in matches:
            match_text = match.group().lower()
            if match_text in title_lower:
                score += 5.0

        # Boost for recent ADRs
        from datetime import date as date_type

        days_old = (date_type.today() - entry.date).days
        recency_boost = max(0, 1.0 - (days_old / 365))
        score += recency_boost

        # Boost for accepted status
        if entry.status == ADRStatus.ACCEPTED:
            score += 2.0

        # Boost for having linked commits
        score += len(entry.linked_commits) * 0.5

        return score

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the indexed ADRs.

        Returns:
            Dictionary with count statistics.
        """
        self._ensure_loaded()

        stats: dict[str, int] = {
            "total": len(self._entries),
        }

        # Count by status
        for status in ADRStatus:
            count = sum(1 for e in self._entries.values() if e.status == status)
            stats[f"status_{status.value}"] = count

        # Count with linked commits
        stats["with_linked_commits"] = sum(
            1 for e in self._entries.values() if e.linked_commits
        )

        # Count superseded relationships
        stats["superseded"] = sum(1 for e in self._entries.values() if e.superseded_by)

        return stats

    def get_tags(self) -> dict[str, int]:
        """Get all tags with their usage counts.

        Returns:
            Dictionary mapping tag to count.
        """
        self._ensure_loaded()

        tags: dict[str, int] = {}
        for entry in self._entries.values():
            for tag in entry.tags:
                tags[tag] = tags.get(tag, 0) + 1

        return dict(sorted(tags.items(), key=lambda x: (-x[1], x[0])))

    def get_recent(self, days: int = 30, limit: int = 10) -> list[IndexEntry]:
        """Get recently created or updated ADRs.

        Args:
            days: Look back this many days.
            limit: Maximum number to return.

        Returns:
            List of recent index entries.
        """
        from datetime import timedelta

        since = date.today() - timedelta(days=days)
        result = self.query(since=since, limit=limit, reverse=True)
        return result.entries

    def get_needs_attention(self) -> list[IndexEntry]:
        """Get ADRs that may need attention.

        Returns ADRs that are:
        - Proposed for more than 30 days
        - Deprecated but not superseded
        - Have no linked commits (possibly orphaned)

        Returns:
            List of entries needing attention.
        """
        self._ensure_loaded()
        from datetime import timedelta

        thirty_days_ago = date.today() - timedelta(days=30)
        needs_attention: list[IndexEntry] = []

        for entry in self._entries.values():
            # Old proposals
            if entry.status == ADRStatus.PROPOSED and entry.date < thirty_days_ago:
                needs_attention.append(entry)
                continue

            # Deprecated without supersession
            if entry.status == ADRStatus.DEPRECATED and not entry.superseded_by:
                needs_attention.append(entry)
                continue

        return needs_attention
