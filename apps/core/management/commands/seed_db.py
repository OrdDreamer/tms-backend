"""Seed the database with realistic development data.

Usage:
    python manage.py seed_db          # idempotent seed
    python manage.py seed_db --flush  # wipe seeded data and re-seed
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.management.commands._seed_data import (
    MARKETING_SITE_NAMESPACES,
    MOBILE_APP_NAMESPACES,
    WEB_APP_NAMESPACES,
    generate_keys,
    translate,
)
from apps.projects.models import Project, ProjectLanguage
from apps.translations.models import TranslationKey, TranslationValue
from apps.users.models import User

SUPERUSER_EMAIL = "admin@admin.com"
SUPERUSER_PASSWORD = "admin"

PROJECTS = [
    {
        "slug": "web-app",
        "name": "Web Application",
        "description": (
            "Main web application with admin panel, "
            "user-facing dashboard and translation management features"
        ),
        "languages": [
            ("en", True),
            ("uk", False),
            ("de", False),
            ("fr", False),
            ("es", False),
        ],
        "keys": generate_keys(WEB_APP_NAMESPACES),
    },
    {
        "slug": "mobile-app",
        "name": "Mobile Application",
        "description": "Cross-platform mobile app for iOS and Android",
        "languages": [
            ("en", True),
            ("uk", False),
            ("pl", False),
            ("ja", False),
        ],
        "keys": generate_keys(MOBILE_APP_NAMESPACES),
    },
    {
        "slug": "marketing-site",
        "name": "Marketing Website",
        "description": "Public-facing marketing and landing pages",
        "languages": [
            ("en", True),
            ("uk", False),
            ("de", False),
            ("fr", False),
            ("es", False),
            ("pl", False),
        ],
        "keys": generate_keys(MARKETING_SITE_NAMESPACES),
    },
]


class Command(BaseCommand):
    help = "Seed database with realistic development data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all seeded data before re-seeding",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        with transaction.atomic():
            self._create_superuser()
            for project_cfg in PROJECTS:
                self._seed_project(project_cfg)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))

    # ── internals ──────────────────────────────────────────────────────

    def _flush(self):
        slugs = [p["slug"] for p in PROJECTS]
        deleted_translations = TranslationValue.objects.filter(
            translation_key__project__slug__in=slugs,
        ).delete()[0]
        deleted_keys = TranslationKey.objects.filter(
            project__slug__in=slugs,
        ).delete()[0]
        deleted_langs = ProjectLanguage.objects.filter(
            project__slug__in=slugs,
        ).delete()[0]
        deleted_projects = Project.objects.filter(slug__in=slugs).delete()[0]
        deleted_users = User.objects.filter(email=SUPERUSER_EMAIL).delete()[0]
        self.stdout.write(
            f"Flushed: {deleted_projects} projects, {deleted_langs} languages, "
            f"{deleted_keys} keys, {deleted_translations} values, "
            f"{deleted_users} users"
        )

    def _create_superuser(self):
        if User.objects.filter(email=SUPERUSER_EMAIL).exists():
            self.stdout.write(f"Superuser {SUPERUSER_EMAIL} already exists — skipped")
            return
        User.objects.create_superuser(
            email=SUPERUSER_EMAIL,
            password=SUPERUSER_PASSWORD,
            first_name="Admin",
            last_name="User",
        )
        self.stdout.write(f"Created superuser {SUPERUSER_EMAIL}")

    def _seed_project(self, cfg: dict):
        project, created = Project.objects.get_or_create(
            slug=cfg["slug"],
            defaults={"name": cfg["name"], "description": cfg["description"]},
        )
        if not created:
            self.stdout.write(f"Project «{project.slug}» already exists — skipped")
            return

        base_lang_code, target_lang_codes = None, []
        for lang_code, is_base in cfg["languages"]:
            ProjectLanguage.objects.create(
                project=project, language=lang_code, is_base_language=is_base,
            )
            if is_base:
                base_lang_code = lang_code
            else:
                target_lang_codes.append(lang_code)

        keys_data = cfg["keys"]

        tk_objects = TranslationKey.objects.bulk_create([
            TranslationKey(
                key=key, project=project, description=desc,
            )
            for key, desc, _en_value in keys_data
        ])

        tv_objects = []
        for tk_obj, (key, _desc, en_value) in zip(tk_objects, keys_data):
            tv_objects.append(
                TranslationValue(
                    translation_key=tk_obj,
                    language=base_lang_code,
                    value=en_value,
                )
            )
            for lang_code in target_lang_codes:
                translated = translate(en_value, lang_code)
                if translated is not None:
                    tv_objects.append(
                        TranslationValue(
                            translation_key=tk_obj,
                            language=lang_code,
                            value=translated,
                        )
                    )

        TranslationValue.objects.bulk_create(tv_objects)

        total_keys = len(tk_objects)
        total_values = len(tv_objects)
        translated_values = total_values - total_keys
        max_possible = total_keys * len(target_lang_codes)
        untranslated = max_possible - translated_values
        self.stdout.write(
            f"Project «{project.slug}»: {total_keys} keys, "
            f"{translated_values}/{max_possible} translated, "
            f"{untranslated} untranslated"
        )
