# Django Styleguide

*By Kostiantyn Fedenko*

A comprehensive guide for building scalable Django applications with Django REST Framework APIs and admin interfaces, focusing on e-commerce and marketplace applications.

**Table of contents:**

<!-- toc -->

- [Overview](#overview)
- [Architecture](#architecture)
- [Models](#models)
  - [Base model](#base-model)
  - [Validation](#validation)
  - [Properties and Methods](#properties-and-methods)
  - [Model Relationships](#model-relationships)
  - [Constants and Choices](#constants-and-choices)
- [Utils Layer](#utils-layer)
  - [Business Logic Organization](#business-logic-organization)
  - [Example Structure](#example-structure)
  - [Data Access Patterns](#data-access-patterns)
  - [Transaction Management](#transaction-management)
- [APIs & Serializers](#apis--serializers)
  - [API Structure](#api-structure)
  - [List APIs with Filtering](#list-apis-with-filtering)
  - [Create and Update APIs](#create-and-update-apis)
  - [Advanced Serialization](#advanced-serialization)
  - [APIView Naming Conventions](#apiview-naming-conventions)
- [Admin Interface](#admin-interface)
  - [Enhanced Admin Classes](#enhanced-admin-classes)
  - [Custom Actions](#custom-actions)
  - [Inline Administration](#inline-administration)
- [URL Organization](#url-organization)
  - [URL Names Convention](#url-names-convention)
- [Settings & Configuration](#settings--configuration)
  - [Environment Variables](#environment-variables)
  - [Multi-language Support](#multi-language-support)
- [Error Handling](#error-handling)
  - [Custom Exceptions](#custom-exceptions)
  - [API Error Responses](#api-error-responses)
- [Testing](#testing)
  - [Test Organization](#test-organization)
  - [Factories and Fixtures](#factories-and-fixtures)
  - [Utils Testing](#utils-testing)
- [Celery Tasks](#celery-tasks)
  - [Task Structure](#task-structure)
  - [Error Handling](#error-handling-1)
  - [Periodic Tasks](#periodic-tasks)
- [Performance Optimization](#performance-optimization)

<!-- tocstop -->

## Overview

The core principle of this Django Styleguide is **separation of concerns**:

**Business logic should live in:**
- **Utils** - A dedicated layer where the core business logic lives
- Model properties (simple, non-relational calculations)
- Model `clean` methods for validation

**Business logic should NOT live in:**
- API views and serializers
- Model `save` methods
- Custom managers or querysets
- Signals

## Architecture

This styleguide promotes patterns optimized for product-scale applications:

### Core Technologies
- **Django REST Framework (DRF)**: Primary API framework
- **Django Admin**: Minimalistic admin interfaces for operations
- **Celery**: Background task processing and periodic jobs

### Key Principles
- **API-First Design**: All functionality exposed through well-designed REST APIs
- **Pragmatic Admin**: Minimalistic admin interfaces focused on essential operations
- **Separation of Concerns**: Business logic isolated from API and model layers by defining a dedicated "utils" layer

## Models

Models should focus on data modeling with minimal business logic.

### Base model

Define a consistent `BaseModel` for common fields:

```python
from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    created_at = models.DateTimeField(
        db_index=True, default=timezone.now
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Example from the buyout domain:

```python
class BuyoutRequest(BaseModel):
    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="buyout_requests",
    )
    status = models.CharField(
        max_length=50,
        choices=BuyoutRequestStatus.choices,
        default=BuyoutRequestStatus.NEW,
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        ordering = ["-created_at"]
```

### Validation

Use model `clean` methods for simple validation:

```python
class BuyoutItem(BaseModel):
    request = models.ForeignKey(
        BuyoutRequest, on_delete=models.CASCADE, related_name="items"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be positive")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
```

**Move complex validation to the utils layer** if it involves multiple models or external data.

### Properties and Methods

Use properties for simple derived values:

```python
class Customer(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_verified(self) -> bool:
        return self.documents.filter(status="ACCEPTED").exists()
```

### Model Relationships

Design clear, maintainable relationships between models:

```python
class BuyoutRequest(BaseModel):
    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="buyout_requests",
    )
    warehouse = models.ForeignKey(
        "warehouse.Warehouse",
        on_delete=models.PROTECT,
        related_name="buyout_requests",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_cost__gte=0),
                name="buyout_request_positive_cost",
            ),
        ]


class BuyoutItem(BaseModel):
    request = models.ForeignKey(
        BuyoutRequest, on_delete=models.CASCADE, related_name="items"
    )
    category = models.ForeignKey(
        "core.Category", on_delete=models.PROTECT, null=True, blank=True
    )
    # Many-to-many with explicit through model for additional fields
    packages = models.ManyToManyField(
        "shipment.Package",
        through="BuyoutItemPackage",
        related_name="buyout_items",
    )


class BuyoutItemPackage(BaseModel):
    """Through model for BuyoutItem-Package relationship."""

    buyout_item = models.ForeignKey(
        BuyoutItem, on_delete=models.CASCADE
    )
    package = models.ForeignKey(
        "shipment.Package", on_delete=models.CASCADE
    )
    quantity_shipped = models.PositiveIntegerField(default=0)
```

**Relationship Guidelines:**
- Use `PROTECT` for critical foreign keys (warehouse, categories)
- Use `CASCADE` for ownership relationships (request → items)
- Always specify `related_name` for clarity
- Use through models for many-to-many with additional data

### Constants and Choices

Organize constants clearly and consistently:

```python
class BuyoutRequestStatus(models.TextChoices):
    NEW = "NEW", "New Request"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    AWAITING_PAYMENT = "AWAITING_PAYMENT", "Awaiting Payment"
    PAID = "PAID", "Paid"
    SHIPPED = "SHIPPED", "Shipped"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class DocumentStatus(models.TextChoices):
    NEW = "NEW", "New"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    ACCEPTED = "ACCEPTED", "Accepted"
    DECLINED = "DECLINED", "Declined"


class Customer(BaseModel):
    # Use TextChoices for better admin interface
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    email = models.EmailField(unique=True)
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True
    )

    # Constants for business logic
    class Limits:
        MAX_BUYOUT_REQUESTS_PER_DAY = 10
        MAX_PACKAGE_WEIGHT_KG = 30
        MIN_VERIFICATION_DOCUMENTS = 2
```

## Utils Layer

The utils layer is a dedicated layer where the core business logic lives.

### Business Logic Organization

```python
# buyout/utils.py
from typing import List, Optional
from decimal import Decimal
from django.db import transaction
from .models import BuyoutRequest, BuyoutItem


def buyout_request_create(
    *,
    customer: Customer,
    items_data: List[dict],
    warehouse_id: int,
) -> BuyoutRequest:
    """Create a new buyout request with items."""

    with transaction.atomic():
        request = BuyoutRequest.objects.create(
            customer=customer, warehouse_id=warehouse_id
        )

        for item_data in items_data:
            buyout_item_create(request=request, **item_data)

        request.calculate_total()
        request.save()

        # Send notification
        notification_send(
            customer=customer,
            template="buyout_request_created",
            context={"request": request},
        )

    return request


def buyout_request_list(
    *,
    customer: Optional[Customer] = None,
    status: Optional[str] = None,
) -> QuerySet[BuyoutRequest]:
    """Get filtered list of buyout requests."""

    qs = BuyoutRequest.objects.select_related("customer", "warehouse")

    if customer:
        qs = qs.filter(customer=customer)

    if status:
        qs = qs.filter(status=status)

    return qs.order_by("-created_at")
```

### Example Structure

Organize utils in packages for larger applications:

```
buyout/
├── utils/
│   ├── __init__.py          # Exposes main functions
│   ├── requests.py          # BuyoutRequest operations
│   ├── items.py            # BuyoutItem operations
│   └── notifications.py     # Communication utilities
```

In `buyout/utils/__init__.py`:

```python
from .requests import (
    buyout_request_create,
    buyout_request_update,
    buyout_request_list,
)
from .items import (
    buyout_item_create,
    buyout_item_update,
)
from .notifications import (
    buyout_notification_send,
)
```

This allows clean imports:

```python
# Instead of: from buyout.utils.requests import buyout_request_create
from buyout.utils import buyout_request_create
```

### Data Access Patterns

Structure data access functions for optimal database performance:

```python
# customer/utils.py
from django.db.models import Prefetch, Count, Q
from typing import Optional, List

def customer_get_with_stats(
    *, customer_id: int
) -> Optional[Customer]:
    """Get customer with related statistics."""
    try:
        return (
            Customer.objects.select_related(
                "favorite_warehouse", "country"
            )
            .prefetch_related(
                Prefetch(
                    "buyout_requests",
                    queryset=BuyoutRequest.objects.filter(
                        status__in=[
                            BuyoutRequestStatus.PAID,
                            BuyoutRequestStatus.COMPLETED,
                        ]
                    ),
                ),
                "documents",
            )
            .annotate(
                total_requests=Count("buyout_requests"),
                verified_documents=Count(
                    "documents",
                    filter=Q(documents__status=DocumentStatus.ACCEPTED),
                ),
            )
            .get(id=customer_id)
        )
    except Customer.DoesNotExist:
        return None


def customer_list_active(
    *, search: str = None
) -> QuerySet[Customer]:
    """Get list of active customers with optional search."""
    qs = (
        Customer.objects.filter(is_active=True)
        .select_related("country", "favorite_warehouse")
        .order_by("-created_at")
    )

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    return qs


def buyout_request_get_pending_payment() -> QuerySet[BuyoutRequest]:
    """Get requests awaiting payment with items."""
    return (
        BuyoutRequest.objects.filter(
            status=BuyoutRequestStatus.AWAITING_PAYMENT
        )
        .select_related("customer", "warehouse")
        .prefetch_related("items__category")
        .order_by("created_at")
    )
```

### Transaction Management

Use transactions consistently for data integrity:

```python
from django.db import transaction
from django.core.exceptions import ValidationError

@transaction.atomic
def buyout_request_approve_payment(
    *,
    request_id: int,
    payment_amount: Decimal,
    payment_reference: str,
) -> BuyoutRequest:
    """Approve payment for a buyout request."""

    # Use select_for_update to prevent race conditions
    try:
        request = BuyoutRequest.objects.select_for_update().get(
            id=request_id
        )
    except BuyoutRequest.DoesNotExist:
        raise ValidationError("Buyout request not found")

    if request.status != BuyoutRequestStatus.AWAITING_PAYMENT:
        raise ValidationError(
            f"Cannot approve payment for request with status "
            f"{request.status}"
        )

    if payment_amount != request.total_cost:
        raise ValidationError(
            "Payment amount does not match request total"
        )

    # Update request status
    request.status = BuyoutRequestStatus.PAID
    request.payment_reference = payment_reference
    request.save(
        update_fields=["status", "payment_reference", "updated_at"]
    )

    # Create shipment for the request
    shipment_create_from_buyout_request(request=request)

    # Send confirmation email
    transaction.on_commit(
        lambda: email_send_payment_confirmation.delay(request.id)
    )

    return request


@transaction.atomic
def customer_verify_documents(
    *,
    customer_id: int,
    document_ids: List[int],
    verified_by_user_id: int,
) -> Customer:
    """Verify customer documents and update status."""

    customer = Customer.objects.select_for_update().get(id=customer_id)

    # Update documents
    Document.objects.filter(
        id__in=document_ids, customer=customer
    ).update(
        status=DocumentStatus.ACCEPTED,
        verified_by_id=verified_by_user_id,
        verified_at=timezone.now(),
    )

    # Check if customer is now fully verified
    verified_count = customer.documents.filter(
        status=DocumentStatus.ACCEPTED
    ).count()
    if verified_count >= Customer.Limits.MIN_VERIFICATION_DOCUMENTS:
        customer.is_verified = True
        customer.save(update_fields=["is_verified", "updated_at"])

        # Send welcome email
        transaction.on_commit(
            lambda: email_send_verification_complete.delay(customer.id)
        )

    return customer
```

## APIs & Serializers

Keep APIs simple - they should only handle HTTP concerns and delegate to the utils layer.

### Serializer Organization

Organize serializers in separate files for better maintainability:

```
orders/
└── serializers/
    ├── __init__.py
    ├── api.py      # For your API endpoints
    └── fetch.py    # For external data validation
```

In `orders/serializers/__init__.py`:

```python
from .api import (
    OrderListFilterSerializer,
    OrderListOutputSerializer,
    OrderCreateInputSerializer,
    OrderDetailOutputSerializer,
    OrderItemOutputSerializer,
)
from .fetch import (
    ExternalOrderDataSerializer,
    PaymentProviderResponseSerializer,
)
```

### API Structure

```python
# orders/endpoints/orders.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..utils import order_create, order_list
from ..serializers import (
    OrderListOutputSerializer,
    OrderListFilterSerializer,
    OrderCreateInputSerializer
)


class OrderListAPIView(APIView):
    def get(self, request):
        filters_serializer = OrderListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)

        orders = order_list(
            customer=request.user, **filters_serializer.validated_data
        )

        data = OrderListOutputSerializer(orders, many=True).data
        return Response(data)
```

In `orders/serializers/api.py`:

```python
from rest_framework import serializers
from decimal import Decimal


class OrderListFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    warehouse_id = serializers.IntegerField(required=False)


class OrderListOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    total_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    created_at = serializers.DateTimeField()
    items_count = serializers.IntegerField()


class OrderCreateInputSerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=50,
    )

    def validate_warehouse_id(self, value):
        from warehouse.models import Warehouse

        if not Warehouse.objects.filter(
            id=value, is_active=True
        ).exists():
            raise serializers.ValidationError(
                "Invalid warehouse selected"
            )
        return value
```

### List APIs with Filtering

For pagination and filtering, combine DRF utilities with the utils layer:

```python
# orders/endpoints/orders.py
from rest_framework.pagination import LimitOffsetPagination
from ..serializers import OrderListOutputSerializer, OrderListFilterSerializer

class OrderListAPIView(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    def get(self, request):
        filters_serializer = OrderListFilterSerializer(
            data=request.query_params
        )
        filters_serializer.is_valid(raise_exception=True)

        orders = order_list(
            customer=request.user, **filters_serializer.validated_data
        )

        paginator = self.Pagination()
        page = paginator.paginate_queryset(orders, request, view=self)

        if page is not None:
            serializer = OrderListOutputSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = OrderListOutputSerializer(orders, many=True)
        return Response(serializer.data)
```

### Create and Update APIs

```python
# orders/endpoints/orders.py
from ..serializers import OrderCreateInputSerializer

class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = order_create(
            customer=request.user, **serializer.validated_data
        )

        return Response(
            {"id": order.id}, status=status.HTTP_201_CREATED
        )
```

**Avoid nested serializers when possible** - they can lead to performance issues and complex code. Consider flattening data structures or using separate API endpoints instead. When nested serializers are necessary, **limit nesting to 2 levels maximum** to maintain readability and performance.

### External Data Serialization

For external integrations, use the `fetch.py` file in `orders/serializers/fetch.py`:

```python
# orders/serializers/fetch.py
from rest_framework import serializers
from decimal import Decimal


class ExternalOrderDataSerializer(serializers.Serializer):
    """Validate data from external order systems."""

    external_order_id = serializers.CharField(max_length=100)
    customer_email = serializers.EmailField()
    items = serializers.ListField(child=serializers.DictField())
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    currency = serializers.CharField(max_length=3)

    def validate_items(self, value):
        for item in value:
            required_fields = ["name", "price", "quantity"]
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(
                        f"Missing required field: {field}"
                    )
        return value


class PaymentProviderResponseSerializer(serializers.Serializer):
    """Validate payment provider webhook responses."""

    transaction_id = serializers.CharField()
    status = serializers.ChoiceField(
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ]
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    metadata = serializers.DictField(required=False)
```

### APIView Naming Conventions

Follow DRF generic view naming patterns for consistency and clarity. Use the format `[Entity][Action]APIView` where:

- **Entity**: The main model or resource (e.g., `Order`, `Customer`, `Product`)
- **Action**: The operation being performed

**Standard Actions:**
- `List` - List multiple objects (GET collection)
- `Create` - Create new objects (POST)
- `Detail` - Get single object (GET by ID)
- `Update` - Update existing object (PUT/PATCH)
- `Delete` - Delete object (DELETE)

**Examples:**
```python
# Single action endpoints
class OrderListAPIView(APIView):          # GET /orders/
class OrderCreateAPIView(APIView):        # POST /orders/
class OrderDetailAPIView(APIView):        # GET /orders/{id}/
class OrderUpdateAPIView(APIView):        # PUT/PATCH /orders/{id}/
class OrderDeleteAPIView(APIView):        # DELETE /orders/{id}/

# Combined actions (following DRF generic patterns)
class OrderListCreateAPIView(APIView):    # GET + POST /orders/
class OrderDetailUpdateAPIView(APIView):  # GET + PUT/PATCH /orders/{id}/
class OrderDetailDeleteAPIView(APIView):  # GET + DELETE /orders/{id}/

# Domain-specific actions
class OrderCancelAPIView(APIView):        # POST /orders/{id}/cancel/
class OrderApproveAPIView(APIView):       # POST /orders/{id}/approve/
class CustomerVerifyAPIView(APIView):     # POST /customers/{id}/verify/
```

**Avoid:**
- Generic names like `OrderAPIView` or `OrderView`
- Inconsistent patterns like `OrdersList` or `CreateOrder`
- Mixing naming conventions within the same app

## Admin Interface

Build pragmatic Django admin interfaces focused on essential operations:

### Pragmatic Admin Classes

```python
# buyout/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum

@admin.register(BuyoutRequest)
class BuyoutRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer_link', 'status', 'total_cost',
        'items_count', 'created_at', 'warehouse'
    ]
    list_filter = [
        'status', 'warehouse', 'created_at',
        ('customer__country', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'customer__email', 'customer__first_name',
        'customer__last_name', 'id'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_cost_display']
    raw_id_fields = ['customer']

    fieldsets = [
        ('Basic Information', {
            'fields': ['id', 'customer', 'warehouse', 'status']
        }),
        ('Financial', {
            'fields': ['total_cost_display', 'currency', 'payment_reference']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'warehouse'
        ).annotate(
            items_count=Count('items')
        )

    def customer_link(self, obj):
        url = reverse('admin:customer_customer_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)
    customer_link.short_description = 'Customer'

    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = 'Items'
    items_count.admin_order_field = 'items_count'

    def total_cost_display(self, obj):
        return f"{obj.total_cost} {obj.currency}"
    total_cost_display.short_description = 'Total Cost'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'full_name', 'country', 'is_verified',
        'is_active', 'buyout_requests_count', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_verified', 'country',
        'gender', 'created_at'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'verification_status']

    fieldsets = [
        ('Personal Information', {
            'fields': ['email', 'first_name', 'last_name', 'phone', 'gender']
        }),
        ('Location & Preferences', {
            'fields': ['country', 'favorite_warehouse', 'preferred_language']
        }),
        ('Status', {
            'fields': ['is_active', 'is_verified', 'verification_status']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'country', 'favorite_warehouse'
        ).annotate(
            buyout_requests_count=Count('buyout_requests')
        )

    def verification_status(self, obj):
        verified_docs = obj.documents.filter(status=DocumentStatus.ACCEPTED).count()
        total_docs = obj.documents.count()

        if obj.is_verified:
            color = 'green'
            status = 'Verified'
        elif verified_docs > 0:
            color = 'orange'
            status = 'Partial'
        else:
            color = 'red'
            status = 'Unverified'

        return format_html(
            '<span style="color: {};">{} ({}/{})</span>',
            color, status, verified_docs, total_docs
        )
    verification_status.short_description = 'Verification Status'
```

### Custom Actions

```python
from django.contrib import messages
from django.http import HttpResponseRedirect

class BuyoutRequestAdmin(admin.ModelAdmin):
    # ... previous code ...

    actions = ['approve_requests', 'cancel_requests', 'export_to_csv']

    def approve_requests(self, request, queryset):
        """Bulk approve buyout requests."""
        eligible = queryset.filter(status=BuyoutRequestStatus.AWAITING_PAYMENT)

        if not eligible.exists():
            messages.error(request, "No eligible requests for approval")
            return

        count = 0
        for buyout_request in eligible:
            try:
                # Use utils function for business logic
                buyout_request_approve(request_id=buyout_request.id)
                count += 1
            except Exception as e:
                messages.error(request, f"Error approving {buyout_request.id}: {e}")

        messages.success(request, f"Successfully approved {count} requests")

    approve_requests.short_description = "Approve selected requests"

    def cancel_requests(self, request, queryset):
        """Bulk cancel buyout requests."""
        eligible = queryset.exclude(
            status__in=[BuyoutRequestStatus.COMPLETED, BuyoutRequestStatus.CANCELLED]
        )

        count = eligible.update(status=BuyoutRequestStatus.CANCELLED)
        messages.success(request, f"Cancelled {count} requests")

    cancel_requests.short_description = "Cancel selected requests"
```

### Inline Administration

```python
class BuyoutItemInline(admin.TabularInline):
    model = BuyoutItem
    extra = 0
    fields = ['name', 'price', 'quantity', 'category', 'status']
    readonly_fields = ['created_at']
    raw_id_fields = ['category']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ['document_type', 'file', 'status', 'verified_at']
    readonly_fields = ['verified_at', 'created_at']


# Add to main admin classes
class BuyoutRequestAdmin(admin.ModelAdmin):
    # ... previous code ...
    inlines = [BuyoutItemInline]


class CustomerAdmin(admin.ModelAdmin):
    # ... previous code ...
    inlines = [DocumentInline]
```

## URL Organization

Organize URLs for maintainability and clarity:

```python
# buyout/urls.py
from django.urls import path, include

from .endpoints.buyout import (
    BuyoutRequestListAPIView,
    BuyoutRequestCreateAPIView,
    BuyoutRequestDetailAPIView,
    BuyoutRequestUpdateAPIView,
)
from .endpoints.staff import (
    BuyoutRequestAdminListAPIView,
    BuyoutRequestApproveAPIView,
)

# Public API patterns
buyout_patterns = [
    path('', BuyoutRequestListAPIView.as_view(), name='list'),
    path('create/', BuyoutRequestCreateAPIView.as_view(), name='create'),
    path('<uuid:request_id>/', BuyoutRequestDetailAPIView.as_view(), name='detail'),
    path('<uuid:request_id>/update/', BuyoutRequestUpdateAPIView.as_view(), name='update'),
]

# Staff/Admin API patterns
staff_patterns = [
    path('', BuyoutRequestAdminListAPIView.as_view(), name='admin-list'),
    path('<uuid:request_id>/approve/', BuyoutRequestApproveAPIView.as_view(), name='approve'),
]

urlpatterns = [
    path('requests/', include((buyout_patterns, 'buyout-requests'))),
    path('staff/requests/', include((staff_patterns, 'buyout-staff'))),
]

# Main project urls.py
from django.urls import path, include

urlpatterns = [
    path('api/v1/buyout/', include('buyout.urls')),
    path('api/v1/customers/', include('customer.urls')),
    path('api/v1/shipments/', include('shipment.urls')),
]
```

### URL Names Convention

Use consistent URL naming patterns that correspond to your APIView naming convention. Follow the format `[entity]-[action]` where:

- **Entity**: Lowercase model name (e.g., `order`, `customer`, `product`)
- **Action**: The primary action performed (`list`, `detail`, `create`, `update`, `delete`, or custom action name)

**Standard URL Names:**

| View Class                 | URL Pattern               | Method(s)       | Action Type        | URL Name          |
| -------------------------- | ------------------------- | --------------- | ------------------ | ----------------- |
| `OrderListAPIView`         | `/orders/`                | GET             | list               | `order-list`      |
| `OrderCreateAPIView`       | `/orders/`                | POST            | create             | `order-list`      |
| `OrderDetailAPIView`       | `/orders/{id}/`           | GET             | retrieve           | `order-detail`    |
| `OrderUpdateAPIView`       | `/orders/{id}/`           | PUT, PATCH      | update             | `order-detail`    |
| `OrderDeleteAPIView`       | `/orders/{id}/`           | DELETE          | destroy            | `order-detail`    |
| `OrderListCreateAPIView`   | `/orders/`                | GET, POST       | list + create      | `order-list`      |
| `OrderDetailUpdateAPIView` | `/orders/{id}/`           | GET, PUT, PATCH | retrieve + update  | `order-detail`    |
| `OrderDetailDeleteAPIView` | `/orders/{id}/`           | GET, DELETE     | retrieve + destroy | `order-detail`    |
| `OrderCancelAPIView`       | `/orders/{id}/cancel/`    | POST            | custom action      | `order-cancel`    |
| `OrderApproveAPIView`      | `/orders/{id}/approve/`   | POST            | custom action      | `order-approve`   |
| `CustomerVerifyAPIView`    | `/customers/{id}/verify/` | POST            | custom action      | `customer-verify` |

**Implementation Example:**

```python
# orders/urls.py
from django.urls import path, include
from .endpoints import (
    OrderListCreateAPIView,
    OrderDetailUpdateAPIView,
    OrderCancelAPIView,
    OrderApproveAPIView,
)

# Order patterns
order_patterns = [
    path("", OrderListCreateAPIView.as_view(), name="order-list"),
    path(
        "<uuid:order_id>/",
        OrderDetailUpdateAPIView.as_view(),
        name="order-detail",
    ),
    path(
        "<uuid:order_id>/cancel/",
        OrderCancelAPIView.as_view(),
        name="order-cancel",
    ),
    path(
        "<uuid:order_id>/approve/",
        OrderApproveAPIView.as_view(),
        name="order-approve",
    ),
]

urlpatterns = [
    path("orders/", include((order_patterns, "orders"))),
]
```

**Key Principles:**
- Collection endpoints (list/create) use `[entity]-list`
- Individual resource endpoints (detail/update/delete) use `[entity]-detail`
- Custom actions use `[entity]-[action]` (e.g., `order-cancel`, `customer-verify`)
- Use hyphens, not underscores, for URL names
- Keep names lowercase and descriptive

## Settings & Configuration

Organize settings in a modular structure:

```
settings/
├── __init__.py
├── base.py
├── local.py
├── production.py
└── test.py
```

Use environment variables consistently:

```python
# settings/base.py
import environ

env = environ.Env()

DEBUG = env.bool("DEBUG", default=False)
DATABASE_URL = env("DATABASE_URL")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
```

### Environment Variables

Use consistent naming conventions for environment variables:

```python
# settings/base.py
import environ

env = environ.Env()

# Django core settings
DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env("SECRET_KEY")
DATABASE_URL = env("DATABASE_URL")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Application-specific settings
BUYOUT_SERVICE_URL = env("BUYOUT_SERVICE_URL", default="")
MAX_BUYOUT_ITEMS_PER_REQUEST = env.int(
    "MAX_BUYOUT_ITEMS_PER_REQUEST", default=50
)
CUSTOMER_VERIFICATION_REQUIRED = env.bool(
    "CUSTOMER_VERIFICATION_REQUIRED", default=True
)

# External services
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# File storage
USE_S3_STORAGE = env.bool("USE_S3_STORAGE", default=False)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
```

### Multi-language Support

Configure internationalization for global applications:

```python
# settings/base.py
from django.utils.translation import gettext_lazy as _

# Internationalization
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("ru", _("Russian")),
    ("uk", _("Ukrainian")),
    ("uz", _("Uzbek")),
    ("de", _("German")),
    ("kz", _("Kazakh")),
    ("es-mx", _("Spanish (Mexico)")),
    ("pl", _("Polish")),
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Email template language handling
def get_customer_language(customer):
    """Get customer's preferred language or default."""
    if (
        hasattr(customer, "preferred_language")
        and customer.preferred_language
    ):
        return customer.preferred_language
    return LANGUAGE_CODE
```

Example multilingual model fields:

```python
class BuyoutRequestCancellationReason(BaseModel):
    code = models.CharField(max_length=50, unique=True)

    # Multi-language support
    name_en = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    name_uk = models.CharField(max_length=200)
    name_uz = models.CharField(max_length=200)
    name_de = models.CharField(max_length=200)
    name_kz = models.CharField(max_length=200)
    name_es_mx = models.CharField(max_length=200)
    name_pl = models.CharField(max_length=200)

    def get_localized_name(self, language_code="en"):
        """Get name in specified language."""
        field_name = f"name_{language_code.replace('-', '_')}"
        return getattr(self, field_name, self.name_en)
```

## Error Handling

Create consistent error responses:

```python
# core/exceptions.py
class ApplicationError(Exception):
    def __init__(self, message: str, extra: dict = None):
        self.message = message
        self.extra = extra or {}


# config/exception_handlers.py
def custom_exception_handler(exc, context):
    if isinstance(exc, ApplicationError):
        return Response(
            {"message": exc.message, "extra": exc.extra}, status=400
        )

    # Handle other exceptions...
    return default_handler(exc, context)
```

Use in utils:

```python
def buyout_request_create(*, customer: Customer, **kwargs):
    if not customer.is_verified:
        raise ApplicationError(
            message="Customer must be verified to create buyout requests",
            extra={"required_documents": ["passport", "address"]},
        )
```

### Custom Exceptions

Create a hierarchy of application-specific exceptions:

```python
# core/exceptions.py
class ApplicationError(Exception):
    """Base application exception."""
    def __init__(self, message: str, extra: dict = None):
        self.message = message
        self.extra = extra or {}
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation-related errors."""
    pass


class PermissionError(ApplicationError):
    """Permission-related errors."""
    pass


class BuyoutError(ApplicationError):
    """Buyout-specific errors."""
    pass


class CustomerError(ApplicationError):
    """Customer-specific errors."""
    pass


# buyout/exceptions.py
from core.exceptions import BuyoutError

class BuyoutRequestLimitExceeded(BuyoutError):
    """Customer has exceeded their daily buyout request limit."""
    pass


class InsufficientPayment(BuyoutError):
    """Payment amount is insufficient for the request."""
    pass


class InvalidBuyoutStatus(BuyoutError):
    """Operation not allowed for current buyout status."""
    pass
```

### API Error Responses

Implement consistent error handling across all APIs:

```python
# core/exception_handlers.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

def custom_exception_handler(exc, context):
    """Custom exception handler for consistent API errors."""

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        return Response({
            'message': 'Validation error',
            'extra': {'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)}
        }, status=400)

    # Handle custom application errors
    if isinstance(exc, ApplicationError):
        return Response({
            'message': exc.message,
            'extra': exc.extra
        }, status=400)

    # Default DRF handling
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize DRF error format
        custom_response_data = {
            'message': 'Request failed',
            'extra': response.data
        }
        response.data = custom_response_data

    return response


# settings.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "core.exception_handlers.custom_exception_handler",
    # ... other settings
}
```

## Testing

Test the utils layer comprehensively:

```python
# tests/test_buyout_utils.py
from django.test import TestCase
from django.contrib.auth import get_user_model

from buyout.utils import buyout_request_create
from customer.tests.factories import CustomerFactory


class BuyoutRequestCreateTests(TestCase):
    def setUp(self):
        self.customer = CustomerFactory(is_verified=True)

    def test_creates_request_with_items(self):
        items_data = [
            {'name': 'Product 1', 'price': '29.99', 'quantity': 1},
            {'name': 'Product 2', 'price': '15.50', 'quantity': 2}
        ]

        request = buyout_request_create(
            customer=self.customer,
            warehouse_id=1,
            items_data=items_data
        )

        self.assertEqual(request.items.count(), 2)
        self.assertEqual(request.total_cost, Decimal('60.99'))

    def test_raises_error_for_unverified_customer(self):
        self.customer.is_verified = False

        with self.assertRaises(ApplicationError):
            buyout_request_create(
                customer=self.customer,
                warehouse_id=1,
                items_data=[]
            )
```

Use factories for consistent test data:

```python
# customer/tests/factories.py
import factory
from customer.models import Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    is_active = True
    is_verified = True
```

### Test Organization

Structure tests to match your application architecture:

```
buyout/
├── tests/
│   ├── __init__.py
│   ├── factories.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── test_requests.py
│   │   └── test_payments.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── test_buyout_request.py
│   │   └── test_buyout_item.py
│   └── apis/
│       ├── __init__.py
│       ├── test_buyout_list_api.py
│       └── test_buyout_create_api.py
```

### Factories and Fixtures

Use factories for consistent, maintainable test data:

```python
# buyout/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from decimal import Decimal

from buyout.models import BuyoutRequest, BuyoutItem
from customer.tests.factories import CustomerFactory
from warehouse.tests.factories import WarehouseFactory


class BuyoutRequestFactory(DjangoModelFactory):
    class Meta:
        model = BuyoutRequest

    customer = factory.SubFactory(CustomerFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    status = BuyoutRequestStatus.NEW
    total_cost = Decimal('0.00')
    currency = 'USD'


class BuyoutItemFactory(DjangoModelFactory):
    class Meta:
        model = BuyoutItem

    request = factory.SubFactory(BuyoutRequestFactory)
    name = factory.Faker('word')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    quantity = factory.Faker('random_int', min=1, max=10)
    product_url = factory.Faker('url')

    @factory.post_generation
    def update_request_total(self, create, extracted, **kwargs):
        """Update the request total after creating items."""
        if create:
            self.request.calculate_total()
            self.request.save()


# Usage in tests
class BuyoutRequestCreateTests(TestCase):
    def setUp(self):
        self.customer = CustomerFactory(is_verified=True)
        self.warehouse = WarehouseFactory()

    def test_creates_request_with_multiple_items(self):
        request = BuyoutRequestFactory(
            customer=self.customer,
            warehouse=self.warehouse
        )
        BuyoutItemFactory.create_batch(3, request=request)

        self.assertEqual(request.items.count(), 3)
        self.assertGreater(request.total_cost, 0)
```

### Utils Testing

Focus testing on the business logic layer:

```python
# buyout/tests/utils/test_requests.py
from decimal import Decimal
from django.test import TestCase
from django.db import transaction

from buyout.utils import buyout_request_create, buyout_request_approve_payment
from buyout.models import BuyoutRequestStatus
from core.exceptions import ValidationError


class BuyoutRequestCreateTests(TestCase):
    def setUp(self):
        self.customer = CustomerFactory(is_verified=True)
        self.warehouse = WarehouseFactory()
        self.items_data = [
            {'name': 'Product 1', 'price': '29.99', 'quantity': 1},
            {'name': 'Product 2', 'price': '15.50', 'quantity': 2}
        ]

    def test_creates_request_successfully(self):
        request = buyout_request_create(
            customer=self.customer,
            warehouse_id=self.warehouse.id,
            items_data=self.items_data
        )

        self.assertEqual(request.customer, self.customer)
        self.assertEqual(request.warehouse, self.warehouse)
        self.assertEqual(request.items.count(), 2)
        self.assertEqual(request.total_cost, Decimal('60.99'))

    def test_raises_error_for_unverified_customer(self):
        self.customer.is_verified = False
        self.customer.save()

        with self.assertRaises(ValidationError) as context:
            buyout_request_create(
                customer=self.customer,
                warehouse_id=self.warehouse.id,
                items_data=self.items_data
            )

        self.assertIn('verified', str(context.exception))

    def test_calculates_total_correctly(self):
        request = buyout_request_create(
            customer=self.customer,
            warehouse_id=self.warehouse.id,
            items_data=self.items_data
        )

        expected_total = Decimal('29.99') + (Decimal('15.50') * 2)
        self.assertEqual(request.total_cost, expected_total)

    @patch('buyout.tasks.email_send_payment_confirmation.delay')
    def test_payment_approval_sends_email(self, mock_email):
        request = BuyoutRequestFactory(
            status=BuyoutRequestStatus.AWAITING_PAYMENT,
            total_cost=Decimal('100.00')
        )

        buyout_request_approve_payment(
            request_id=request.id,
            payment_amount=Decimal('100.00'),
            payment_reference='PAY123'
        )

        request.refresh_from_db()
        self.assertEqual(request.status, BuyoutRequestStatus.PAID)
        mock_email.assert_called_once_with(request.id)
```

## Celery Tasks

Celery is used for background task processing and periodic jobs in our applications. We treat Celery tasks as an interface to our core business logic.

### Task Structure

Keep tasks simple - they should fetch data and call utils functions:

```python
# buyout/tasks.py
from celery import shared_task
from django.utils import timezone

from buyout.models import BuyoutRequest
from buyout.utils import buyout_request_send_notification


@shared_task
def buyout_request_created_notification(request_id):
    """Send notification when a buyout request is created."""
    try:
        request = BuyoutRequest.objects.select_related('customer').get(id=request_id)
    except BuyoutRequest.DoesNotExist:
        # Log the error but don't retry for non-existent objects
        return f"BuyoutRequest {request_id} not found"

    # Use utils function for business logic
    buyout_request_send_notification(
        request=request,
        notification_type='created'
    )

    return f"Notification sent for request {request_id}"


@shared_task
def customer_welcome_email(customer_id):
    """Send welcome email to newly verified customer."""
    from customer.models import Customer
    from customer.utils import customer_send_welcome_email

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return f"Customer {customer_id} not found"

    # Call utils function
    customer_send_welcome_email(customer=customer)

    return f"Welcome email sent to {customer.email}"
```

**Key principles:**
- Tasks call utils functions for business logic
- Import models within task functions to avoid circular imports
- Keep tasks focused on a single responsibility
- Return meaningful success messages for monitoring

### Error Handling

Implement robust error handling with retries:

```python
from celery import shared_task
from celery.utils.log import get_task_logger
from decimal import Decimal

from core.exceptions import ApplicationError
from buyout.models import BuyoutRequest


logger = get_task_logger(__name__)


def _payment_processing_failure(self, exc, task_id, args, kwargs, einfo):
    """Handle payment processing failures."""
    request_id = args[0]

    logger.error(f"Payment processing failed for request {request_id}: {exc}")

    # Call utils function to handle failure
    from buyout.utils import buyout_request_mark_payment_failed

    try:
        buyout_request_mark_payment_failed(
            request_id=request_id,
            error_message=str(exc)
        )
    except Exception as e:
        logger.error(f"Failed to mark payment as failed: {e}")


@shared_task(bind=True, on_failure=_payment_processing_failure, max_retries=3)
def process_buyout_payment(self, request_id, payment_data):
    """Process payment for a buyout request."""
    try:
        request = BuyoutRequest.objects.get(id=request_id)

        # Use utils function for business logic
        from buyout.utils import buyout_request_process_payment

        buyout_request_process_payment(
            request=request,
            payment_data=payment_data
        )

        return f"Payment processed for request {request_id}"

    except ApplicationError as exc:
        # Don't retry application errors
        logger.warning(f"Application error processing payment: {exc}")
        raise exc

    except Exception as exc:
        # Retry other errors with exponential backoff
        logger.warning(f"Error processing payment, retrying: {exc}")
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=5)
def send_customer_email(self, customer_id, template_name, context=None):
    """Send email to customer with retry logic."""
    from customer.utils import customer_send_email

    try:
        customer_send_email(
            customer_id=customer_id,
            template_name=template_name,
            context=context or {}
        )

    except Exception as exc:
        if self.request.retries < self.max_retries:
            # Exponential backoff: 1min, 2min, 4min, 8min, 16min
            countdown = 60 * (2 ** self.request.retries)
            logger.warning(
                f"Email sending failed, retrying in {countdown}s: {exc}"
            )
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Final failure - log and don't retry
            logger.error(f"Email sending failed permanently: {exc}")
            raise exc
```

### Periodic Tasks

Manage recurring tasks with database-driven configuration:

```python
# buyout/tasks.py
@shared_task
def cleanup_expired_buyout_requests():
    """Clean up buyout requests that have been abandoned."""
    from buyout.utils import buyout_request_cleanup_expired

    cutoff_date = timezone.now() - timezone.timedelta(days=30)

    cleaned_count = buyout_request_cleanup_expired(cutoff_date=cutoff_date)

    return f"Cleaned up {cleaned_count} expired requests"


@shared_task
def send_payment_reminders():
    """Send payment reminders for pending buyout requests."""
    from buyout.utils import buyout_request_send_payment_reminders

    reminder_count = buyout_request_send_payment_reminders()

    return f"Sent {reminder_count} payment reminders"


@shared_task
def customer_verification_reminder():
    """Send verification reminders to unverified customers."""
    from customer.utils import customer_send_verification_reminders

    cutoff_date = timezone.now() - timezone.timedelta(days=7)

    reminder_count = customer_send_verification_reminders(
        registered_before=cutoff_date
    )

    return f"Sent {reminder_count} verification reminders"


# Management command to set up periodic tasks
# management/commands/setup_periodic_tasks.py
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Setup periodic Celery tasks'

    def handle(self, *args, **options):
        # Daily cleanup at 2 AM
        daily_2am, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=2,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Every 6 hours for payment reminders
        every_6h, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour='*/6',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Weekly verification reminders on Monday at 10 AM
        weekly_monday, _ = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=10,
            day_of_week=1,  # Monday
            day_of_month='*',
            month_of_year='*',
        )

        periodic_tasks = [
            {
                'name': 'Cleanup expired buyout requests',
                'task': 'buyout.tasks.cleanup_expired_buyout_requests',
                'crontab': daily_2am,
                'enabled': True,
            },
            {
                'name': 'Send payment reminders',
                'task': 'buyout.tasks.send_payment_reminders',
                'crontab': every_6h,
                'enabled': True,
            },
            {
                'name': 'Send verification reminders',
                'task': 'buyout.tasks.customer_verification_reminder',
                'crontab': weekly_monday,
                'enabled': True,
            },
        ]

        for task_config in periodic_tasks:
            task, created = PeriodicTask.objects.update_or_create(
                name=task_config['name'],
                defaults={
                    'task': task_config['task'],
                    'crontab': task_config['crontab'],
                    'enabled': task_config['enabled'],
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f"{action}: {task.name}")
```

**Celery Configuration Example:**

```python
# project/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# settings.py
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="redis://localhost:6379/0"
)
CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND", default="redis://localhost:6379/0"
)

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

# Task routing
CELERY_TASK_ROUTES = {
    "buyout.tasks.*": {"queue": "buyout"},
    "customer.tasks.*": {"queue": "customer"},
    "*.send_email": {"queue": "emails"},
}

# Use django-celery-beat for periodic tasks
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

## Performance Optimization

Optimize database queries and application performance:

```python
# buyout/utils.py - Optimized queries
def buyout_request_dashboard_data(*, customer: Customer) -> dict:
    """Get dashboard data with optimized queries."""

    # Single query with annotations for counts
    request_stats = BuyoutRequest.objects.filter(
        customer=customer
    ).aggregate(
        total_requests=Count('id'),
        active_requests=Count('id', filter=Q(
            status__in=[BuyoutRequestStatus.NEW, BuyoutRequestStatus.IN_PROGRESS]
        )),
        completed_requests=Count('id', filter=Q(
            status=BuyoutRequestStatus.COMPLETED
        )),
        total_spent=Sum('total_cost', filter=Q(
            status__in=[BuyoutRequestStatus.PAID, BuyoutRequestStatus.COMPLETED]
        )) or Decimal('0.00')
    )

    # Recent requests with prefetch
    recent_requests = BuyoutRequest.objects.filter(
        customer=customer
    ).select_related(
        'warehouse'
    ).prefetch_related(
        Prefetch(
            'items',
            queryset=BuyoutItem.objects.select_related('category')
        )
    ).order_by('-created_at')[:5]

    return {
        'stats': request_stats,
        'recent_requests': recent_requests,
        'customer_verified': customer.is_verified,
    }


# Use database indexes for common queries
class BuyoutRequest(BaseModel):
    # ... fields ...

    class Meta:
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['warehouse', 'status']),
        ]


# Cache frequently accessed data
from django.core.cache import cache

def get_customer_verification_status(customer_id: int) -> bool:
    """Get customer verification status with caching."""
    cache_key = f'customer_verified:{customer_id}'

    verified = cache.get(cache_key)
    if verified is None:
        try:
            customer = Customer.objects.get(id=customer_id)
            verified = customer.is_verified
            cache.set(cache_key, verified, timeout=3600)  # Cache for 1 hour
        except Customer.DoesNotExist:
            verified = False

    return verified


# Bulk operations for efficiency
def buyout_items_bulk_update_status(
    *,
    item_ids: List[int],
    status: str
) -> int:
    """Bulk update status for multiple items."""
    return BuyoutItem.objects.filter(
        id__in=item_ids
    ).update(
        status=status,
        updated_at=timezone.now()
    )
```

---

This styleguide represents proven patterns for building maintainable, scalable Django applications. The key is consistent application of these patterns across your entire codebase, creating a unified development experience for your team.

**Remember:**
- Keep business logic in the utils layer
- Build minimalistic admin interfaces for essential operations only
- Structure tests to match your application architecture
- Optimize database queries early and often
- Handle errors consistently across all components
- Use background tasks for time-consuming operations

Apply these patterns systematically, and you'll have a robust foundation for scaling your Django application to handle real-world production demands.
