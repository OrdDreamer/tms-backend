# Django Styleguide (Minified Reference)

*By Kostiantyn Fedenko*

> This is a minified version of the [full styleguide](STYLEGUIDE.md) optimized for AI context windows.

## Core Principles
- Business logic lives in **utils layer** only
- Also allowed: model `clean()` for validation, model properties for simple derived values
- Never in: views, serializers, model `save()`, managers, querysets, signals

## Models

### BaseModel
```python
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

### Model Rules
- `clean()` for simple field validation; move multi-model/external validation to utils
- Properties for simple derived values only (no DB queries in properties)
- Always specify `related_name` on ForeignKey/M2M fields
- Use `PROTECT` for critical FK (warehouse, categories); `CASCADE` for ownership (request → items)
- Use explicit through models for M2M with extra fields
- Add `CheckConstraint` in `Meta.constraints` for DB-level integrity
- Use `TextChoices` for status/choice fields; inner `class Limits` for business constants
- Always set `Meta.ordering`

```python
class BuyoutRequestStatus(models.TextChoices):
    NEW = "NEW", "New Request"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    AWAITING_PAYMENT = "AWAITING_PAYMENT", "Awaiting Payment"
    PAID = "PAID", "Paid"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"

class Customer(BaseModel):
    class Limits:
        MAX_BUYOUT_REQUESTS_PER_DAY = 10

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_verified(self) -> bool:
        return self.documents.filter(status="ACCEPTED").exists()
```

## Utils Layer

### Function Naming
- `{model}_{action}` — e.g. `buyout_request_create`, `customer_list_active`, `buyout_request_approve_payment`
- Use keyword-only args (`*`) for all utils functions

### Structure for Large Apps
```
buyout/
└── utils/
    ├── __init__.py   # re-exports all public functions
    ├── requests.py
    ├── items.py
    └── notifications.py
```

### Create Pattern
```python
def buyout_request_create(*, customer: Customer, items_data: List[dict], warehouse_id: int) -> BuyoutRequest:
    with transaction.atomic():
        request = BuyoutRequest.objects.create(customer=customer, warehouse_id=warehouse_id)
        for item_data in items_data:
            buyout_item_create(request=request, **item_data)
        request.calculate_total()
        request.save()
        transaction.on_commit(lambda: email_send_created.delay(request.id))
    return request
```

### List/Get Pattern
```python
def customer_list_active(*, search: str = None) -> QuerySet[Customer]:
    qs = Customer.objects.filter(is_active=True).select_related("country").order_by("-created_at")
    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(email__icontains=search))
    return qs

def customer_get_with_stats(*, customer_id: int) -> Optional[Customer]:
    try:
        return Customer.objects.select_related("country").prefetch_related("documents").annotate(
            total_requests=Count("buyout_requests")
        ).get(id=customer_id)
    except Customer.DoesNotExist:
        return None
```

### Transaction Pattern
```python
@transaction.atomic
def buyout_request_approve_payment(*, request_id: int, payment_amount: Decimal, payment_reference: str) -> BuyoutRequest:
    request = BuyoutRequest.objects.select_for_update().get(id=request_id)  # prevent race conditions
    if request.status != BuyoutRequestStatus.AWAITING_PAYMENT:
        raise ValidationError(f"Cannot approve payment for status {request.status}")
    if payment_amount != request.total_cost:
        raise ValidationError("Payment amount does not match request total")
    request.status = BuyoutRequestStatus.PAID
    request.payment_reference = payment_reference
    request.save(update_fields=["status", "payment_reference", "updated_at"])
    shipment_create_from_buyout_request(request=request)
    transaction.on_commit(lambda: email_send_payment_confirmation.delay(request.id))
    return request
```
- Use `select_for_update()` to prevent race conditions
- Use `save(update_fields=[...])` for targeted updates
- Fire async tasks via `transaction.on_commit()` to avoid premature execution

## APIs & Serializers

### Serializer Organization
```
orders/serializers/
├── __init__.py   # re-exports
├── api.py        # API input/output serializers
└── fetch.py      # external data validation serializers
```

### View Rules
- Views handle HTTP only; delegate all logic to utils
- Use `APIView`, not generic views or viewsets
- Validate input with serializer, call util, return output serializer

```python
class OrderListAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request):
        filters_serializer = OrderListFilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        orders = order_list(customer=request.user, **filters_serializer.validated_data)
        paginator = self.Pagination()
        page = paginator.paginate_queryset(orders, request, view=self)
        if page is not None:
            return paginator.get_paginated_response(OrderListOutputSerializer(page, many=True).data)
        return Response(OrderListOutputSerializer(orders, many=True).data)

class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = order_create(customer=request.user, **serializer.validated_data)
        return Response({"id": order.id}, status=status.HTTP_201_CREATED)
```

### Serializer Rules
- Use `serializers.Serializer`, not `ModelSerializer` (explicit control)
- Separate input (filter/create) from output serializers
- Avoid nested serializers; max 2 levels when unavoidable
- Validate FK existence in serializer `validate_<field>()` methods

### APIView Naming: `[Entity][Action]APIView`
- `OrderListAPIView` — GET collection
- `OrderCreateAPIView` — POST
- `OrderDetailAPIView` — GET by id
- `OrderUpdateAPIView` — PUT/PATCH
- `OrderDeleteAPIView` — DELETE
- `OrderListCreateAPIView` — GET + POST
- `OrderDetailUpdateAPIView` — GET + PUT/PATCH
- `OrderCancelAPIView` — domain action (POST)

## URL Organization

### URL Names: `[entity]-[action]` (hyphens, lowercase)
| View | URL Name |
|------|----------|
| List / ListCreate | `order-list` |
| Detail / DetailUpdate / DetailDelete | `order-detail` |
| Custom action | `order-cancel`, `order-approve`, `customer-verify` |

```python
order_patterns = [
    path("", OrderListCreateAPIView.as_view(), name="order-list"),
    path("<uuid:order_id>/", OrderDetailUpdateAPIView.as_view(), name="order-detail"),
    path("<uuid:order_id>/cancel/", OrderCancelAPIView.as_view(), name="order-cancel"),
]
urlpatterns = [
    path("orders/", include((order_patterns, "orders"))),
]
# root urls.py
urlpatterns = [
    path("api/v1/buyout/", include("buyout.urls")),
]
```

## Admin Interface

### Rules
- Minimalistic — only essential operations
- Always `select_related` + `annotate` in `get_queryset()`
- Use `raw_id_fields` for FK with many records
- Use `format_html` + `reverse()` for linked columns
- Always set `readonly_fields` for auto fields (`id`, `created_at`, `updated_at`)
- Actions call utils functions; never put business logic directly in action methods

```python
@admin.register(BuyoutRequest)
class BuyoutRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_link", "status", "total_cost", "items_count", "created_at"]
    list_filter = ["status", "warehouse", "created_at"]
    search_fields = ["customer__email", "id"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["customer"]
    inlines = [BuyoutItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("customer", "warehouse").annotate(items_count=Count("items"))

    def customer_link(self, obj):
        url = reverse("admin:customer_customer_change", args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)

    actions = ["approve_requests"]

    def approve_requests(self, request, queryset):
        for buyout_request in queryset.filter(status=BuyoutRequestStatus.AWAITING_PAYMENT):
            try:
                buyout_request_approve(request_id=buyout_request.id)  # call utils
            except Exception as e:
                messages.error(request, f"Error: {e}")
```

### Inlines
```python
class BuyoutItemInline(admin.TabularInline):
    model = BuyoutItem
    extra = 0
    fields = ["name", "price", "quantity", "category", "status"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["category"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")
```

## Settings & Configuration

```
settings/
├── base.py
├── local.py
├── production.py
└── test.py
```

```python
# settings/base.py
import environ
env = environ.Env()

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
DATABASE_URL = env("DATABASE_URL")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
USE_S3_STORAGE = env.bool("USE_S3_STORAGE", default=False)
MAX_BUYOUT_ITEMS_PER_REQUEST = env.int("MAX_BUYOUT_ITEMS_PER_REQUEST", default=50)
```

### Multi-language
- Store per-language fields: `name_en`, `name_ru`, `name_uk`, etc.
- `get_localized_name(language_code)` method on model using `getattr(self, f"name_{lang}")`
- `USE_I18N = True`, `LOCALE_PATHS = [BASE_DIR / "locale"]`

## Error Handling

```python
# core/exceptions.py
class ApplicationError(Exception):
    def __init__(self, message: str, extra: dict = None):
        self.message = message
        self.extra = extra or {}
        super().__init__(self.message)

class ValidationError(ApplicationError): pass
class PermissionError(ApplicationError): pass
class BuyoutError(ApplicationError): pass

# buyout/exceptions.py
class BuyoutRequestLimitExceeded(BuyoutError): pass
class InsufficientPayment(BuyoutError): pass
class InvalidBuyoutStatus(BuyoutError): pass
```

```python
# core/exception_handlers.py
def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        return Response({"message": "Validation error", "extra": {"details": str(exc)}}, status=400)
    if isinstance(exc, ApplicationError):
        return Response({"message": exc.message, "extra": exc.extra}, status=400)
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"message": "Request failed", "extra": response.data}
    return response

# settings.py
REST_FRAMEWORK = {"EXCEPTION_HANDLER": "core.exception_handlers.custom_exception_handler"}
```

- Raise `ApplicationError` (or subclass) in utils for business rule violations
- Standard error response shape: `{"message": str, "extra": dict}`

## Testing

### Structure
```
buyout/tests/
├── factories.py
├── utils/
│   ├── test_requests.py
│   └── test_payments.py
├── models/
│   └── test_buyout_request.py
└── apis/
    └── test_buyout_create_api.py
```

### Rules
- Test the utils layer primarily; API tests are secondary
- Use `factory_boy` factories for all test data
- Test both happy path and error cases
- Use `@patch` for external calls (email tasks, etc.)

```python
class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
    first_name = factory.Faker("first_name")
    email = factory.Faker("email")
    is_active = True
    is_verified = True

class BuyoutRequestFactory(DjangoModelFactory):
    class Meta:
        model = BuyoutRequest
    customer = factory.SubFactory(CustomerFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    status = BuyoutRequestStatus.NEW
    total_cost = Decimal("0.00")

class BuyoutRequestCreateTests(TestCase):
    def setUp(self):
        self.customer = CustomerFactory(is_verified=True)

    def test_raises_error_for_unverified_customer(self):
        self.customer.is_verified = False
        self.customer.save()
        with self.assertRaises(ValidationError):
            buyout_request_create(customer=self.customer, warehouse_id=1, items_data=[])

    @patch("buyout.tasks.email_send_payment_confirmation.delay")
    def test_payment_approval_sends_email(self, mock_email):
        request = BuyoutRequestFactory(status=BuyoutRequestStatus.AWAITING_PAYMENT, total_cost=Decimal("100.00"))
        buyout_request_approve_payment(request_id=request.id, payment_amount=Decimal("100.00"), payment_reference="PAY123")
        request.refresh_from_db()
        self.assertEqual(request.status, BuyoutRequestStatus.PAID)
        mock_email.assert_called_once_with(request.id)
```

## Celery Tasks

### Rules
- Tasks are thin wrappers: fetch object, call utils function, return status string
- Import models inside task function body to avoid circular imports
- `ApplicationError` → do not retry; other exceptions → retry with exponential backoff
- Fire tasks via `transaction.on_commit()` when inside atomic blocks

```python
@shared_task
def buyout_request_created_notification(request_id):
    try:
        request = BuyoutRequest.objects.select_related("customer").get(id=request_id)
    except BuyoutRequest.DoesNotExist:
        return f"BuyoutRequest {request_id} not found"
    buyout_request_send_notification(request=request, notification_type="created")
    return f"Notification sent for request {request_id}"

@shared_task(bind=True, max_retries=3)
def process_buyout_payment(self, request_id, payment_data):
    try:
        from buyout.utils import buyout_request_process_payment
        request = BuyoutRequest.objects.get(id=request_id)
        buyout_request_process_payment(request=request, payment_data=payment_data)
    except ApplicationError as exc:
        raise exc  # no retry
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Periodic Tasks
- Use `django-celery-beat` with `DatabaseScheduler`
- Register via management command using `PeriodicTask.objects.update_or_create()`
- Route tasks by app: `CELERY_TASK_ROUTES = {"buyout.tasks.*": {"queue": "buyout"}}`

```python
# project/celery.py
app = Celery("project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# settings.py
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
```

## Performance Optimization

- `select_related()` for FK/OneToOne; `prefetch_related()` / `Prefetch()` for reverse/M2M
- `annotate()` for counts/sums instead of Python-side aggregation
- `aggregate()` for single-query stats
- `select_for_update()` inside atomic blocks to prevent race conditions
- `save(update_fields=[...])` for targeted updates
- `bulk_update()` / `.update()` for batch changes
- Add `Meta.indexes` for columns used in frequent filters/ordering
- Cache with `django.core.cache` for expensive repeated reads (invalidate on write)

```python
class BuyoutRequest(BaseModel):
    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["warehouse", "status"]),
        ]
```
