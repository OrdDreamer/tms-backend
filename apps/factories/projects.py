import factory

from apps.projects.models import Project, ProjectLanguage


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    slug = factory.Sequence(lambda n: f"project-{n}")
    name = factory.Sequence(lambda n: f"Project {n}")
    description = ""


class ProjectLanguageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectLanguage

    project = factory.SubFactory(ProjectFactory)
    language = "en"
    is_base_language = True
