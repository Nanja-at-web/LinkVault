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

    def test_index_html_tags_panel_has_management_ui(self):
        html = index_html()

        self.assertIn('id="tag-create-form"', html)
        self.assertIn('id="tag-create-input"', html)
        self.assertIn("tag-rename-btn", html)
        self.assertIn("tag-delete-btn", html)
        self.assertIn("openRenameDialog", html)
        self.assertIn("/api/tags/rename", html)
        self.assertIn("/api/tags/delete", html)

    def test_index_html_collections_panel_has_management_ui(self):
        html = index_html()

        self.assertIn('id="collection-create-form"', html)
        self.assertIn('id="collection-create-input"', html)
        self.assertIn("coll-rename-btn", html)
        self.assertIn("coll-delete-btn", html)
        self.assertIn("/api/collections/rename", html)
        self.assertIn("/api/collections/delete", html)

    def test_index_html_has_rename_label_dialog(self):
        html = index_html()

        self.assertIn('id="rename-label-dialog"', html)
        self.assertIn('id="rename-label-form"', html)
        self.assertIn('id="rename-label-input"', html)

    def test_index_html_has_settings_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="settings"', html)
        self.assertIn('id="settings"', html)
        self.assertIn("Einstellungen", html)

    def test_index_html_has_sync_drift_ui(self):
        html = index_html()

        self.assertIn('id="sync-snapshot-status"', html)
        self.assertIn('id="sync-drift-result"', html)
        self.assertIn("renderSyncSnapshotStatus", html)
        self.assertIn("renderSyncDrift", html)
        self.assertIn("/api/sync/snapshot", html)
        self.assertIn("/api/sync/drift", html)
        self.assertIn("Browser-Sync-Status", html)

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

    def test_index_html_quick_add_has_ux_improvements(self):
        html = index_html()

        # Inbox hint visible in dialog
        self.assertIn('id="qa-inbox-hint"', html)
        self.assertIn("Inbox", html)
        # Favorite star outside details
        self.assertIn('id="qa-fav-star"', html)
        self.assertIn("qa-fav-star", html)
        self.assertIn('id="qa-fav-hidden"', html)
        # Post-save feedback
        self.assertIn('id="qa-save-feedback"', html)
        self.assertIn("Bookmark gespeichert", html)
        # Vollformular as secondary button
        self.assertIn('id="qa-fullform"', html)
        self.assertIn("secondary-sm", html)
        # Preflight match type label
        self.assertIn("matchTypeLabel", html)
        self.assertIn("qa-preflight-match-type", html)
        self.assertIn("qa-preflight-actions", html)
        self.assertIn("Tags/Notizen aktualisieren", html)
        self.assertIn("Trotzdem neu speichern", html)

    def test_index_html_has_archive_tab(self):
        html = index_html()

        self.assertIn('data-tab-trigger="archive"', html)
        self.assertIn('data-tab-panel="archive"', html)
        self.assertIn('id="archive"', html)
        self.assertIn("Archiv", html)
        self.assertIn("Phase 3", html)

    def test_index_html_has_sort_controls(self):
        html = index_html()

        self.assertIn('id="sort-by"', html)
        self.assertIn('id="sort-order"', html)
        self.assertIn("sort_by", html)
        self.assertIn("sort_order", html)
        self.assertIn("Hinzugefuegt", html)
        self.assertIn("Zuletzt geaendert", html)
        self.assertIn("Absteigend", html)
        self.assertIn("Aufsteigend", html)

    def test_index_html_has_favorites_care_section(self):
        html = index_html()

        self.assertIn("favorites-care-drawer", html)
        self.assertIn("refresh-favorites-report", html)
        self.assertIn("check-favorite-links", html)
        self.assertIn("link-check-status", html)
        self.assertIn("favorites-report-uncategorized", html)
        self.assertIn("favorites-report-duplicated", html)
        self.assertIn("favorites-report-dead", html)
        self.assertIn("uncategorized-list", html)
        self.assertIn("duplicated-list", html)
        self.assertIn("dead-list", html)
        self.assertIn("renderFavoritesReport", html)
        self.assertIn("refreshFavoritesReport", html)
        self.assertIn("/api/favorites/report", html)
        self.assertIn("/api/favorites/check", html)

    def test_index_html_has_collection_scores(self):
        html = index_html()

        self.assertIn("refresh-collection-scores", html)
        self.assertIn("care-score", html)
        self.assertIn("collectionScores", html)
        self.assertIn("/api/collections/scores", html)
        self.assertIn("refreshCollectionScores", html)

    def test_index_html_has_dedup_panel(self):
        html = index_html()

        self.assertIn('data-tab-trigger="dedup"', html)
        self.assertIn('data-tab-panel="dedup"', html)
        self.assertIn('id="dedup-output"', html)
        self.assertIn('id="dry-run"', html)
        self.assertIn("refreshDryRun", html)
        self.assertIn("/api/dedup/dry-run", html)

    def test_index_html_dedup_panel_has_management_ux(self):
        html = index_html()

        # Bulk bar slot
        self.assertIn('id="dedup-bulk-bar"', html)
        # Inline merge history
        self.assertIn('id="dedup-merge-history-section"', html)
        self.assertIn('id="dedup-merge-history-list"', html)
        # Auto-load wiring
        self.assertIn("refreshDedupPanel", html)
        # Merge history fetch
        self.assertIn("refreshDedupMergeHistory", html)
        self.assertIn("/api/dedup/merges", html)
        # Winner reason rendering
        self.assertIn("winner_reason", html)
        # Feedback elements
        self.assertIn("dedup-merge-result", html)
        self.assertIn("dedup-merge-error", html)
        # Bulk merge all safe
        self.assertIn("dedup-merge-all-safe", html)
        # Silent merge helper
        self.assertIn("mergeDuplicatesSilent", html)

    def test_index_html_has_api_token_test(self):
        html = index_html()

        self.assertIn('id="token-test-input"', html)
        self.assertIn('id="token-test-btn"', html)
        self.assertIn('id="token-test-result"', html)
        self.assertIn("testApiToken", html)
        self.assertIn("Token testen", html)
        self.assertIn("Sofort testen", html)
        self.assertIn("data-focus-token-test", html)

    def test_index_html_profile_has_companion_setup_guidance(self):
        html = index_html()

        # Companion Extension setup guidance in profile/token section
        self.assertIn("Companion Extension", html)
        self.assertIn("Extension einrichten", html)
        # Setup steps reference token creation and options page
        self.assertIn("Token unten erstellen", html)
        self.assertIn("Token-Klartext kopieren", html)


    def test_index_html_has_shortcut_help(self):
        html = index_html()

        self.assertIn('id="shortcut-help-dialog"', html)
        self.assertIn('id="shortcut-help-close"', html)
        self.assertIn('id="shortcut-help-btn"', html)
        self.assertIn("openShortcutHelp", html)
        self.assertIn("closeShortcutHelp", html)
        self.assertIn("Tastaturkuerzel", html)
        self.assertIn("Ctrl/Cmd+K", html)
        self.assertIn("Ctrl</kbd>/<kbd>Cmd", html)
        self.assertIn("Schnell-Speichern", html)
        self.assertIn("shortcut-table", html)
        self.assertIn("kbd-cell", html)

    def test_index_html_has_phase6_import_formats(self):
        html = index_html()

        self.assertIn("firefox-jsonlz4", html)
        self.assertIn("Firefox-JSONLZ4", html)
        self.assertIn("generic-csv", html)
        self.assertIn("generic-json", html)
        self.assertIn("Generisch CSV", html)
        self.assertIn("Generisch JSON", html)
        self.assertIn("generic-mapping-ui", html)
        self.assertIn("generic-mapping-fields", html)
        self.assertIn("detectGenericColumns", html)
        self.assertIn("/api/import/firefox-jsonlz4", html)
        self.assertIn("/api/import/generic", html)
        self.assertIn("/api/import/generic/columns", html)
        self.assertIn("BINARY_IMPORT_FORMATS", html)
        self.assertIn("GENERIC_IMPORT_FORMATS", html)

    def test_index_html_import_panel_has_ux_improvements(self):
        html = index_html()

        # Step-based layout
        self.assertIn("import-step-num", html)
        self.assertIn("import-step-header", html)
        # Format hint
        self.assertIn('id="import-format-hint"', html)
        self.assertIn("FORMAT_HINTS", html)
        self.assertIn("updateImportFormatUi", html)
        # Binary format notice
        self.assertIn('id="import-binary-notice"', html)
        self.assertIn("import-binary-notice", html)
        # Separate submit button (not form submit)
        self.assertIn('id="import-submit-btn"', html)
        # Preview result and import result are separate
        self.assertIn('id="import-preview-output"', html)
        self.assertIn('id="import-result-output"', html)
        # Result UX: go to inbox
        self.assertIn("import-goto-inbox", html)
        self.assertIn("Inbox anzeigen", html)
        # Inline import history
        self.assertIn("import-history-section", html)
        self.assertIn("import-history-list", html)
        self.assertIn("refreshImportHistory", html)

    def test_index_html_has_export_section(self):
        html = index_html()

        # Export download link
        self.assertIn("/api/export/bookmarks.html", html)
        self.assertIn("export-bookmarks-link", html)
        self.assertIn("linkvault-bookmarks.html", html)
        # Export card UI
        self.assertIn("export-card", html)
        self.assertIn("Browser-HTML herunterladen", html)
        self.assertIn("Bookmarks exportieren", html)


    def test_index_html_has_system_tab(self):
        html = index_html()

        # Nav label and panel heading renamed from "Betrieb" to "System"
        self.assertIn('data-tab-trigger="operations">System', html)
        self.assertIn("<h2>System</h2>", html)
        # Subtitle updated
        self.assertIn("Health-Status", html)
        self.assertIn("Aktivitaetsverlauf", html)
        # Activity section moved up and has description
        self.assertIn('id="activity-log"', html)
        # Merge-Verlauf section
        self.assertIn("Merge-Verlauf", html)
        self.assertIn('id="merge-history"', html)
        # Backup & Restore card
        self.assertIn("ops-backup-info", html)
        self.assertIn("backup-linkvault.sh", html)
        self.assertIn("restore-linkvault.sh", html)
        self.assertIn("ops-code", html)
        # Settings tab points to System tab
        self.assertIn("System &amp; Backup", html)

    def test_index_html_settings_tab_has_useful_navigation(self):
        html = index_html()

        self.assertIn('id="settings"', html)
        self.assertIn("Ansichtsoptionen", html)
        self.assertIn("Konto &amp; API-Token", html)
        self.assertIn("System &amp; Backup", html)
        # All three cards link to other tabs
        self.assertIn('data-tab-trigger="bookmarks"', html)
        self.assertIn('data-tab-trigger="profile"', html)
        self.assertIn('data-tab-trigger="operations"', html)


if __name__ == "__main__":
    unittest.main()
