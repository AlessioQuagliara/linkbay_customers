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

# Crea le tabelle
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

# Inizializza servizi
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
    return "tenant_123"  # Da JWT token, header, ecc.

# Crea router
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

```python
from linkbay_customers.schemas import CustomerCreate

customer_data = CustomerCreate(
    email="mario.rossi@example.com",
    first_name="Mario",
    last_name="Rossi",
    phone="+393331234567",
    preferences={
        "language": "it",
        "newsletter_subscribed": True,
        "marketing_consent": True,
    },
    tags=["vip", "early_adopter"],
)

customer = customer_service.create_customer(db, "tenant_123", customer_data)
```

### Cercare e filtrare clienti

```python
from linkbay_customers.schemas import CustomerSearchFilters

filters = CustomerSearchFilters(
    segment="high_value",
    min_total_spent=1000,
    tags=["vip"],
)

customers, total = customer_service.list_customers(
    db, "tenant_123", filters, page=1, page_size=50
)
```

### Exportare dati (GDPR)

```python
# Export completo dei dati cliente
export_data = gdpr_service.export_customer_data(db, "tenant_123", customer_id)

# Anonimizzazione (GDPR Right to Erasure)
result = gdpr_service.delete_customer_data(
    db, "tenant_123", customer_id, anonymize=True
)
```

### AI Analytics

```python
# Segmentazione automatica
segment = ai_service.update_customer_segment(db, customer_id)
# Ritorna: "new", "active", "high_value", "at_risk", "dormant", "churned"

# Predizione churn risk
churn_score = ai_service.calculate_churn_risk(db, customer_id)
# Ritorna: 0.0-1.0 (più alto = maggior rischio)

# Predizione Customer Lifetime Value
clv = ai_service.predict_clv(db, customer_id, prediction_months=12)
# Ritorna: ricavo previsto per i prossimi 12 mesi

# Trova clienti simili
similar = ai_service.find_similar_customers(db, "tenant_123", customer_id, limit=10)
```

### Merge di clienti duplicati

```python
from linkbay_customers.schemas import CustomerMergeRequest

merge_request = CustomerMergeRequest(
    source_customer_id=123,  # Sarà cancellato
    target_customer_id=456,  # Sarà mantenuto
    merge_addresses=True,
    merge_notes=True,
    merge_tags=True,
)

customer_service.merge_customers(db, "tenant_123", merge_request)
```

## API Endpoints disponibili

### Gestione Clienti
- `POST /customers` - Crea cliente
- `GET /customers` - Lista clienti (paginata, filtrata)
- `GET /customers/search?q=query` - Cerca clienti
- `GET /customers/{id}` - Dettagli cliente
- `PATCH /customers/{id}` - Aggiorna cliente
- `DELETE /customers/{id}` - Elimina cliente

### GDPR
- `GET /customers/{id}/export` - Export dati completo
- `POST /customers/{id}/consent/{type}` - Aggiorna consenso
- `GET /customers/{id}/consent` - Stato consensi

### Indirizzi
- `POST /customers/{id}/addresses` - Aggiungi indirizzo
- `GET /customers/{id}/addresses` - Lista indirizzi

### Note
- `POST /customers/{id}/notes` - Aggiungi nota
- `GET /customers/{id}/notes` - Lista note

### Funzionalità Avanzate
- `POST /customers/merge` - Merge clienti duplicati
- `POST /customers/{id}/segment` - Aggiorna segmento
- `POST /customers/{id}/churn-risk` - Calcola churn risk
- `POST /customers/{id}/clv` - Predici CLV
- `GET /customers/{id}/similar` - Trova simili
- `GET /customers/{id}/recommendations` - Raccomandazioni

## Modelli e Campi

### Customer

**Info Base:** `email`, `first_name`, `last_name`, `phone`, `birthday`, `gender`  
**Preferenze (JSON):** `language`, `newsletter_subscribed`, `marketing_consent`, `analytics_consent`  
**Analytics:** `total_orders`, `total_spent`, `average_order_value`, `last_order_at`, `first_order_at`  
**AI:** `customer_lifetime_value`, `churn_risk_score`, `segment`, `embedding`  
**GDPR:** `consent_data`, `is_anonymized`, `deleted_at`  

### Address

`type` (billing/shipping), `address_line1`, `address_line2`, `city`, `state`, `postal_code`, `country`, `is_default`

### CustomerNote

`note`, `created_by`, `created_at`

## Conformità GDPR

### Right to Access
```python
export = gdpr_service.export_customer_data(db, tenant_id, customer_id)
# Ritorna JSON completo con tutti i dati
```

### Right to Erasure
```python
# Anonimizzazione (consigliato)
result = gdpr_service.delete_customer_data(db, tenant_id, customer_id, anonymize=True)
# Rimuove PII, mantiene analytics

# Cancellazione hard (rimuove tutto)
result = gdpr_service.delete_customer_data(db, tenant_id, customer_id, anonymize=False)
```

### Tracking Consensi
```python
# Aggiorna consenso
gdpr_service.update_consent(db, tenant_id, customer_id, "marketing", True)

# Verifica consenso
has_consent = gdpr_service.has_consent(db, tenant_id, customer_id, "marketing")
```

## Testing

```bash
# Installa dipendenze dev
pip install linkbay-customers[dev]

# Esegui test
pytest tests/

# Coverage
pytest --cov=linkbay_customers tests/
```

## Personalizzazione

### Modelli Personalizzati

```python
from linkbay_customers.models import CustomerMixin

class CustomCustomer(Base, CustomerMixin):
    __tablename__ = "my_customers"
    
    # Aggiungi campi personalizzati
    company_name = Column(String(255))
    tax_id = Column(String(50))
    loyalty_points = Column(Integer, default=0)

# Usa con i servizi
customer_service = CustomerService(customer_model=CustomCustomer)
```

### Integrazione con LinkBay-AI

```python
from linkbay_ai import AIClient

ai_client = AIClient(api_key="your-api-key")
ai_service = AIService(customer_model=Customer, ai_client=ai_client)

# Ora usa modelli ML production per predizioni
```

## Dipendenze

**Richieste:**
- `sqlalchemy>=2.0.0`
- `fastapi>=0.110.0`
- `pydantic>=2.0.0`
- `linkbay-core>=0.1.0`
- `linkbay-multitenant>=0.2.0`

**Opzionali:**
- `pgvector>=0.2.0` (similarità vettoriale)
- `numpy>=1.24.0` (operazioni AI)

## Licenza

MIT License - vedi [LICENSE](LICENSE)

## Supporto

- GitHub: [LinkBay-Customers](https://github.com/alessioquagliara/LinkBay-Customers)
- Email: quagliara.alessio@gmail.com

## Package Correlati

- **linkbay-core**: Utilità core per l'ecosistema LinkBay
- **linkbay-multitenant**: Supporto architettura multi-tenant
- **linkbay-ai**: Integrazione servizi AI e ML


## Roadmap consigliata


## Licenza

MIT. Puoi usarla e modificarla liberamente, assicurandoti di valutarne i rischi nel tuo contesto.

## Supporto

- Issues: https://github.com/AlessioQuagliara/linkbay_cusomers/issues
- Email: quagliara.alessio@gmail.com

Contribuisci, apri una issue o raccontaci come stai usando la libreria 🧡
