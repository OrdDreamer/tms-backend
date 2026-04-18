"""Generative seed data: namespace templates + pseudo-translation.

Keys are defined as compact namespace -> suffix-list mappings.
Each suffix is either a plain string (EN value auto-derived via title-case)
or a (suffix, en_value) tuple for custom English text.

The translate() function generates deterministic pseudo-translations
in the format ``[UK] Save``.  ~20 % of (value, lang) pairs return None
to simulate untranslated keys for testing.
"""

from __future__ import annotations


def _humanize(suffix: str) -> str:
    return suffix.replace("_", " ").title()


def generate_keys(
    namespaces: dict[str, list],
) -> list[tuple[str, str, str]]:
    """Expand namespace templates into (dotted_key, description, en_value)."""
    result: list[tuple[str, str, str]] = []
    for ns, suffixes in namespaces.items():
        for entry in suffixes:
            if isinstance(entry, tuple):
                suffix, en_value = entry
            else:
                suffix = entry
                en_value = _humanize(suffix)
            result.append((f"{ns}.{suffix}", "", en_value))
    return result


def translate(en_value: str, lang: str) -> str | None:
    """Deterministic pseudo-translation; ~20 % keys stay untranslated."""
    if hash(f"{en_value}\x00{lang}") % 5 == 0:
        return None
    return f"[{lang.upper()}] {en_value}"


# ═════════════════════════════════════════════════════════════════════════════
# Web Application  (321 keys, 3-4 levels)
# Entry = "suffix" (EN from title-case) | ("suffix", "Custom EN value")
# ═════════════════════════════════════════════════════════════════════════════

WEB_APP_NAMESPACES = {
    "common.buttons": [
        "save",
        "cancel",
        "delete",
        "edit",
        "create",
        "submit",
        "back",
        "next",
        "previous",
        "close",
        "confirm",
        "search",
        "filter",
        "sort",
        "export",
        ("import_btn", "Import"),
        "refresh",
        "apply",
    ],
    "common.labels": [
        "name",
        "email",
        "status",
        "type",
        "description",
        "date",
        "time",
        "language",
        "project",
        "key",
        "value",
        "actions",
        "details",
    ],
    "common.messages": [
        ("success", "Operation completed successfully"),
        ("error", "An error occurred"),
        "warning",
        ("loading", "Loading..."),
        ("saving", "Saving..."),
        ("no_results", "No results found"),
        ("confirm_delete", "Are you sure you want to delete this item?"),
        ("unsaved_changes", "You have unsaved changes"),
        ("copied", "Copied to clipboard"),
        ("try_again", "Please try again"),
    ],
    "common.validation": [
        ("required", "This field is required"),
        ("min_length", "Must be at least {min} characters"),
        ("max_length", "Must be at most {max} characters"),
        ("invalid_email", "Please enter a valid email address"),
        ("invalid_format", "Invalid format"),
        ("already_exists", "This value already exists"),
        ("too_short", "Value is too short"),
        ("too_long", "Value is too long"),
        ("passwords_mismatch", "Passwords do not match"),
        ("field_invalid", "This field is invalid"),
    ],
    "auth.login.form": [
        ("title", "Sign In"),
        ("subtitle", "Enter your credentials to continue"),
        ("email_label", "Email address"),
        ("email_placeholder", "you@example.com"),
        ("password_label", "Password"),
        ("password_placeholder", "Enter your password"),
        ("submit_button", "Sign In"),
        ("forgot_password", "Forgot password?"),
        ("remember_me", "Remember me"),
        ("no_account", "Don't have an account?"),
    ],
    "auth.register.form": [
        ("title", "Create Account"),
        ("subtitle", "Fill in the details to get started"),
        ("first_name", "First name"),
        ("last_name", "Last name"),
        ("email", "Email address"),
        ("password", "Password"),
        ("confirm_password", "Confirm password"),
        ("submit_button", "Create Account"),
    ],
    "auth.register.validation": [
        ("email_taken", "This email is already registered"),
        ("weak_password", "Password is too weak"),
        ("passwords_mismatch", "Passwords do not match"),
        ("terms_required", "You must accept the terms"),
        ("invalid_email", "Please enter a valid email"),
    ],
    "auth.password.reset": [
        ("title", "Reset Password"),
        ("description", "Enter your email to receive a reset link"),
        ("email_label", "Email address"),
        ("submit_button", "Send Reset Link"),
        ("success_message", "Reset link sent to your email"),
        ("back_to_login", "Back to login"),
        ("expired_link", "This reset link has expired"),
        ("invalid_token", "Invalid or expired token"),
    ],
    "auth.password.change": [
        ("title", "Change Password"),
        ("current_label", "Current password"),
        ("new_label", "New password"),
        ("confirm_label", "Confirm new password"),
        ("submit_button", "Update Password"),
        ("success_message", "Password updated successfully"),
    ],
    "nav.sidebar.menu": [
        "dashboard",
        "projects",
        "translations",
        "settings",
        "users",
        "integrations",
        "reports",
        "activity",
        "help",
        ("logout", "Log Out"),
    ],
    "nav.header.actions": [
        ("search_placeholder", "Search..."),
        "notifications",
        "profile",
        ("language_switch", "Language"),
        ("quick_add", "Quick Add"),
    ],
    "dashboard.stats.cards": [
        ("total_projects", "Total Projects"),
        ("total_keys", "Total Keys"),
        ("total_translations", "Total Translations"),
        ("completion_rate", "Completion Rate"),
        ("recent_changes", "Recent Changes"),
        ("untranslated", "Untranslated"),
        ("languages", "Languages"),
        ("active_users", "Active Users"),
    ],
    "dashboard.widgets.activity": [
        ("title", "Recent Activity"),
        ("no_activity", "No recent activity"),
        ("view_all", "View All"),
        "created",
        "updated",
        "deleted",
        "imported",
    ],
    "dashboard.widgets.progress": [
        ("title", "Translation Progress"),
        ("completed", "Completed"),
        ("in_progress", "In Progress"),
        ("not_started", "Not Started"),
        ("overall", "Overall Progress"),
    ],
    "errors.http.not_found": [
        ("title", "Page Not Found"),
        ("description", "The page you are looking for does not exist"),
        ("back_home", "Go to Homepage"),
        ("search_suggestion", "Try searching for what you need"),
    ],
    "errors.http.forbidden": [
        ("title", "Access Denied"),
        ("description", "You do not have permission to access this page"),
        ("contact_admin", "Contact administrator"),
        ("back_home", "Go to Homepage"),
    ],
    "errors.http.server_error": [
        ("title", "Server Error"),
        ("description", "Something went wrong on our end"),
        ("try_again", "Try Again"),
        ("report_issue", "Report Issue"),
    ],
    "errors.http.unauthorized": [
        ("title", "Unauthorized"),
        ("description", "Please log in to access this page"),
        ("login_link", "Go to Login"),
    ],
    "errors.validation.messages": [
        ("required_field", "This field is required"),
        ("invalid_value", "Invalid value provided"),
        ("duplicate_entry", "This entry already exists"),
        ("format_error", "Invalid format"),
        ("length_exceeded", "Maximum length exceeded"),
    ],
    "errors.network.status": [
        ("connection_lost", "Connection lost"),
        ("timeout", "Request timed out"),
        "retry",
        ("offline_mode", "You are offline"),
    ],
    "settings.profile.general": [
        ("title", "General Settings"),
        ("first_name", "First name"),
        ("last_name", "Last name"),
        "email",
        "language",
        "timezone",
        ("save_button", "Save Changes"),
        ("cancel_button", "Cancel"),
    ],
    "settings.profile.avatar": [
        ("title", "Profile Picture"),
        ("upload", "Upload Photo"),
        ("remove", "Remove Photo"),
        ("max_size_hint", "Maximum file size: 5MB"),
        ("allowed_formats", "Allowed formats: JPG, PNG"),
        "preview",
    ],
    "settings.security.password": [
        ("title", "Change Password"),
        ("current", "Current password"),
        ("new_field", "New password"),
        ("confirm", "Confirm new password"),
        (
            "requirements_hint",
            "At least 8 characters with one uppercase letter",
        ),
        ("submit", "Update Password"),
    ],
    "settings.notifications.email": [
        ("title", "Email Notifications"),
        ("enabled", "Enable email notifications"),
        ("daily_digest", "Daily digest"),
        ("weekly_report", "Weekly report"),
        ("on_mention", "When someone mentions me"),
        ("on_key_update", "When a key is updated"),
        ("on_import", "When an import completes"),
    ],
    "settings.notifications.push": [
        ("title", "Push Notifications"),
        ("enabled", "Enable push notifications"),
        ("new_translation", "New translation added"),
        ("new_comment", "New comment"),
        ("task_assigned", "Task assigned to me"),
        ("deadline", "Deadline reminder"),
    ],
    "settings.api.tokens": [
        ("title", "API Tokens"),
        ("description", "Manage your API access tokens"),
        ("create", "Create Token"),
        "revoke",
        ("copy_button", "Copy"),
        ("expiry", "Expires"),
        ("name_label", "Token name"),
        ("last_used", "Last used"),
    ],
    "settings.api.webhooks": [
        ("title", "Webhooks"),
        ("description", "Configure webhook endpoints"),
        ("create", "Add Webhook"),
        ("url_label", "URL"),
        ("events_label", "Events"),
        ("test_button", "Test"),
    ],
    "projects.list.header": [
        ("title", "Projects"),
        ("create_button", "New Project"),
        ("search_placeholder", "Search projects..."),
        ("sort_by", "Sort by"),
        ("no_projects", "No projects found"),
        ("total_count", "Total"),
    ],
    "projects.detail.header": [
        ("edit_button", "Edit"),
        ("delete_button", "Delete"),
        ("settings_link", "Settings"),
        ("languages_count", "Languages"),
        ("export_button", "Export"),
        ("import_button", "Import"),
    ],
    "projects.detail.tabs": [
        "translations",
        "activity",
        "settings",
        "statistics",
        "languages",
    ],
    "projects.detail.languages": [
        ("title", "Languages"),
        ("add_button", "Add Language"),
        ("remove_button", "Remove"),
        ("set_base", "Set as Base"),
        ("confirm_remove", "Remove this language?"),
        ("base_label", "Base"),
    ],
    "projects.detail.stats": [
        ("total_keys", "Total Keys"),
        ("translated", "Translated"),
        ("untranslated", "Untranslated"),
        ("completion_percent", "Completion"),
        ("last_updated", "Last Updated"),
    ],
    "translations.list.toolbar": [
        ("title", "Translations"),
        ("search_placeholder", "Search keys..."),
        ("filter_language", "Language"),
        ("filter_status", "Status"),
        ("sort_by", "Sort by"),
        ("bulk_actions", "Bulk Actions"),
        ("select_all", "Select All"),
        ("deselect_all", "Deselect All"),
    ],
    "translations.detail.form": [
        ("key_label", "Key"),
        ("description_label", "Description"),
        ("created_label", "Created"),
        ("updated_label", "Updated"),
        ("values_title", "Translations"),
        ("add_value", "Add Translation"),
        ("delete_button", "Delete Key"),
        ("confirm_delete", "Are you sure you want to delete this key?"),
    ],
    "translations.status.labels": [
        "translated",
        "untranslated",
        ("needs_review", "Needs Review"),
        "approved",
        "rejected",
        "outdated",
    ],
    "translations.bulk.actions": [
        ("import_btn", "Import"),
        ("export_btn", "Export"),
        ("delete_btn", "Delete Selected"),
        ("copy_btn", "Copy Keys"),
        ("select_all", "Select All"),
        ("confirm", "Are you sure?"),
    ],
    "translations.filters.panel": [
        ("all_keys", "All Keys"),
        ("translated_only", "Translated"),
        ("untranslated_only", "Untranslated"),
        ("needs_review", "Needs Review"),
        ("by_language", "By Language"),
        ("by_namespace", "By Namespace"),
        ("clear_filters", "Clear Filters"),
    ],
    "forms.project.create": [
        ("title", "Create Project"),
        ("name_label", "Project name"),
        ("name_placeholder", "My Project"),
        ("slug_label", "Slug"),
        ("slug_placeholder", "my-project"),
        ("description_label", "Description"),
        ("base_language_label", "Base language"),
        ("submit_button", "Create"),
    ],
    "forms.project.settings": [
        ("title", "Project Settings"),
        ("name_label", "Project name"),
        ("description_label", "Description"),
        ("danger_zone", "Danger Zone"),
        ("delete_project", "Delete Project"),
        ("save_button", "Save Changes"),
    ],
    "forms.translation.create": [
        ("title", "Add Translation Key"),
        ("key_label", "Key"),
        ("key_placeholder", "section.subsection.key_name"),
        ("description_label", "Description"),
        ("language_select", "Language"),
        ("submit_button", "Create"),
    ],
    "forms.import.upload": [
        ("title", "Import Translations"),
        ("description", "Upload a file to import translations"),
        ("file_label", "Choose file"),
        ("format_select", "File format"),
        ("language_select", "Target language"),
        ("overwrite_checkbox", "Overwrite existing translations"),
        ("submit_button", "Import"),
    ],
    "forms.export.options": [
        ("title", "Export Translations"),
        ("format_select", "File format"),
        ("languages_select", "Languages"),
        ("include_empty", "Include untranslated keys"),
        ("filename_label", "File name"),
        ("submit_button", "Export"),
    ],
    "table.pagination.controls": [
        "showing",
        ("of_total", "of"),
        ("per_page", "per page"),
        ("first_page", "First"),
        ("last_page", "Last"),
        ("next_page", "Next"),
        ("previous_page", "Previous"),
    ],
    "table.headers.columns": [
        "key",
        "value",
        "language",
        "status",
        ("updated_at", "Updated"),
        "actions",
    ],
    "modal.confirm.dialog": [
        ("title", "Confirm Action"),
        ("message", "This action cannot be undone"),
        ("confirm_button", "Confirm"),
        ("cancel_button", "Cancel"),
        ("warning_text", "Please review before proceeding"),
    ],
    "activity.log.entries": [
        ("title", "Activity Log"),
        ("no_activity", "No activity recorded"),
        ("load_more", "Load More"),
        ("filter_by_user", "Filter by user"),
        ("filter_by_type", "Filter by type"),
    ],
    "activity.types.events": [
        ("key_created", "Key created"),
        ("key_deleted", "Key deleted"),
        ("key_updated", "Key updated"),
        ("value_created", "Translation added"),
        ("value_updated", "Translation updated"),
        ("language_added", "Language added"),
        ("language_removed", "Language removed"),
        ("import_completed", "Import completed"),
    ],
}

# ═════════════════════════════════════════════════════════════════════════════
# Mobile Application  (60 keys)
# ═════════════════════════════════════════════════════════════════════════════

MOBILE_APP_NAMESPACES = {
    "common.buttons": [
        "save",
        "cancel",
        "delete",
        "edit",
        "back",
        "next",
        "close",
        "confirm",
        "search",
        "share",
    ],
    "common.labels": [
        "name",
        "email",
        "phone",
        "status",
        "date",
        "language",
        "version",
        "size",
    ],
    "onboarding.welcome.screen": [
        ("title", "Welcome to TMS"),
        ("subtitle", "Manage translations on the go"),
        (
            "description",
            "Access your projects, review translations, "
            "and collaborate with your team anywhere",
        ),
        ("skip_button", "Skip"),
        ("next_button", "Next"),
        ("start_button", "Get Started"),
    ],
    "onboarding.setup.steps": [
        ("language_title", "Choose Your Language"),
        ("profile_title", "Set Up Your Profile"),
        ("notifications_title", "Stay Updated"),
        ("complete_title", "You're All Set!"),
        ("skip_link", "Skip"),
        ("continue_button", "Continue"),
    ],
    "onboarding.permissions.dialog": [
        ("camera_title", "Allow camera access for profile photo"),
        ("location_title", "Allow location for timezone detection"),
        ("notifications_title", "Allow notifications to stay updated"),
        ("allow_button", "Allow"),
        ("deny_button", "Deny"),
    ],
    "push.notifications.types": [
        ("new_message", "New message"),
        ("update_available", "Update available"),
        ("reminder", "Reminder"),
        ("achievement", "Achievement unlocked"),
        ("system_alert", "System alert"),
    ],
    "push.notifications.settings": [
        ("enable_all", "Enabled"),
        "sounds",
        "vibration",
        ("quiet_hours", "Quiet hours"),
    ],
    "profile.settings.general": [
        ("title", "Profile"),
        ("display_name", "Display name"),
        "bio",
        "email",
        "phone",
        ("save_button", "Save"),
    ],
    "profile.settings.privacy": [
        ("title", "Privacy"),
        ("profile_visibility", "Profile visibility"),
        ("activity_status", "Activity status"),
        ("read_receipts", "Read receipts"),
        ("save_button", "Save"),
    ],
    "screens.home.sections": [
        "recent",
        "favorites",
        "trending",
        "recommended",
        "all",
    ],
}

# ═════════════════════════════════════════════════════════════════════════════
# Marketing Website  (40 keys)
# ═════════════════════════════════════════════════════════════════════════════

MARKETING_SITE_NAMESPACES = {
    "hero.main.content": [
        ("title", "Translate Your Product With Confidence"),
        ("subtitle", "The modern translation management platform for teams"),
        (
            "description",
            "Streamline your localization workflow with powerful "
            "collaboration tools and seamless integrations",
        ),
        ("cta_button", "Start Free Trial"),
        ("secondary_link", "Learn More"),
    ],
    "hero.secondary.content": [
        ("title", "Trusted by 10,000+ Teams Worldwide"),
        (
            "description",
            "From startups to enterprises, teams "
            "rely on TMS for their translation needs",
        ),
        ("cta_button", "Get Started Free"),
        ("image_alt", "Translation management dashboard screenshot"),
    ],
    "features.list.items": [
        ("title", "Why Choose TMS?"),
        ("fast_title", "Lightning Fast"),
        (
            "fast_description",
            "Import and export translations in seconds, not minutes",
        ),
        ("secure_title", "Enterprise Security"),
        (
            "secure_description",
            "Your data is encrypted at rest and in transit",
        ),
        ("scalable_title", "Infinitely Scalable"),
    ],
    "features.detail.descriptions": [
        (
            "fast_text",
            "Our optimized pipeline processes thousands of keys per second",
        ),
        (
            "secure_text",
            "SOC 2 compliant with end-to-end encryption and audit logging",
        ),
        (
            "scalable_text",
            "Handle millions of translations across hundreds of projects",
        ),
        (
            "reliable_text",
            "99.99% uptime SLA with automatic failover and backups",
        ),
    ],
    "pricing.plans.labels": [
        ("title", "Simple, Transparent Pricing"),
        ("free_name", "Free"),
        ("free_price", "$0/month"),
        ("pro_name", "Pro"),
        ("pro_price", "$29/month"),
        ("enterprise_name", "Enterprise"),
    ],
    "pricing.plans.features": [
        ("unlimited_projects", "Unlimited projects"),
        ("api_access", "API access"),
        ("priority_support", "Priority support"),
        ("custom_domain", "Custom domain"),
        "analytics",
    ],
    "cta.primary.content": [
        ("title", "Ready to Get Started?"),
        ("description", "Join thousands of teams already using TMS"),
        ("button_text", "Start Free Trial"),
        ("subtext", "No credit card required"),
    ],
    "footer.links.company": ["about", "careers", "blog", "contact"],
    "footer.links.legal": [
        ("privacy", "Privacy Policy"),
        ("terms", "Terms of Service"),
    ],
}
