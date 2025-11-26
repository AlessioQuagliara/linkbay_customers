# LinkBay Customers

**Version**: 0.1.0  
**License**: MIT  
**Python**: 3.8+  

Multi-tenant customer management system for FastAPI with GDPR compliance and AI-powered analytics.

---

## Table of Contents

- [What is LinkBay Customers?](#what-is-linkbay-customers)
- [Who Should Use This Library](#who-should-use-this-library)
- [Who Should NOT Use This Library](#who-should-not-use-this-library)
- [Installation](#installation)
- [Core Features](#core-features)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
  - [Customer Service](#customer-service)
  - [GDPR Service](#gdpr-service)
  - [AI Service](#ai-service)
  - [REST API Endpoints](#rest-api-endpoints)
- [Data Models](#data-models)
- [Schemas](#schemas)
- [GDPR Compliance](#gdpr-compliance)
- [AI-Powered Features](#ai-powered-features)
- [Advanced Usage](#advanced-usage)
- [Testing](#testing)
- [Dependencies](#dependencies)
- [License](#license)
- [Support](#support)

---

## What is LinkBay Customers?

`linkbay-customers` is a comprehensive, production-ready customer management system designed for FastAPI applications with multi-tenant architecture. It provides a complete solution for managing customer data, addresses, notes, analytics, and AI-powered insights while ensuring full GDPR compliance.

Unlike monolithic CRM systems, LinkBay Customers is a flexible library that integrates seamlessly with your existing FastAPI application. It uses a dynamic model system that works with any SQLAlchemy session and custom models, making it highly adaptable to your specific requirements.

**Key capabilities:**
- Multi-tenant data isolation with tenant-based queries and constraints
- Complete GDPR compliance suite (right to access, right to erasure, consent tracking)
- AI-powered customer analytics (segmentation, CLV prediction, churn risk scoring)
- Customer similarity search using vector embeddings
- Flexible data models that extend your existing database schema
- Production-ready REST API with comprehensive validation
- Merge functionality for duplicate customer resolution

---

## Who Should Use This Library

This library is designed for:

- **SaaS application developers**: Building multi-tenant B2B or B2C platforms that need customer management
- **E-commerce platforms**: Requiring customer profiles, order analytics, and segmentation
- **CRM builders**: Need building blocks for custom CRM solutions with GDPR compliance
- **FastAPI developers**: Looking for production-ready customer management without building from scratch
- **European businesses**: Requiring GDPR compliance for customer data handling
- **Data-driven applications**: Wanting AI-powered customer insights (CLV, churn prediction, segmentation)
- **Teams needing flexibility**: Want to customize database models while maintaining core functionality
- **Growth-focused companies**: Need customer analytics and behavioral segmentation

---

## Who Should NOT Use This Library

This library may not be suitable if:

- **You need a complete CRM**: This is a library providing building blocks, not a full-featured CRM with UI, workflows, and campaign management
- **You don't use FastAPI**: The router and dependency system are designed specifically for FastAPI
- **You don't use SQLAlchemy**: All database operations are built on SQLAlchemy ORM
- **You don't need multi-tenancy**: Single-tenant applications don't benefit from the tenant isolation features
- **You want plug-and-play simplicity**: This requires integration work - defining models, configuring services, and implementing authentication
- **You need real-time AI**: The AI features use heuristics by default; production ML requires LinkBay-AI integration
- **You use Django**: This library is FastAPI-specific; Django has its own ORM and patterns
- **You prefer GraphQL**: The API is RESTful; GraphQL requires custom integration

---

## Installation

Install via pip (when published):

```bash
pip install linkbay-customers
```

With AI support (embeddings, pgvector for similarity search):

```bash
pip install linkbay-customers[ai]
```

For development:

```bash
pip install linkbay-customers[dev]
```

Direct installation from repository:

```bash
pip install git+https://github.com/AlessioQuagliara/LinkBay-Customers.git
```

---

## Core Features

**Multi-Tenant Architecture**
- Complete data isolation between tenants
- Tenant-scoped queries and constraints
- Unique constraints per tenant (email uniqueness)

**GDPR Compliance**
- Right to access: Complete data export in JSON format
- Right to erasure: Data anonymization and deletion
- Consent tracking: Marketing, analytics, cookies consent with timestamps
- Audit trails: Track when and how data was accessed or modified

**Customer Management**
- Full CRUD operations for customers, addresses, and notes
- Advanced search and filtering
- Tag-based organization
- Custom preferences storage (JSON)
- Soft deletion support

**Analytics & Metrics**
- Order analytics: Total orders, total spent, AOV (Average Order Value)
- Customer lifecycle tracking: First and last order dates
- Real-time metrics updates
- Historical trend analysis

**AI-Powered Features**
- Automatic customer segmentation (new, active, high_value, at_risk, dormant, churned)
- Churn risk scoring (0-1 probability)
- Customer Lifetime Value (CLV) prediction
- Customer similarity search using vector embeddings
- Product recommendations based on similar customer behavior

**Flexible Architecture**
- Dynamic model system: Works with any SQLAlchemy models
- Dependency injection: Fully compatible with FastAPI dependencies
- Modular services: Use only what you need
- Extensible schemas: Add custom fields easily

---

## Architecture Overview

LinkBay Customers uses a three-layer architecture:

**1. Models Layer** (Database)
- Mixin-based models (CustomerMixin, AddressMixin, CustomerNoteMixin)
- Extend your existing models without modifying library code
- Full SQLAlchemy ORM support with relationships

**2. Service Layer** (Business Logic)
- `CustomerService`: CRUD operations, search, analytics updates
- `GDPRService`: Data export, deletion, consent management
- `AIService`: Segmentation, predictions, similarity search
- All services work with dependency injection

**3. Router Layer** (API)
- Factory function creates FastAPI router with your configuration
- Complete REST API with OpenAPI documentation
- Automatic validation with Pydantic schemas
- Multi-tenant context from dependencies

---

## Quick Start

### Step 1: Define Your Models

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from linkbay_customers.models import CustomerMixin, AddressMixin, CustomerNoteMixin

Base = declarative_base()

class Customer(Base, CustomerMixin):
    __tablename__ = "customers"

class Address(Base, AddressMixin):
    __tablename__ = "customer_addresses"

class CustomerNote(Base, CustomerNoteMixin):
    __tablename__ = "customer_notes"

# Create tables
engine = create_engine("postgresql://user:pass@localhost/db")
Base.metadata.create_all(engine)
```

### Step 2: Configure Services and Router

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from linkbay_customers import CustomerService, GDPRService, AIService
from linkbay_customers.router import create_customer_router

app = FastAPI()

# Initialize services
customer_service = CustomerService(
    customer_model=Customer,
    address_model=Address,
    note_model=CustomerNote,
)

gdpr_service = GDPRService(
    customer_model=Customer,
    address_model=Address,
    note_model=CustomerNote,
)

ai_service = AIService(customer_model=Customer)

# Dependency functions
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

def get_tenant_id():
    return "tenant_123"  # Extract from JWT token, header, etc.

# Create router
router = create_customer_router(
    get_db=get_db,
    get_tenant_id=get_tenant_id,
    customer_service=customer_service,
    gdpr_service=gdpr_service,
    ai_service=ai_service,
)

app.include_router(router)
```

### Step 3: Start and Use the API

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## API Reference

### Customer Service

The `CustomerService` class handles all customer-related business logic.

#### Initialization

```python
from linkbay_customers import CustomerService

service = CustomerService(
    customer_model=Customer,      # Required: Your Customer model
    address_model=Address,        # Optional: Your Address model
    note_model=CustomerNote,      # Optional: Your CustomerNote model
)
```

#### `create_customer(db, tenant_id, data) -> Customer`

Creates a new customer.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `data` (CustomerCreate): Customer creation data

**Returns:**
- `Customer`: Created customer instance

**Example:**
```python
from linkbay_customers.schemas import CustomerCreate

customer_data = CustomerCreate(
    email="mario.rossi@example.com",
    first_name="Mario",
    last_name="Rossi",
    phone="+393331234567",
    birthday="1990-05-15",
    gender="male",
    preferences={
        "language": "it",
        "newsletter_subscribed": True,
        "marketing_consent": True,
        "analytics_consent": True,
    },
    tags=["vip", "early_adopter"],
)

customer = service.create_customer(db, "tenant_123", customer_data)
```

#### `get_customer(db, tenant_id, customer_id) -> Optional[Customer]`

Retrieves a customer by ID.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID

**Returns:**
- `Customer | None`: Customer instance or None if not found

**Example:**
```python
customer = service.get_customer(db, "tenant_123", 42)
if customer:
    print(f"Found: {customer.email}")
```

#### `list_customers(db, tenant_id, filters, page, page_size) -> Tuple[List[Customer], int]`

Lists customers with filtering and pagination.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `filters` (CustomerSearchFilters): Search and filter criteria
- `page` (int): Page number (1-indexed)
- `page_size` (int): Number of items per page

**Returns:**
- `Tuple[List[Customer], int]`: List of customers and total count

**Example:**
```python
from linkbay_customers.schemas import CustomerSearchFilters

filters = CustomerSearchFilters(
    segment="high_value",
    min_total_spent=1000,
    tags=["vip"],
    email_contains="@gmail.com",
)

customers, total = service.list_customers(
    db, "tenant_123", filters, page=1, page_size=50
)

print(f"Found {total} customers, showing page 1")
for customer in customers:
    print(f"- {customer.email}: ${customer.total_spent}")
```

#### `search_customers(db, tenant_id, query) -> List[Customer]`

Full-text search across customer fields.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `query` (str): Search query

**Returns:**
- `List[Customer]`: List of matching customers

**Searchable fields:**
- Email
- First name
- Last name
- Phone

**Example:**
```python
results = service.search_customers(db, "tenant_123", "mario")
# Returns customers with "mario" in name or email
```

#### `update_customer(db, tenant_id, customer_id, data) -> Optional[Customer]`

Updates customer information.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `data` (CustomerUpdate): Updated fields

**Returns:**
- `Customer | None`: Updated customer or None if not found

**Example:**
```python
from linkbay_customers.schemas import CustomerUpdate

update_data = CustomerUpdate(
    phone="+393339876543",
    preferences={"language": "en"},
)

customer = service.update_customer(db, "tenant_123", 42, update_data)
```

#### `delete_customer(db, tenant_id, customer_id, soft_delete) -> bool`

Deletes a customer.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `soft_delete` (bool): If True, marks as deleted; if False, removes from database

**Returns:**
- `bool`: True if deleted successfully

**Example:**
```python
# Soft delete (recommended)
service.delete_customer(db, "tenant_123", 42, soft_delete=True)

# Hard delete (permanent removal)
service.delete_customer(db, "tenant_123", 42, soft_delete=False)
```

#### `merge_customers(db, tenant_id, merge_request) -> Customer`

Merges two customer records (deduplication).

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `merge_request` (CustomerMergeRequest): Merge configuration

**Returns:**
- `Customer`: Target customer with merged data

**Example:**
```python
from linkbay_customers.schemas import CustomerMergeRequest

merge_request = CustomerMergeRequest(
    source_customer_id=123,  # Will be deleted
    target_customer_id=456,  # Will be kept
    merge_addresses=True,
    merge_notes=True,
    merge_tags=True,
    merge_preferences=True,
)

merged_customer = service.merge_customers(db, "tenant_123", merge_request)
```

#### `update_customer_analytics(db, customer_id, order_data) -> None`

Updates customer analytics metrics after an order.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `customer_id` (int): Customer ID
- `order_data` (dict): Order information

**Order data structure:**
```python
order_data = {
    "total": 99.99,          # Order total amount
    "created_at": datetime,  # Order timestamp
}
```

**Updates:**
- `total_orders`: Increments by 1
- `total_spent`: Adds order total
- `average_order_value`: Recalculates
- `last_order_at`: Updates to order date
- `first_order_at`: Sets if first order

**Example:**
```python
from datetime import datetime

service.update_customer_analytics(
    db,
    customer_id=42,
    order_data={
        "total": 149.99,
        "created_at": datetime.utcnow(),
    }
)
```

#### Address Management

**`add_address(db, tenant_id, customer_id, data) -> Address`**

Adds an address to a customer.

```python
from linkbay_customers.schemas import AddressCreate

address_data = AddressCreate(
    type="shipping",
    address_line1="Via Roma 123",
    address_line2="Interno 4",
    city="Milano",
    state="MI",
    postal_code="20100",
    country="IT",
    is_default=True,
)

address = service.add_address(db, "tenant_123", 42, address_data)
```

**`list_addresses(db, tenant_id, customer_id) -> List[Address]`**

Lists all addresses for a customer.

```python
addresses = service.list_addresses(db, "tenant_123", 42)
for address in addresses:
    print(f"{address.type}: {address.city}, {address.country}")
```

**`update_address(db, tenant_id, customer_id, address_id, data) -> Optional[Address]`**

Updates an address.

```python
from linkbay_customers.schemas import AddressUpdate

update_data = AddressUpdate(
    city="Roma",
    postal_code="00100",
)

address = service.update_address(db, "tenant_123", 42, 1, update_data)
```

**`delete_address(db, tenant_id, customer_id, address_id) -> bool`**

Deletes an address.

```python
service.delete_address(db, "tenant_123", 42, 1)
```

#### Customer Notes

**`add_note(db, tenant_id, customer_id, data, created_by) -> CustomerNote`**

Adds a note to a customer.

```python
from linkbay_customers.schemas import CustomerNoteCreate

note_data = CustomerNoteCreate(
    note="Customer requested expedited shipping for next order",
)

note = service.add_note(
    db,
    "tenant_123",
    42,
    note_data,
    created_by="user_456"
)
```

**`list_notes(db, tenant_id, customer_id) -> List[CustomerNote]`**

Lists all notes for a customer.

```python
notes = service.list_notes(db, "tenant_123", 42)
for note in notes:
    print(f"[{note.created_at}] {note.created_by}: {note.note}")
```

---

### GDPR Service

The `GDPRService` class handles GDPR compliance operations.

#### Initialization

```python
from linkbay_customers import GDPRService

gdpr_service = GDPRService(
    customer_model=Customer,
    address_model=Address,
    note_model=CustomerNote,
)
```

#### `export_customer_data(db, tenant_id, customer_id) -> Optional[Dict]`

Exports all customer data (GDPR Right to Access).

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID

**Returns:**
- `Dict | None`: Complete customer data in JSON format

**Export includes:**
- Personal information
- All addresses
- All notes
- Preferences and consent data
- Analytics metrics
- Tags and metadata

**Example:**
```python
export = gdpr_service.export_customer_data(db, "tenant_123", 42)

if export:
    print(f"Export date: {export['export_date']}")
    print(f"Customer: {export['customer']['email']}")
    print(f"Total orders: {export['customer']['total_orders']}")
    print(f"Addresses: {len(export['addresses'])}")
```

**Sample export structure:**
```json
{
  "export_date": "2025-11-26T10:30:00",
  "export_format": "json",
  "customer": {
    "id": 42,
    "email": "mario.rossi@example.com",
    "first_name": "Mario",
    "last_name": "Rossi",
    "phone": "+393331234567",
    "birthday": "1990-05-15",
    "gender": "male",
    "preferences": {...},
    "tags": ["vip"],
    "total_orders": 15,
    "total_spent": 1499.85,
    "consent_data": {...}
  },
  "addresses": [...],
  "notes": [...],
  "analytics": {...}
}
```

#### `delete_customer_data(db, tenant_id, customer_id, anonymize) -> Dict`

Deletes or anonymizes customer data (GDPR Right to Erasure).

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `anonymize` (bool): If True, anonymize; if False, hard delete

**Returns:**
- `Dict`: Deletion result with status

**Anonymization (recommended):**
- Removes all PII (email, name, phone, addresses)
- Keeps analytics data for business intelligence
- Sets `is_anonymized=True` flag
- Irreversible operation

**Hard deletion:**
- Removes customer record from database
- Removes all addresses and notes
- Cannot be undone

**Example:**
```python
# Anonymization (GDPR-compliant, keeps analytics)
result = gdpr_service.delete_customer_data(
    db, "tenant_123", 42, anonymize=True
)

print(result)
# {
#     "success": True,
#     "method": "anonymized",
#     "customer_id": 42,
#     "deleted_at": "2025-11-26T10:30:00"
# }

# Hard deletion (complete removal)
result = gdpr_service.delete_customer_data(
    db, "tenant_123", 42, anonymize=False
)
```

#### `update_consent(db, tenant_id, customer_id, consent_type, consented, metadata) -> bool`

Updates customer consent for a specific type.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `consent_type` (str): Type of consent ("marketing", "analytics", "cookies")
- `consented` (bool): Consent status
- `metadata` (dict, optional): Additional data (IP, user agent, etc.)

**Returns:**
- `bool`: True if updated successfully

**Example:**
```python
# Update marketing consent
gdpr_service.update_consent(
    db,
    "tenant_123",
    42,
    consent_type="marketing",
    consented=True,
    metadata={
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
    }
)

# Revoke analytics consent
gdpr_service.update_consent(
    db,
    "tenant_123",
    42,
    consent_type="analytics",
    consented=False,
)
```

#### `has_consent(db, tenant_id, customer_id, consent_type) -> bool`

Checks if customer has given consent for a specific type.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `consent_type` (str): Type of consent

**Returns:**
- `bool`: True if consent is given

**Example:**
```python
if gdpr_service.has_consent(db, "tenant_123", 42, "marketing"):
    send_marketing_email(customer)
else:
    print("No marketing consent")
```

#### `get_consent_history(db, tenant_id, customer_id) -> Dict`

Retrieves complete consent history for a customer.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID

**Returns:**
- `Dict`: Consent history with timestamps

**Example:**
```python
consent_history = gdpr_service.get_consent_history(db, "tenant_123", 42)

print(consent_history)
# {
#     "marketing": {
#         "consented": True,
#         "date": "2025-01-15T10:30:00",
#         "ip_address": "192.168.1.1"
#     },
#     "analytics": {
#         "consented": False,
#         "date": "2025-01-15T10:30:00"
#     }
# }
```

---

### AI Service

The `AIService` class provides AI-powered customer analytics.

#### Initialization

```python
from linkbay_customers import AIService

ai_service = AIService(
    customer_model=Customer,
    ai_client=None,  # Optional: LinkBay-AI client for production ML
)
```

#### `update_customer_segment(db, customer_id) -> Optional[str]`

Automatically updates customer segment based on behavior.

**Segments:**
- `new`: First order within 30 days
- `active`: Regular purchases (orders in last 90 days)
- `high_value`: Total spent > $1000 and active
- `at_risk`: Was active but no orders in 90-180 days
- `dormant`: No orders in 180-365 days
- `churned`: No orders in 365+ days

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `customer_id` (int): Customer ID

**Returns:**
- `str | None`: New segment or None if customer not found

**Example:**
```python
segment = ai_service.update_customer_segment(db, 42)
print(f"Customer segment: {segment}")  # "high_value"

# Batch update all customers
from sqlalchemy import select

customers = db.execute(select(Customer)).scalars().all()
for customer in customers:
    ai_service.update_customer_segment(db, customer.id)
```

#### `calculate_churn_risk(db, customer_id) -> Optional[float]`

Calculates churn risk score for a customer.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `customer_id` (int): Customer ID

**Returns:**
- `float | None`: Churn risk score (0.0-1.0) or None

**Score interpretation:**
- 0.0 - 0.3: Low risk (active customer)
- 0.3 - 0.6: Medium risk (at risk)
- 0.6 - 1.0: High risk (likely to churn)

**Calculation factors:**
- Days since last order
- Order frequency
- Total orders
- Average order value trend

**Example:**
```python
risk = ai_service.calculate_churn_risk(db, 42)

if risk is not None:
    if risk > 0.7:
        print(f"HIGH RISK: {risk:.2f} - Send retention offer")
    elif risk > 0.4:
        print(f"MEDIUM RISK: {risk:.2f} - Monitor closely")
    else:
        print(f"LOW RISK: {risk:.2f} - Customer is healthy")
```

#### `predict_clv(db, customer_id, prediction_months) -> Optional[float]`

Predicts Customer Lifetime Value for future months.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `customer_id` (int): Customer ID
- `prediction_months` (int): Number of months to predict

**Returns:**
- `float | None`: Predicted revenue or None

**Calculation method:**
- Uses historical average order value
- Estimates order frequency
- Projects future value based on segment

**Example:**
```python
# Predict next 12 months
clv_12m = ai_service.predict_clv(db, 42, prediction_months=12)
print(f"Predicted 12-month CLV: ${clv_12m:.2f}")

# Predict next 6 months
clv_6m = ai_service.predict_clv(db, 42, prediction_months=6)

# Calculate customer acquisition cost efficiency
cac = 50  # Customer acquisition cost
if clv_12m and clv_12m > cac * 3:
    print("Customer is profitable (CLV > 3x CAC)")
```

#### `find_similar_customers(db, tenant_id, customer_id, limit) -> List[Customer]`

Finds similar customers using vector embeddings.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Reference customer ID
- `limit` (int): Maximum number of results

**Returns:**
- `List[Customer]`: List of similar customers

**Similarity factors:**
- Purchase behavior
- Average order value
- Order frequency
- Product preferences
- Customer segment

**Example:**
```python
similar = ai_service.find_similar_customers(
    db, "tenant_123", 42, limit=10
)

print(f"Customers similar to #{42}:")
for customer in similar:
    print(f"- #{customer.id}: {customer.email}")
    print(f"  Segment: {customer.segment}, AOV: ${customer.average_order_value}")
```

#### `generate_recommendations(db, tenant_id, customer_id, limit) -> List[Dict]`

Generates product recommendations based on similar customers.

**Parameters:**
- `db` (Session): SQLAlchemy database session
- `tenant_id` (str): Tenant identifier
- `customer_id` (int): Customer ID
- `limit` (int): Maximum number of recommendations

**Returns:**
- `List[Dict]`: List of recommended products

**Recommendation logic:**
- Finds similar customers
- Identifies products purchased by similar customers
- Excludes products already purchased by target customer
- Ranks by popularity among similar customers

**Example:**
```python
recommendations = ai_service.generate_recommendations(
    db, "tenant_123", 42, limit=5
)

print("Recommended products:")
for rec in recommendations:
    print(f"- {rec['product_name']}: {rec['score']:.2f} confidence")
```

---

### REST API Endpoints

The `create_customer_router()` function generates a complete REST API.

#### Customer Management

**`POST /customers`**

Creates a new customer.

**Request:**
```json
{
  "email": "mario.rossi@example.com",
  "first_name": "Mario",
  "last_name": "Rossi",
  "phone": "+393331234567",
  "birthday": "1990-05-15",
  "gender": "male",
  "preferences": {
    "language": "it",
    "newsletter_subscribed": true,
    "marketing_consent": true
  },
  "tags": ["vip", "early_adopter"]
}
```

**Response:** `201 Created`
```json
{
  "id": 42,
  "tenant_id": "tenant_123",
  "email": "mario.rossi@example.com",
  "first_name": "Mario",
  "last_name": "Rossi",
  "total_orders": 0,
  "total_spent": 0.0,
  "segment": null,
  "created_at": "2025-11-26T10:30:00"
}
```

**`GET /customers`**

Lists customers with filtering and pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `segment` (str): Filter by segment
- `min_total_spent` (float): Minimum total spent
- `max_total_spent` (float): Maximum total spent
- `tags` (str): Comma-separated tags
- `email_contains` (str): Email substring match
- `created_after` (datetime): Created after date
- `created_before` (datetime): Created before date

**Example:** `GET /customers?segment=high_value&min_total_spent=1000&page=1&page_size=50`

**Response:** `200 OK`
```json
{
  "items": [...],
  "total": 156,
  "page": 1,
  "page_size": 50,
  "total_pages": 4
}
```

**`GET /customers/search?q={query}`**

Searches customers by email, name, or phone.

**Query Parameters:**
- `q` (str): Search query

**Example:** `GET /customers/search?q=mario`

**Response:** `200 OK`
```json
[
  {
    "id": 42,
    "email": "mario.rossi@example.com",
    "first_name": "Mario",
    "last_name": "Rossi"
  }
]
```

**`GET /customers/{customer_id}`**

Retrieves customer details.

**Path Parameters:**
- `customer_id` (int): Customer ID

**Response:** `200 OK`
```json
{
  "id": 42,
  "email": "mario.rossi@example.com",
  "total_orders": 15,
  "total_spent": 1499.85,
  "segment": "high_value",
  "churn_risk_score": 0.12
}
```

**`PATCH /customers/{customer_id}`**

Updates customer information.

**Path Parameters:**
- `customer_id` (int): Customer ID

**Request:**
```json
{
  "phone": "+393339876543",
  "preferences": {
    "language": "en"
  }
}
```

**Response:** `200 OK`

**`DELETE /customers/{customer_id}`**

Deletes a customer (soft delete by default).

**Path Parameters:**
- `customer_id` (int): Customer ID

**Query Parameters:**
- `soft_delete` (bool): If true, soft delete; if false, hard delete (default: true)

**Response:** `204 No Content`

**`POST /customers/merge`**

Merges two customer records.

**Request:**
```json
{
  "source_customer_id": 123,
  "target_customer_id": 456,
  "merge_addresses": true,
  "merge_notes": true,
  "merge_tags": true,
  "merge_preferences": true
}
```

**Response:** `200 OK`

#### GDPR Endpoints

**`GET /customers/{customer_id}/export`**

Exports all customer data (GDPR Right to Access).

**Path Parameters:**
- `customer_id` (int): Customer ID

**Response:** `200 OK`
```json
{
  "export_date": "2025-11-26T10:30:00",
  "customer": {...},
  "addresses": [...],
  "notes": [...],
  "analytics": {...}
}
```

**`DELETE /customers/{customer_id}/gdpr`**

Deletes or anonymizes customer data (GDPR Right to Erasure).

**Path Parameters:**
- `customer_id` (int): Customer ID

**Query Parameters:**
- `anonymize` (bool): If true, anonymize; if false, hard delete (default: true)

**Response:** `200 OK`
```json
{
  "success": true,
  "method": "anonymized",
  "customer_id": 42,
  "deleted_at": "2025-11-26T10:30:00"
}
```

**`POST /customers/{customer_id}/consent/{consent_type}`**

Updates customer consent.

**Path Parameters:**
- `customer_id` (int): Customer ID
- `consent_type` (str): Consent type (marketing, analytics, cookies)

**Request:**
```json
{
  "consented": true,
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  }
}
```

**Response:** `200 OK`

**`GET /customers/{customer_id}/consent`**

Retrieves consent history.

**Path Parameters:**
- `customer_id` (int): Customer ID

**Response:** `200 OK`
```json
{
  "marketing": {
    "consented": true,
    "date": "2025-01-15T10:30:00"
  },
  "analytics": {
    "consented": false,
    "date": "2025-01-15T10:30:00"
  }
}
```

#### Address Endpoints

**`POST /customers/{customer_id}/addresses`**

Adds an address to a customer.

**Path Parameters:**
- `customer_id` (int): Customer ID

**Request:**
```json
{
  "type": "shipping",
  "address_line1": "Via Roma 123",
  "city": "Milano",
  "postal_code": "20100",
  "country": "IT",
  "is_default": true
}
```

**Response:** `201 Created`

**`GET /customers/{customer_id}/addresses`**

Lists all customer addresses.

**Path Parameters:**
- `customer_id` (int): Customer ID

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "type": "shipping",
    "address_line1": "Via Roma 123",
    "city": "Milano",
    "country": "IT",
    "is_default": true
  }
]
```

**`PATCH /customers/{customer_id}/addresses/{address_id}`**

Updates an address.

**`DELETE /customers/{customer_id}/addresses/{address_id}`**

Deletes an address.

#### Note Endpoints

**`POST /customers/{customer_id}/notes`**

Adds a note to a customer.

**Request:**
```json
{
  "note": "Customer requested expedited shipping"
}
```

**Response:** `201 Created`

**`GET /customers/{customer_id}/notes`**

Lists all customer notes.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "note": "Customer requested expedited shipping",
    "created_by": "user_456",
    "created_at": "2025-11-26T10:30:00"
  }
]
```

#### AI Endpoints

**`POST /customers/{customer_id}/segment`**

Updates customer segment.

**Response:** `200 OK`
```json
{
  "segment": "high_value"
}
```

**`GET /customers/{customer_id}/churn-risk`**

Calculates churn risk.

**Response:** `200 OK`
```json
{
  "churn_risk_score": 0.23,
  "risk_level": "low"
}
```

**`GET /customers/{customer_id}/clv?months=12`**

Predicts Customer Lifetime Value.

**Query Parameters:**
- `months` (int): Prediction period (default: 12)

**Response:** `200 OK`
```json
{
  "predicted_clv": 1249.99,
  "prediction_months": 12
}
```

**`GET /customers/{customer_id}/similar?limit=10`**

Finds similar customers.

**Query Parameters:**
- `limit` (int): Maximum results (default: 10)

**Response:** `200 OK`
```json
[
  {
    "id": 87,
    "email": "similar@example.com",
    "segment": "high_value",
    "similarity_score": 0.92
  }
]
```

**`GET /customers/{customer_id}/recommendations?limit=5`**

Generates product recommendations.

**Query Parameters:**
- `limit` (int): Maximum recommendations (default: 5)

**Response:** `200 OK`
```json
[
  {
    "product_id": 123,
    "product_name": "Premium Subscription",
    "score": 0.87,
    "reason": "Popular among similar customers"
  }
]
```

---

## Data Models

### CustomerMixin

Base mixin for Customer model. Extend this to create your custom Customer model.

**Fields:**

**Primary Key:**
- `id` (int): Auto-incrementing primary key

**Multi-Tenant:**
- `tenant_id` (str): Tenant identifier (indexed)

**Personal Information:**
- `email` (str): Email address (indexed, unique per tenant)
- `first_name` (str, optional): First name
- `last_name` (str, optional): Last name
- `phone` (str, optional): Phone number
- `birthday` (date, optional): Date of birth
- `gender` (str, optional): Gender

**Preferences:**
- `preferences` (JSON): Customer preferences (language, newsletter, etc.)
- `tags` (JSON array): Customer tags for segmentation

**Analytics:**
- `total_orders` (int): Total number of orders (default: 0)
- `total_spent` (float): Total amount spent (default: 0.0)
- `average_order_value` (float): Average order value (default: 0.0)
- `last_order_at` (datetime, optional): Last order timestamp
- `first_order_at` (datetime, optional): First order timestamp

**AI Analytics:**
- `customer_lifetime_value` (float, optional): Predicted CLV
- `churn_risk_score` (float, optional): Churn risk (0-1)
- `segment` (str, optional): Customer segment (indexed)
- `embedding` (JSON, optional): Vector embedding for similarity

**Metadata:**
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp
- `deleted_at` (datetime, optional): Soft deletion timestamp

**GDPR:**
- `is_anonymized` (bool): Anonymization flag (default: False)
- `consent_data` (JSON): Consent tracking data

**Indexes:**
- `(tenant_id, email)`: Unique constraint
- `(tenant_id, segment)`: Segment filtering
- `deleted_at`: Soft delete queries

**Usage:**
```python
from linkbay_customers.models import CustomerMixin
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String

Base = declarative_base()

class Customer(Base, CustomerMixin):
    __tablename__ = "customers"
    
    # Add custom fields
    company_name = Column(String(255))
    tax_id = Column(String(50))
    loyalty_points = Column(Integer, default=0)
```

### AddressMixin

Base mixin for Address model.

**Fields:**

- `id` (int): Auto-incrementing primary key
- `customer_id` (int): Foreign key to customer
- `tenant_id` (str): Tenant identifier
- `type` (str): Address type (billing, shipping, other)
- `address_line1` (str): Address line 1
- `address_line2` (str, optional): Address line 2
- `city` (str): City
- `state` (str, optional): State/province
- `postal_code` (str): Postal/ZIP code
- `country` (str): ISO 3166-1 alpha-2 country code
- `is_default` (bool): Default address flag (default: False)
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Usage:**
```python
from linkbay_customers.models import AddressMixin

class Address(Base, AddressMixin):
    __tablename__ = "customer_addresses"
```

### CustomerNoteMixin

Base mixin for CustomerNote model.

**Fields:**

- `id` (int): Auto-incrementing primary key
- `customer_id` (int): Foreign key to customer
- `tenant_id` (str): Tenant identifier
- `note` (str): Note content
- `created_by` (str): User who created the note
- `created_at` (datetime): Creation timestamp

**Usage:**
```python
from linkbay_customers.models import CustomerNoteMixin

class CustomerNote(Base, CustomerNoteMixin):
    __tablename__ = "customer_notes"
```

---

## Schemas

### CustomerCreate

Schema for creating a customer.

**Fields:**
- `email` (EmailStr): Email address (required)
- `first_name` (str, optional): First name
- `last_name` (str, optional): Last name
- `phone` (str, optional): Phone number
- `birthday` (date, optional): Date of birth
- `gender` (str, optional): Gender
- `preferences` (dict, optional): Customer preferences
- `tags` (list[str], optional): Customer tags

### CustomerUpdate

Schema for updating a customer (all fields optional).

### CustomerResponse

Schema for customer response data.

**Includes all CustomerCreate fields plus:**
- `id` (int): Customer ID
- `tenant_id` (str): Tenant identifier
- `total_orders` (int): Total orders
- `total_spent` (float): Total spent
- `average_order_value` (float): Average order value
- `last_order_at` (datetime, optional): Last order date
- `customer_lifetime_value` (float, optional): Predicted CLV
- `churn_risk_score` (float, optional): Churn risk
- `segment` (str, optional): Customer segment
- `created_at` (datetime): Creation date
- `updated_at` (datetime): Last update date
- `is_anonymized` (bool): Anonymization flag

### CustomerSearchFilters

Schema for filtering customer searches.

**Fields:**
- `segment` (str, optional): Filter by segment
- `min_total_spent` (float, optional): Minimum total spent
- `max_total_spent` (float, optional): Maximum total spent
- `tags` (list[str], optional): Filter by tags
- `email_contains` (str, optional): Email substring
- `created_after` (datetime, optional): Created after date
- `created_before` (datetime, optional): Created before date

### AddressCreate / AddressUpdate / AddressResponse

Schemas for address operations.

### CustomerNoteCreate / CustomerNoteResponse

Schemas for customer note operations.

### CustomerMergeRequest

Schema for merging customers.

**Fields:**
- `source_customer_id` (int): Customer to merge from (will be deleted)
- `target_customer_id` (int): Customer to merge into (will be kept)
- `merge_addresses` (bool): Merge addresses (default: True)
- `merge_notes` (bool): Merge notes (default: True)
- `merge_tags` (bool): Merge tags (default: True)
- `merge_preferences` (bool): Merge preferences (default: False)

---

## GDPR Compliance

LinkBay Customers provides comprehensive GDPR compliance features.

### Right to Access (Article 15)

Customers have the right to obtain a copy of their personal data.

**Implementation:**
```python
# Export all customer data
export = gdpr_service.export_customer_data(db, tenant_id, customer_id)

# Export includes:
# - Personal information
# - All addresses
# - All notes
# - Preferences and consent
# - Analytics metrics
# - Complete audit trail
```

**API Endpoint:**
```
GET /customers/{customer_id}/export
```

### Right to Erasure (Article 17)

Customers have the right to request deletion of their personal data.

**Implementation:**
```python
# Anonymization (recommended - keeps analytics)
result = gdpr_service.delete_customer_data(
    db, tenant_id, customer_id, anonymize=True
)

# Hard deletion (complete removal)
result = gdpr_service.delete_customer_data(
    db, tenant_id, customer_id, anonymize=False
)
```

**Anonymization process:**
1. Removes all PII (email, name, phone, birthday)
2. Deletes all addresses
3. Anonymizes notes (removes content)
4. Keeps analytics data (orders, revenue) for business intelligence
5. Sets `is_anonymized=True` flag
6. Cannot be reversed

**API Endpoint:**
```
DELETE /customers/{customer_id}/gdpr?anonymize=true
```

### Consent Management (Article 7)

Track and manage customer consent for various purposes.

**Consent types:**
- `marketing`: Marketing communications
- `analytics`: Analytics tracking
- `cookies`: Cookie usage

**Implementation:**
```python
# Update consent
gdpr_service.update_consent(
    db, tenant_id, customer_id,
    consent_type="marketing",
    consented=True,
    metadata={
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
    }
)

# Check consent before action
if gdpr_service.has_consent(db, tenant_id, customer_id, "marketing"):
    send_marketing_email(customer)

# Retrieve consent history
history = gdpr_service.get_consent_history(db, tenant_id, customer_id)
```

**API Endpoints:**
```
POST /customers/{customer_id}/consent/{consent_type}
GET /customers/{customer_id}/consent
```

### Data Portability (Article 20)

Data export is provided in machine-readable JSON format for easy transfer to other services.

### Audit Trail

All consent updates include:
- Timestamp
- IP address (optional)
- User agent (optional)
- Previous consent state

---

## AI-Powered Features

### Customer Segmentation

Automatic segmentation based on purchase behavior and engagement.

**Segments:**

**new**: New customer (first order within 30 days)
- Characteristics: 1-2 orders, recent signup
- Actions: Onboarding campaigns, first-time buyer incentives

**active**: Regular active customer
- Characteristics: Recent purchases (last 90 days), consistent engagement
- Actions: Loyalty programs, upsell opportunities

**high_value**: High-value customer
- Characteristics: Total spent > $1000, active status
- Actions: VIP treatment, exclusive offers, personal account manager

**at_risk**: Customer at risk of churning
- Characteristics: Was active but no orders in 90-180 days
- Actions: Win-back campaigns, special discounts, feedback surveys

**dormant**: Dormant customer
- Characteristics: No orders in 180-365 days
- Actions: Re-engagement campaigns, "we miss you" offers

**churned**: Churned customer
- Characteristics: No orders in 365+ days
- Actions: Final re-activation attempts, exit surveys

**Usage:**
```python
# Update single customer
segment = ai_service.update_customer_segment(db, customer_id)

# Batch update all customers
customers = db.query(Customer).all()
for customer in customers:
    ai_service.update_customer_segment(db, customer.id)

# Filter by segment
high_value = db.query(Customer).filter(
    Customer.tenant_id == "tenant_123",
    Customer.segment == "high_value"
).all()
```

### Churn Risk Scoring

Predicts probability of customer churn (0.0-1.0).

**Risk levels:**
- 0.0-0.3: Low risk (active, engaged customer)
- 0.3-0.6: Medium risk (showing warning signs)
- 0.6-1.0: High risk (likely to churn soon)

**Calculation factors:**
- Days since last order
- Order frequency decline
- Total number of orders
- Average order value trend
- Engagement metrics

**Usage:**
```python
risk = ai_service.calculate_churn_risk(db, customer_id)

if risk > 0.7:
    # High risk - immediate action needed
    trigger_retention_campaign(customer)
elif risk > 0.4:
    # Medium risk - monitor and engage
    schedule_followup(customer)
```

### Customer Lifetime Value (CLV) Prediction

Predicts future revenue from a customer.

**Prediction methodology:**
- Historical average order value
- Order frequency analysis
- Segment-based multipliers
- Trend analysis

**Usage:**
```python
# Predict next 12 months
clv = ai_service.predict_clv(db, customer_id, prediction_months=12)

# Calculate ROI
cac = 50  # Customer acquisition cost
if clv > cac * 3:
    print("Profitable customer (CLV > 3x CAC)")

# Segment customers by CLV
high_clv = [c for c in customers if c.customer_lifetime_value > 1000]
```

### Customer Similarity Search

Find similar customers based on behavior and preferences.

**Similarity factors:**
- Purchase patterns
- Average order value
- Order frequency
- Product preferences
- Customer segment
- Engagement level

**Usage:**
```python
# Find 10 most similar customers
similar = ai_service.find_similar_customers(
    db, "tenant_123", customer_id, limit=10
)

# Use for:
# - Targeted campaigns
# - Product recommendations
# - Behavior prediction
# - Cohort analysis
```

### Product Recommendations

Generate personalized product recommendations.

**Recommendation logic:**
1. Find similar customers
2. Identify products purchased by similar customers
3. Exclude already purchased products
4. Rank by popularity and relevance

**Usage:**
```python
recommendations = ai_service.generate_recommendations(
    db, "tenant_123", customer_id, limit=5
)

for rec in recommendations:
    print(f"{rec['product_name']}: {rec['score']:.0%} match")
```

---

## Advanced Usage

### Custom Models

Extend the mixin models with your own fields:

```python
from linkbay_customers.models import CustomerMixin
from sqlalchemy import Column, String, Integer, Boolean

class EnterpriseCustomer(Base, CustomerMixin):
    __tablename__ = "enterprise_customers"
    
    # B2B specific fields
    company_name = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    industry = Column(String(100))
    employee_count = Column(Integer)
    
    # Account management
    account_manager_id = Column(String(50))
    contract_value = Column(Float)
    contract_start_date = Column(Date)
    contract_end_date = Column(Date)
    
    # Enterprise features
    has_sso = Column(Boolean, default=False)
    has_api_access = Column(Boolean, default=False)
    api_rate_limit = Column(Integer, default=1000)
```

### Multi-Database Support

Use different databases for different tenants:

```python
def get_db_for_tenant(tenant_id: str):
    """Return appropriate database session based on tenant."""
    if tenant_id.startswith("enterprise"):
        return Session(enterprise_engine)
    else:
        return Session(standard_engine)

router = create_customer_router(
    get_db=get_db_for_tenant,
    get_tenant_id=get_tenant_id,
    customer_service=customer_service,
)
```

### Custom Segmentation Rules

Override segmentation logic:

```python
class CustomAIService(AIService):
    def update_customer_segment(self, db, customer_id):
        customer = db.query(self.customer_model).get(customer_id)
        
        # Custom B2B segmentation
        if customer.company_name:
            if customer.total_spent > 10000:
                segment = "enterprise"
            elif customer.total_spent > 1000:
                segment = "business"
            else:
                segment = "startup"
        else:
            # Use default B2C segmentation
            segment = super().update_customer_segment(db, customer_id)
        
        customer.segment = segment
        db.commit()
        return segment
```

### Webhook Integration

Trigger webhooks on customer events:

```python
from linkbay_webhooks import WebhookService

webhook_service = WebhookService()

def create_customer_with_webhook(db, tenant_id, data):
    # Create customer
    customer = customer_service.create_customer(db, tenant_id, data)
    
    # Trigger webhook
    webhook_service.trigger(
        tenant_id=tenant_id,
        event="customer.created",
        data={"customer_id": customer.id, "email": customer.email}
    )
    
    return customer
```

### Batch Operations

Process customers in batches:

```python
from sqlalchemy import select

# Update all customer segments
def update_all_segments(db, tenant_id):
    query = select(Customer).where(Customer.tenant_id == tenant_id)
    customers = db.execute(query).scalars().all()
    
    updated = 0
    for customer in customers:
        ai_service.update_customer_segment(db, customer.id)
        updated += 1
        
        if updated % 100 == 0:
            print(f"Updated {updated} customers...")
            db.commit()
    
    db.commit()
    print(f"Total updated: {updated}")

# Calculate churn risk for at-risk segment
def calculate_churn_for_at_risk(db, tenant_id):
    at_risk = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.segment == "at_risk"
    ).all()
    
    for customer in at_risk:
        risk = ai_service.calculate_churn_risk(db, customer.id)
        customer.churn_risk_score = risk
    
    db.commit()
```

### Export to External Systems

Export customer data to CRM or marketing tools:

```python
def export_to_mailchimp(db, tenant_id, segment=None):
    """Export customers to Mailchimp."""
    from mailchimp3 import MailChimp
    
    filters = CustomerSearchFilters(segment=segment) if segment else None
    customers, _ = customer_service.list_customers(
        db, tenant_id, filters, page=1, page_size=1000
    )
    
    client = MailChimp(mc_api='your-api-key')
    
    for customer in customers:
        if gdpr_service.has_consent(db, tenant_id, customer.id, "marketing"):
            client.lists.members.create('list_id', {
                'email_address': customer.email,
                'status': 'subscribed',
                'merge_fields': {
                    'FNAME': customer.first_name,
                    'LNAME': customer.last_name,
                },
                'tags': customer.tags,
            })
```

---

## Testing

```bash
# Install development dependencies
pip install linkbay-customers[dev]

# Run tests
pytest tests/

# Run with coverage
pytest --cov=linkbay_customers tests/

# Run specific test file
pytest tests/test_service.py

# Run with verbose output
pytest -v tests/
```

**Test structure:**
```
tests/
├── test_models.py       # Model tests
├── test_service.py      # Service layer tests
├── test_gdpr.py         # GDPR compliance tests
├── test_ai.py           # AI feature tests
├── test_router.py       # API endpoint tests
└── conftest.py          # Shared fixtures
```

---

## Dependencies

**Required:**
- `sqlalchemy>=2.0.0` - Database ORM
- `fastapi>=0.110.0` - Web framework
- `pydantic>=2.0.0` - Data validation
- `linkbay-core>=0.1.0` - Core utilities
- `linkbay-multitenant>=0.2.0` - Multi-tenant support

**Optional (AI features):**
- `pgvector>=0.2.0` - Vector similarity search
- `numpy>=1.24.0` - Numerical operations
- `scikit-learn>=1.3.0` - Machine learning utilities

**Optional (Production AI):**
- `linkbay-ai>=0.1.0` - Production ML models

**Development:**
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `black>=23.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking
- `ruff>=0.1.0` - Linting

---

## License

MIT License - Copyright (c) 2025 Alessio Quagliara (quagliara.alessio@gmail.com)

See [LICENSE](LICENSE) for full details.

---

## Support

- Issues: https://github.com/AlessioQuagliara/linkbay_customers/issues
- Email: quagliara.alessio@gmail.com

Contribuisci, apri una issue o raccontaci come stai usando la libreria 🧡
