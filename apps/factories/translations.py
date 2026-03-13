import factory

from apps.translations.models import TranslationKey, TranslationValue


class TranslationKeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TranslationKey

    project = factory.SubFactory("apps.factories.projects.ProjectFactory")
    key = factory.Sequence(lambda n: f"section.key{n}")
    description = ""


class TranslationValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TranslationValue

    translation_key = factory.SubFactory(TranslationKeyFactory)
    language = "en"
    value = factory.Faker("sentence")
