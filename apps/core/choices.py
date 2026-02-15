from django.db import models


class LanguageChoices(models.TextChoices):
    """Available languages for TMS projects"""

    # Популярні європейські мови
    UKRAINIAN = "uk", "Українська"
    ENGLISH = "en", "English"
    POLISH = "pl", "Polski"
    GERMAN = "de", "Deutsch"
    FRENCH = "fr", "Français"
    SPANISH = "es", "Español"
    ITALIAN = "it", "Italiano"
    PORTUGUESE = "pt", "Português"
    DUTCH = "nl", "Nederlands"
    CZECH = "cs", "Čeština"
    SLOVAK = "sk", "Slovenčina"
    ROMANIAN = "ro", "Română"
    HUNGARIAN = "hu", "Magyar"
    BULGARIAN = "bg", "Български"
    GREEK = "el", "Ελληνικά"
    SWEDISH = "sv", "Svenska"
    DANISH = "da", "Dansk"
    NORWEGIAN = "no", "Norsk"
    FINNISH = "fi", "Suomi"

    # Слов"янські
    RUSSIAN = "ru", "Русский"
    BELARUSIAN = "be", "Беларуская"
    CROATIAN = "hr", "Hrvatski"
    SERBIAN = "sr", "Српски"
    SLOVENIAN = "sl", "Slovenščina"

    # Азіатські
    CHINESE_SIMPLIFIED = "zh-CN", "简体中文"
    CHINESE_TRADITIONAL = "zh-TW", "繁體中文"
    JAPANESE = "ja", "日本語"
    KOREAN = "ko", "한국어"
    VIETNAMESE = "vi", "Tiếng Việt"
    THAI = "th", "ไทย"
    HINDI = "hi", "हिन्दी"
    ARABIC = "ar", "العربية"
    HEBREW = "he", "עברית"
    TURKISH = "tr", "Türkçe"

    # Інші
    INDONESIAN = "id", "Bahasa Indonesia"
    MALAY = "ms", "Bahasa Melayu"
    PERSIAN = "fa", "فارسی"
    BENGALI = "bn", "বাংলা"
    URDU = "ur", "اردو"
    SWAHILI = "sw", "Kiswahili"
