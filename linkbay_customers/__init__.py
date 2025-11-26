"""
LinkBay Customers - Multi-tenant customer management system.

This package provides a complete customer management solution with:
- Multi-tenant architecture
- GDPR compliance (data export, deletion, consent tracking)
- AI-powered analytics (CLV prediction, churn risk, segmentation)
- Customer embeddings for semantic similarity
"""

__version__ = "0.1.0"

from .models import Customer, Address, CustomerNote
from .schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    CustomerNoteCreate,
    CustomerNoteResponse,
)
from .service import CustomerService
from .router import router as customers_router

__all__ = [
    # Models
    "Customer",
    "Address",
    "CustomerNote",
    # Schemas
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerListResponse",
    "AddressCreate",
    "AddressUpdate",
    "AddressResponse",
    "CustomerNoteCreate",
    "CustomerNoteResponse",
    # Service
    "CustomerService",
    # Router
    "customers_router",
]
