"""
Tests for vault search and filter functionality.
"""

import pytest
from stegvault.vault import (
    create_vault,
    add_entry,
    search_entries,
    filter_by_tags,
    filter_by_url,
)


class TestSearchEntries:
    """Test vault search functionality."""

    def test_search_by_key(self):
        """Test searching by key."""
        vault = create_vault()
        add_entry(vault, "gmail_personal", "pass1", username="user@gmail.com")
        add_entry(vault, "github_work", "pass2", username="workuser")
        add_entry(vault, "twitter", "pass3", username="tweeter")

        results = search_entries(vault, "gmail")
        assert len(results) == 1
        assert results[0].key == "gmail_personal"

    def test_search_by_username(self):
        """Test searching by username."""
        vault = create_vault()
        add_entry(vault, "service1", "pass1", username="john@example.com")
        add_entry(vault, "service2", "pass2", username="jane@example.com")
        add_entry(vault, "service3", "pass3", username="bob@test.com")

        results = search_entries(vault, "example.com")
        assert len(results) == 2
        keys = {r.key for r in results}
        assert keys == {"service1", "service2"}

    def test_search_by_url(self):
        """Test searching by URL."""
        vault = create_vault()
        add_entry(vault, "site1", "pass1", url="https://github.com")
        add_entry(vault, "site2", "pass2", url="https://gitlab.com")
        add_entry(vault, "site3", "pass3", url="https://github.com/org")

        results = search_entries(vault, "github")
        assert len(results) == 2

    def test_search_by_notes(self):
        """Test searching by notes."""
        vault = create_vault()
        add_entry(vault, "acc1", "pass1", notes="Work account for project X")
        add_entry(vault, "acc2", "pass2", notes="Personal account")
        add_entry(vault, "acc3", "pass3", notes="Work account for project Y")

        results = search_entries(vault, "project")
        assert len(results) == 2

    def test_search_case_insensitive(self):
        """Test case-insensitive search (default)."""
        vault = create_vault()
        add_entry(vault, "GitHub", "pass1", username="USER@GITHUB.COM")

        results = search_entries(vault, "github", case_sensitive=False)
        assert len(results) == 1

        results = search_entries(vault, "GITHUB", case_sensitive=False)
        assert len(results) == 1

    def test_search_case_sensitive(self):
        """Test case-sensitive search."""
        vault = create_vault()
        add_entry(vault, "GitHub", "pass1", username="user@example.com")
        add_entry(vault, "github", "pass2", username="user2@example.com")

        results = search_entries(vault, "GitHub", case_sensitive=True)
        assert len(results) == 1
        assert results[0].key == "GitHub"

    def test_search_specific_fields(self):
        """Test searching in specific fields only."""
        vault = create_vault()
        add_entry(vault, "test_key", "pass1", username="other", notes="test note")

        # Search only in key field
        results = search_entries(vault, "test", fields=["key"])
        assert len(results) == 1

        # Search only in username field (shouldn't match "test_key")
        results = search_entries(vault, "test", fields=["username"])
        assert len(results) == 0

    def test_search_no_results(self):
        """Test search with no matching entries."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1")

        results = search_entries(vault, "nonexistent")
        assert len(results) == 0

    def test_search_empty_query(self):
        """Test search with empty query."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1")

        results = search_entries(vault, "")
        assert len(results) == 0

    def test_search_multiple_matches(self):
        """Test entry appearing only once even if multiple fields match."""
        vault = create_vault()
        add_entry(vault, "test_service", "pass1", username="test_user", notes="test notes")

        # Should find the entry only once even though "test" appears in multiple fields
        results = search_entries(vault, "test")
        assert len(results) == 1


class TestFilterByTags:
    """Test vault tag filtering functionality."""

    def test_filter_single_tag(self):
        """Test filtering by single tag."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=["work"])
        add_entry(vault, "key2", "pass2", tags=["personal"])
        add_entry(vault, "key3", "pass3", tags=["work", "email"])

        results = filter_by_tags(vault, ["work"])
        assert len(results) == 2
        keys = {r.key for r in results}
        assert keys == {"key1", "key3"}

    def test_filter_multiple_tags_any(self):
        """Test filtering by multiple tags with ANY match."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=["work", "email"])
        add_entry(vault, "key2", "pass2", tags=["personal", "social"])
        add_entry(vault, "key3", "pass3", tags=["work"])

        results = filter_by_tags(vault, ["work", "social"], match_all=False)
        assert len(results) == 3  # All have at least one of the tags

    def test_filter_multiple_tags_all(self):
        """Test filtering by multiple tags with ALL match."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=["work", "email"])
        add_entry(vault, "key2", "pass2", tags=["work", "email", "important"])
        add_entry(vault, "key3", "pass3", tags=["work"])

        results = filter_by_tags(vault, ["work", "email"], match_all=True)
        assert len(results) == 2
        keys = {r.key for r in results}
        assert keys == {"key1", "key2"}

    def test_filter_no_tags(self):
        """Test filtering with empty tag list."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=["work"])

        results = filter_by_tags(vault, [])
        assert len(results) == 0

    def test_filter_nonexistent_tag(self):
        """Test filtering by tag that doesn't exist."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=["work"])

        results = filter_by_tags(vault, ["nonexistent"])
        assert len(results) == 0

    def test_filter_entry_without_tags(self):
        """Test filtering when entry has no tags."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", tags=[])
        add_entry(vault, "key2", "pass2", tags=["work"])

        results = filter_by_tags(vault, ["work"])
        assert len(results) == 1
        assert results[0].key == "key2"


class TestFilterByURL:
    """Test vault URL filtering functionality."""

    def test_filter_url_substring(self):
        """Test filtering by URL substring (default)."""
        vault = create_vault()
        add_entry(vault, "site1", "pass1", url="https://github.com")
        add_entry(vault, "site2", "pass2", url="https://gitlab.com")
        add_entry(vault, "site3", "pass3", url="https://github.com/org")

        results = filter_by_url(vault, "github")
        assert len(results) == 2

    def test_filter_url_exact_match(self):
        """Test filtering by exact URL match."""
        vault = create_vault()
        add_entry(vault, "site1", "pass1", url="https://github.com")
        add_entry(vault, "site2", "pass2", url="https://github.com/org")

        results = filter_by_url(vault, "https://github.com", exact=True)
        assert len(results) == 1
        assert results[0].key == "site1"

    def test_filter_url_case_insensitive(self):
        """Test URL filtering is case-insensitive."""
        vault = create_vault()
        add_entry(vault, "site1", "pass1", url="https://GitHub.com")

        results = filter_by_url(vault, "github")
        assert len(results) == 1

    def test_filter_empty_url_pattern(self):
        """Test filtering with empty URL pattern."""
        vault = create_vault()
        add_entry(vault, "site1", "pass1", url="https://github.com")

        results = filter_by_url(vault, "")
        assert len(results) == 0

    def test_filter_entry_without_url(self):
        """Test filtering when entry has no URL."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", url=None)
        add_entry(vault, "key2", "pass2", url="https://github.com")

        results = filter_by_url(vault, "github")
        assert len(results) == 1
        assert results[0].key == "key2"

    def test_filter_no_matching_urls(self):
        """Test filtering with no matching URLs."""
        vault = create_vault()
        add_entry(vault, "key1", "pass1", url="https://example.com")

        results = filter_by_url(vault, "github")
        assert len(results) == 0


class TestCombinedFilters:
    """Test combining multiple search/filter operations."""

    def test_search_then_filter_tags(self):
        """Test searching and then filtering results by tags."""
        vault = create_vault()
        add_entry(vault, "gmail_work", "pass1", tags=["work", "email"])
        add_entry(vault, "gmail_personal", "pass2", tags=["personal", "email"])
        add_entry(vault, "github_work", "pass3", tags=["work", "code"])

        # First search for "gmail"
        search_results = search_entries(vault, "gmail")
        assert len(search_results) == 2

        # Then filter by work tag manually (simulating combined workflow)
        work_entries = [e for e in search_results if "work" in e.tags]
        assert len(work_entries) == 1
        assert work_entries[0].key == "gmail_work"

    def test_filter_tags_and_url_intersection(self):
        """Test filtering by both tags and URL (intersection)."""
        vault = create_vault()
        add_entry(vault, "gh1", "pass1", url="https://github.com", tags=["work"])
        add_entry(vault, "gh2", "pass2", url="https://github.com", tags=["personal"])
        add_entry(vault, "gl1", "pass3", url="https://gitlab.com", tags=["work"])

        # Filter by tag
        tag_results = filter_by_tags(vault, ["work"])
        assert len(tag_results) == 2

        # Filter by URL
        url_results = filter_by_url(vault, "github")
        assert len(url_results) == 2

        # Intersection (entries with work tag AND github URL)
        # Use keys for intersection since VaultEntry is not hashable
        tag_keys = {e.key for e in tag_results}
        url_keys = {e.key for e in url_results}
        intersection_keys = tag_keys.intersection(url_keys)

        assert len(intersection_keys) == 1
        assert "gh1" in intersection_keys
