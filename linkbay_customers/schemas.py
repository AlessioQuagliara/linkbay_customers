"""
Pydantic schemas for LinkBay Customers API.

These schemas handle request/response validation and serialization.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# Address Schemas
# ============================================================================

class AddressBase(BaseModel):
    """Base address schema."""
    type: str = Field(..., description="Address type: billing, shipping, other")
    address_line1: str = Field(..., max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(..., max_length=20)
    country: str = Field(..., max_length=2, description="ISO 3166-1 alpha-2 country code")
    is_default: bool = Field(default=False)


class AddressCreate(AddressBase):
    """Schema for creating an address."""
    pass


class AddressUpdate(BaseModel):
    """Schema for updating an address."""
    type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None


class AddressResponse(AddressBase):
    """Schema for address response."""
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Customer Preferences
# ============================================================================

class CustomerPreferences(BaseModel):
    """Customer preferences schema."""
    language: Optional[str] = Field(default="en", max_length=10)
    newsletter_subscribed: Optional[bool] = Field(default=False)
    marketing_consent: Optional[bool] = Field(default=False)
    analytics_consent: Optional[bool] = Field(default=False)
    cookies_consent: Optional[bool] = Field(default=False)
    timezone: Optional[str] = Field(default="UTC")


class ConsentRecord(BaseModel):
    """Single consent record."""
    consented: bool
    date: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentData(BaseModel):
    """Customer consent tracking."""
    marketing: Optional[ConsentRecord] = None
    analytics: Optional[ConsentRecord] = None
    cookies: Optional[ConsentRecord] = None


# ============================================================================
# Customer Schemas
# ============================================================================

class CustomerBase(BaseModel):
    """Base customer schema."""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    birthday: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=50)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    tenant_id: Optional[str] = None  # Will be set from context if not provided


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    birthday: Optional[date] = None
    gender: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    id: int
    tenant_id: str
    
    # Analytics
    total_orders: int
    total_spent: float
    average_order_value: float
    last_order_at: Optional[datetime] = None
    first_order_at: Optional[datetime] = None
    
    # AI Analytics
    customer_lifetime_value: Optional[float] = None
    churn_risk_score: Optional[float] = None
    segment: Optional[str] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    is_anonymized: bool
    
    model_config = ConfigDict(from_attributes=True)


class CustomerWithAddresses(CustomerResponse):
    """Customer response with addresses included."""
    addresses: List[AddressResponse] = Field(default_factory=list)


class CustomerListResponse(BaseModel):
    """Paginated customer list response."""
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Customer Note Schemas
# ============================================================================

class CustomerNoteCreate(BaseModel):
    """Schema for creating a customer note."""
    note: str = Field(..., description="Note content")
    created_by: Optional[str] = Field(None, description="User ID or email of note creator")


class CustomerNoteResponse(BaseModel):
    """Schema for customer note response."""
    id: int
    customer_id: int
    note: str
    created_by: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# GDPR Schemas
# ============================================================================

class CustomerDataExport(BaseModel):
    """Complete customer data export for GDPR compliance."""
    customer: CustomerResponse
    addresses: List[AddressResponse]
    notes: List[CustomerNoteResponse]
    consent_data: Optional[Dict[str, Any]] = None
    export_date: datetime
    export_format: str = "json"


class CustomerDeleteRequest(BaseModel):
    """Request to delete customer data (GDPR)."""
    reason: Optional[str] = Field(None, description="Reason for deletion")
    anonymize: bool = Field(
        default=True,
        description="If True, anonymize data instead of hard delete"
    )


class CustomerDeleteResponse(BaseModel):
    """Response after customer deletion."""
    customer_id: int
    anonymized: bool
    deleted_at: datetime
    message: str


# ============================================================================
# Search and Filter Schemas
# ============================================================================

class CustomerSearchFilters(BaseModel):
    """Filters for customer search."""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = None
    tags: Optional[List[str]] = None
    min_total_spent: Optional[float] = None
    max_total_spent: Optional[float] = None
    min_orders: Optional[int] = None
    max_orders: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    include_deleted: bool = False


# ============================================================================
# Analytics Schemas
# ============================================================================

class CustomerAnalytics(BaseModel):
    """Customer analytics data."""
    customer_id: int
    total_orders: int
    total_spent: float
    average_order_value: float
    customer_lifetime_value: Optional[float] = None
    churn_risk_score: Optional[float] = None
    segment: Optional[str] = None
    last_order_at: Optional[datetime] = None
    first_order_at: Optional[datetime] = None


class CustomerSegmentUpdate(BaseModel):
    """Update customer segment."""
    segment: str = Field(..., description="Customer segment: new, active, high_value, at_risk, dormant, churned")


class CustomerEmbeddingUpdate(BaseModel):
    """Update customer embedding."""
    embedding: List[float] = Field(..., description="Customer embedding vector")


# ============================================================================
# Merge Customers Schema
# ============================================================================

class CustomerMergeRequest(BaseModel):
    """Request to merge duplicate customers."""
    source_customer_id: int = Field(..., description="Customer to merge from (will be deleted)")
    target_customer_id: int = Field(..., description="Customer to merge into (will be kept)")
    merge_addresses: bool = Field(default=True, description="Merge addresses from source to target")
    merge_notes: bool = Field(default=True, description="Merge notes from source to target")
    merge_tags: bool = Field(default=True, description="Merge tags from source to target")


class CustomerMergeResponse(BaseModel):
    """Response after customer merge."""
    target_customer_id: int
    source_customer_id: int
    merged_at: datetime
    message: str
