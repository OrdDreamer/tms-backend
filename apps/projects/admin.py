from django.contrib import admin, messages

from apps.projects.models import Project, ProjectLanguage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Project model.

    Defines list display, search fields, filters.
    """
    list_display = (
        "slug",
        "name",
        "display_base_language",
        "display_all_languages"
    )
    search_fields = ("slug", "name")
    list_filter = ("languages__language",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("languages")

    def display_base_language(self, obj):
        base_language = obj.get_base_language()
        return (
            (f"{base_language.get_language_display()} "
             f"({base_language.language})")
            if base_language else
            "-"
        )

    display_base_language.short_description = "Base Language"

    def display_all_languages(self, obj):
        language_codes = [lang.language for lang in obj.languages.all()]
        return ", ".join(language_codes) if language_codes else "-"

    display_all_languages.short_description = "All Languages"


@admin.register(ProjectLanguage)
class ProjectLanguageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ProjectLanguage model.

    Allows managing project languages independently with filtering and search.
    """
    list_display = ("project", "display_language", "is_base_language")
    search_fields = ["project__slug", "project__name", "language"]

    list_filter = (
        "is_base_language",
        "project",
        "language"
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("project")

    def display_language(self, obj):
        return f"{obj.get_language_display()} ({obj.language})"

    display_language.short_description = "Language"

    actions = ["set_base_language"]

    @admin.action(description="Set selected language as base language")
    def set_base_language(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one language to set as base.",
                messages.ERROR,
            )
            return

        project_language = queryset.first()
        project_language.set_base_language()
        self.message_user(
            request,
            f"{project_language.get_language_display()} "
            f"({project_language.language}) "
            f"is now the base language for {project_language.project}.",
            messages.SUCCESS,
        )
