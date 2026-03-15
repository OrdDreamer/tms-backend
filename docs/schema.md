# Database Schema

Entity-relationship diagram of the TMS data model.

> Generated from Django models. Update this file when models change.

```mermaid
erDiagram
    User {
        bigint id PK
        string email UK
        string first_name
        string last_name
        bool is_active
        bool is_staff
        bool is_superuser
        datetime date_joined
    }

    Project {
        uuid id PK
        string slug UK
        string name
        text description
        datetime created_at
        datetime updated_at
    }

    ProjectLanguage {
        uuid id PK
        uuid project_id FK
        string language
        bool is_base_language
        datetime created_at
        datetime updated_at
    }

    TranslationKey {
        uuid id PK
        uuid project_id FK
        string key
        text description
        datetime created_at
        datetime updated_at
    }

    TranslationValue {
        uuid id PK
        uuid translation_key_id FK
        string language
        text value
        datetime created_at
        datetime updated_at
    }

    Project ||--o{ ProjectLanguage : "has"
    Project ||--o{ TranslationKey : "has"
    TranslationKey ||--o{ TranslationValue : "has"
```

**Constraints:**
- `ProjectLanguage`: unique `(project, language)`, only one `is_base_language=true` per project
- `TranslationKey`: unique `(key, project)`, key format: `^[a-z0-9]+(?:[._][a-z0-9]+)*$`
- `TranslationValue`: unique `(translation_key, language)`
