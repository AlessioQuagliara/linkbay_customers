"""
Example usage of LinkBay Customers package.

This file demonstrates how to set up and use the customer management system.
"""

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

from linkbay_customers.models import CustomerMixin, AddressMixin, CustomerNoteMixin
from linkbay_customers.service import CustomerService
from linkbay_customers.gdpr import GDPRService
from linkbay_customers.ai import AIService
from linkbay_customers.router import create_customer_router
from linkbay_customers.schemas import CustomerCreate

# ============================================================================
# Database Setup
# ============================================================================

DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"
engine = create_engine(DATABASE_URL)
Base = declarative_base()


# ============================================================================
# Define Models
# ============================================================================

class Customer(Base, CustomerMixin):
    """Customer model using CustomerMixin."""
    __tablename__ = "customers"


class Address(Base, AddressMixin):
    """Address model using AddressMixin."""
    __tablename__ = "customer_addresses"


class CustomerNote(Base, CustomerNoteMixin):
    """CustomerNote model using CustomerNoteMixin."""
    __tablename__ = "customer_notes"


# Create tables
Base.metadata.create_all(engine)


# ============================================================================
# Dependency Functions
# ============================================================================

def get_db():
    """Database session dependency."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


def get_tenant_id():
    """
    Get current tenant ID from request context.
    
    In production, extract this from:
    - JWT token claims
    - Request headers (X-Tenant-ID)
    - Subdomain
    - User session
    """
    # Example: return request.state.tenant_id
    return "tenant_123"


# ============================================================================
# Initialize Services
# ============================================================================

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

ai_service = AIService(
    customer_model=Customer,
    # ai_client=your_ai_client,  # Optional: LinkBay-AI integration
)


# ============================================================================
# Create FastAPI Application
# ============================================================================

app = FastAPI(
    title="LinkBay Customers Example",
    description="Customer management system with GDPR compliance and AI analytics",
    version="0.1.0",
)


# ============================================================================
# Include Customer Router
# ============================================================================

router = create_customer_router(
    get_db=get_db,
    get_tenant_id=get_tenant_id,
    customer_service=customer_service,
    gdpr_service=gdpr_service,
    ai_service=ai_service,
    prefix="/api/v1/customers",
    tags=["Customers"],
)

app.include_router(router)


# ============================================================================
# Additional Endpoints (Optional)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LinkBay Customers",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Example: Direct Service Usage (without router)
# ============================================================================

async def create_customer_example():
    """Example of using CustomerService directly."""
    db = next(get_db())
    tenant_id = "tenant_123"
    
    # Create customer
    customer_data = CustomerCreate(
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
        phone="+1234567890",
        preferences={
            "language": "en",
            "newsletter_subscribed": True,
            "marketing_consent": True,
        },
        tags=["vip", "new"],
    )
    
    customer = customer_service.create_customer(db, tenant_id, customer_data)
    print(f"Created customer: {customer.id}")
    
    # Update customer segment
    segment = ai_service.update_customer_segment(db, customer.id)
    print(f"Customer segment: {segment}")
    
    # Calculate churn risk
    churn_risk = ai_service.calculate_churn_risk(db, customer.id)
    print(f"Churn risk: {churn_risk}")
    
    # Export customer data (GDPR)
    export_data = gdpr_service.export_customer_data(db, tenant_id, customer.id)
    print(f"Exported data: {len(export_data)} bytes")
    
    db.close()


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "example:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
