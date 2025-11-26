"""
Dynamic SQLAlchemy models for LinkBay Customers.

These models are designed to be completely dynamic - they don't depend on 
specific table structures. Users can extend or customize them as needed.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_mixin
from sqlalchemy.ext.declarative import declared_attr


class CustomerSegment(str, Enum):
    """Customer segment types."""
    NEW = "new"
    ACTIVE = "active"
    HIGH_VALUE = "high_value"
    AT_RISK = "at_risk"
    DORMANT = "dormant"
    CHURNED = "churned"


class AddressType(str, Enum):
    """Address types."""
    BILLING = "billing"
    SHIPPING = "shipping"
    OTHER = "other"


class GenderType(str, Enum):
    """Gender types."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


@declarative_mixin
class CustomerMixin:
    """
    Mixin for Customer model. Use this to create your own Customer model.
    
    Example:
        from linkbay_customers.models import CustomerMixin
        from your_app.database import Base
        
        class Customer(Base, CustomerMixin):
            __tablename__ = "customers"
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        return "customers"
    
    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Multi-tenant support
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Basic Information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Preferences (stored as JSON for flexibility)
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    # Example preferences structure:
    # {
    #     "language": "en",
    #     "newsletter_subscribed": true,
    #     "marketing_consent": true,
    #     "analytics_consent": true,
    #     "cookies_consent": true,
    #     "timezone": "UTC"
    # }
    
    # Tags for segmentation (stored as JSON array)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    
    # Analytics Fields
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_order_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # AI-Powered Analytics
    customer_lifetime_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    churn_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1
    segment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # AI Embeddings (stored as JSON for compatibility, use pgvector if available)
    embedding: Mapped[Optional[List[float]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # GDPR
    is_anonymized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)
    # Example consent_data structure:
    # {
    #     "marketing": {"consented": true, "date": "2024-01-01T00:00:00Z"},
    #     "analytics": {"consented": false, "date": "2024-01-01T00:00:00Z"},
    #     "cookies": {"consented": true, "date": "2024-01-01T00:00:00Z"}
    # }
    
    @declared_attr
    def __table_args__(cls):
        return (
            Index("idx_customer_tenant_email", "tenant_id", "email"),
            Index("idx_customer_tenant_segment", "tenant_id", "segment"),
            Index("idx_customer_deleted", "deleted_at"),
            UniqueConstraint("tenant_id", "email", name="uq_customer_tenant_email"),
        )


@declarative_mixin
class AddressMixin:
    """
    Mixin for Address model. Use this to create your own Address model.
    
    Example:
        from linkbay_customers.models import AddressMixin
        from your_app.database import Base
        
        class Address(Base, AddressMixin):
            __tablename__ = "customer_addresses"
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        return "customer_addresses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Address Type
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # billing, shipping, other
    
    # Address Fields
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    
    # Metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    @declared_attr
    def __table_args__(cls):
        return (
            Index("idx_address_customer", "customer_id"),
            Index("idx_address_customer_type", "customer_id", "type"),
        )


@declarative_mixin
class CustomerNoteMixin:
    """
    Mixin for CustomerNote model. Use this to create your own CustomerNote model.
    
    Example:
        from linkbay_customers.models import CustomerNoteMixin
        from your_app.database import Base
        
        class CustomerNote(Base, CustomerNoteMixin):
            __tablename__ = "customer_notes"
    """
    
    @declared_attr
    def __tablename__(cls) -> str:
        return "customer_notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Note Content
    note: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # User ID or email
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __table_args__(cls):
        return (Index("idx_note_customer", "customer_id"),)


# Provide default implementations for convenience
# Users can use these or create their own using the mixins

try:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
    
    class Customer(Base, CustomerMixin):
        """Default Customer model implementation."""
        pass
    
    class Address(Base, AddressMixin):
        """Default Address model implementation."""
        pass
    
    class CustomerNote(Base, CustomerNoteMixin):
        """Default CustomerNote model implementation."""
        pass

except ImportError:
    # If Base is not available, users must provide their own
    Customer = None
    Address = None
    CustomerNote = None
