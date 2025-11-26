# LinkBay Customers v0.1.0

[![License](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)](https://fastapi.tiangolo.com)

**Multi-tenant customer management system for FastAPI with GDPR compliance and AI-powered analytics**

Sistema completo di gestione clienti per applicazioni FastAPI con architettura multi-tenant, conformità GDPR e analytics AI-powered.

## Prima di iniziare

**Questa libreria è ideale per:**

✅ Applicazioni SaaS multi-tenant che necessitano gestione clienti  
✅ E-commerce e CRM che richiedono conformità GDPR  
✅ Sistemi che vogliono analytics AI (segmentazione, churn prediction, CLV)  
✅ Progetti che necessitano flessibilità totale nei modelli database  

**Non usare se:**

❌ Hai bisogno di un CRM completo out-of-the-box (questa è una libreria di building blocks)  
❌ Non usi FastAPI o SQLAlchemy  
❌ Non hai bisogno di multi-tenancy  

## Caratteristiche principali

🏢 **Multi-Tenant** - Isolamento completo dei dati tra tenant  
🔒 **GDPR Compliant** - Export, cancellazione, tracciamento consensi  
🤖 **AI-Powered** - Segmentazione, churn risk, CLV prediction  
📊 **Customer Analytics** - Metriche complete su ordini e comportamento  
🎯 **Completamente Dinamico** - Usa i tuoi modelli SQLAlchemy  
🔧 **Altamente Personalizzabile** - Servizi modulari e router flessibili  

## Installazione

```bash
pip install linkbay-customers
```

Con supporto AI (embeddings, pgvector):
```bash
pip install linkbay-customers[ai]
```

Per sviluppo:
```bash
pip install linkbay-customers[dev]
```

## Come funziona (3 passi)

### 1. Definisci i tuoi modelli

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

### 2. Configura i servizi e il router

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

### 3. Avvia e usa l'API

```bash
uvicorn main:app --reload
```

Vai su `http://localhost:8000/docs` per la documentazione interattiva.

## Esempio completo di utilizzo

### Creare un cliente

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

- Issues: https://github.com/AlessioQuagliara/----/issues
- Email: quagliara.alessio@gmail.com

Contribuisci, apri una issue o raccontaci come stai usando la libreria 🧡
