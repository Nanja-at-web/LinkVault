import unittest

from linkvault.server import index_html, linkvault_identity


class ServerHtmlTest(unittest.TestCase):
    def test_linkvault_identity_supports_extension_discovery(self):
        identity = linkvault_identity()

        self.assertEqual(identity["app"], "LinkVault")
        self.assertEqual(identity["health"], "/healthz")
        self.assertIn("version", identity)

    def test_index_html_documents_keyboard_shortcuts(self):
        html = index_html()

        self.assertIn("Ctrl/Cmd+K Suche", html)
        self.assertIn("document.addEventListener('keydown'", html)
        self.assertIn("isTypingTarget", html)
        self.assertIn("setActiveTab('bookmarks')", html)

    def test_index_html_has_bookmark_view_preferences(self):
        html = index_html()

        self.assertIn('id="bookmark-view"', html)
        self.assertIn('id="saved-view-select"', html)
        self.assertIn('id="saved-view-name"', html)
        self.assertIn("Compact List", html)
        self.assertIn("Detailed List", html)
        self.assertIn("Grid/Card", html)
        self.assertIn("data-display-field=\"description\"", html)
        self.assertIn("/api/settings/bookmark-view", html)
        self.assertIn("/api/settings/bookmark-views", html)
        self.assertIn("loadViewPreferences", html)
        self.assertIn("Als Standard speichern", html)
        self.assertIn("Benannte Ansicht speichern", html)
        self.assertIn("Inbox Review", html)
        self.assertIn("Research Grid", html)
        self.assertIn("Duplicate Cleanup", html)
        self.assertIn("Als Default anlegen", html)
        self.assertIn("renderStarterViews", html)
        self.assertIn("Inbox", html)
        self.assertIn("Recherche", html)
        self.assertIn("Dubletten", html)
        self.assertIn('id="active-view-chips"', html)
        self.assertIn("renderActiveViewChips", html)

    def test_index_html_has_conflict_center(self):
        html = index_html()

        self.assertIn("Conflict Center", html)
        self.assertIn('id="conflict-center"', html)
        self.assertIn('id="conflict-groups"', html)
        self.assertIn('id="conflict-state-filter"', html)
        self.assertIn("/api/conflicts", html)
        self.assertIn("/api/restore/sessions", html)
        self.assertIn("/api/restore/sessions/${encodeURIComponent(sessionId)}/conflict-groups/${encodeURIComponent(groupKey)}/decision", html)
        self.assertIn('id="restore-sessions"', html)
        self.assertIn("renderConflicts", html)
        self.assertIn("renderConflictGroups", html)
        self.assertIn("renderGroupImpactPreview", html)
        self.assertIn("data-conflict-group-impact", html)
        self.assertIn("renderConflictDetails", html)
        self.assertIn("renderRestoreSessions", html)

    def test_index_html_has_favorites_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="favorites"', html)
        self.assertIn('id="favorites"', html)
        self.assertIn('id="favorites-list"', html)
        self.assertIn('id="refresh-favorites"', html)
        self.assertIn('id="show-favorites-in-bookmarks"', html)
        self.assertIn("refreshFavorites", html)
        self.assertIn("/api/bookmarks", html)

    def test_index_html_has_tags_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="tags"', html)
        self.assertIn('id="tags"', html)
        self.assertIn('id="tags-list"', html)
        self.assertIn('id="refresh-tags"', html)
        self.assertIn("refreshTags", html)
        self.assertIn("/api/tags", html)

    def test_index_html_has_collections_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="collections"', html)
        self.assertIn('id="collections"', html)
        self.assertIn('id="collections-list"', html)
        self.assertIn('id="refresh-collections"', html)
        self.assertIn("refreshCollections", html)
        self.assertIn("/api/collections", html)

    def test_index_html_has_settings_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="settings"', html)
        self.assertIn('id="settings"', html)
        self.assertIn("Einstellungen", html)

    def test_index_html_has_conflict_center_session_controls(self):
        html = index_html()

        self.assertIn("apply-session-defaults", html)
        self.assertIn("apply-defaults", html)
        self.assertIn("Offene Konflikte mit Standard", html)
        self.assertIn("apply-session-group", html)
        self.assertIn("session-group-select", html)
        self.assertIn("Konflikte erledigt", html)

    def test_index_html_has_quick_add(self):
        html = index_html()

        self.assertIn('id="quick-add-dialog"', html)
        self.assertIn('id="quick-add-btn"', html)
        self.assertIn('id="qa-form"', html)
        self.assertIn('id="qa-preflight"', html)
        self.assertIn('id="qa-cancel"', html)
        self.assertIn('id="qa-submit"', html)
        self.assertIn("openQuickAdd", html)
        self.assertIn("saveAndCloseQuickAdd", html)
        self.assertIn("renderQaPreflight", html)
        self.assertIn("Schnell-Speichern", html)
        self.assertIn("quick-add-nav-btn", html)


if __name__ == "__main__":
    unittest.main()
