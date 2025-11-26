"""
FastAPI router for customer management endpoints.

This module provides a complete REST API for customer management with
multi-tenant support, GDPR compliance, and AI-powered analytics.
"""

from typing import Optional, List, Callable
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerWithAddresses,
    CustomerListResponse,
    CustomerSearchFilters,
    CustomerDataExport,
    CustomerDeleteRequest,
    CustomerDeleteResponse,
    CustomerMergeRequest,
    CustomerMergeResponse,
    AddressCreate,
    AddressUpdate,
    AddressResponse,
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerSegmentUpdate,
    CustomerAnalytics,
)
from .service import CustomerService
from .gdpr import GDPRService
from .ai import AIService


def create_customer_router(
    get_db: Callable,
    get_tenant_id: Callable,
    customer_service: CustomerService,
    gdpr_service: Optional[GDPRService] = None,
    ai_service: Optional[AIService] = None,
    prefix: str = "/customers",
    tags: Optional[List[str]] = None,
) -> APIRouter:
    """
    Create a FastAPI router for customer management.
    
    This factory function creates a router that's completely dynamic and
    doesn't depend on specific models or database configuration.
    
    Args:
        get_db: Dependency function that returns a database session
        get_tenant_id: Dependency function that returns current tenant ID
        customer_service: Configured CustomerService instance
        gdpr_service: Optional GDPRService instance for GDPR endpoints
        ai_service: Optional AIService instance for AI endpoints
        prefix: URL prefix for routes (default: "/customers")
        tags: OpenAPI tags for the router
        
    Returns:
        Configured FastAPI router
        
    Example:
        from fastapi import FastAPI, Depends
        from sqlalchemy.orm import Session
        from linkbay_customers import create_customer_router, CustomerService
        from your_app.database import get_db
        from your_app.auth import get_tenant_id
        from your_app.models import Customer, Address, CustomerNote
        
        app = FastAPI()
        
        # Configure service
        customer_service = CustomerService(
            customer_model=Customer,
            address_model=Address,
            note_model=CustomerNote,
        )
        
        # Create router
        router = create_customer_router(
            get_db=get_db,
            get_tenant_id=get_tenant_id,
            customer_service=customer_service,
        )
        
        app.include_router(router)
    """
    
    router = APIRouter(prefix=prefix, tags=tags or ["customers"])
    
    # ========================================================================
    # Customer CRUD Endpoints
    # ========================================================================
    
    @router.post(
        "",
        response_model=CustomerResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a new customer",
    )
    async def create_customer(
        data: CustomerCreate,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Create a new customer in the system."""
        # Check if customer already exists
        existing = customer_service.get_customer_by_email(db, tenant_id, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with email {data.email} already exists",
            )
        
        customer = customer_service.create_customer(db, tenant_id, data)
        return customer
    
    @router.get(
        "",
        response_model=CustomerListResponse,
        summary="List customers with pagination and filters",
    )
    async def list_customers(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Items per page"),
        email: Optional[str] = Query(None, description="Filter by email (partial match)"),
        first_name: Optional[str] = Query(None, description="Filter by first name"),
        last_name: Optional[str] = Query(None, description="Filter by last name"),
        segment: Optional[str] = Query(None, description="Filter by segment"),
        min_total_spent: Optional[float] = Query(None, description="Minimum total spent"),
        max_total_spent: Optional[float] = Query(None, description="Maximum total spent"),
        include_deleted: bool = Query(False, description="Include deleted customers"),
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """
        List customers with pagination and optional filters.
        
        Supports filtering by:
        - Email, name, segment
        - Spending range
        - Order count
        - Date ranges
        """
        filters = CustomerSearchFilters(
            email=email,
            first_name=first_name,
            last_name=last_name,
            segment=segment,
            min_total_spent=min_total_spent,
            max_total_spent=max_total_spent,
            include_deleted=include_deleted,
        )
        
        customers, total = customer_service.list_customers(
            db, tenant_id, filters, page, page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return CustomerListResponse(
            items=customers,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    @router.get(
        "/search",
        response_model=CustomerListResponse,
        summary="Search customers by text query",
    )
    async def search_customers(
        q: str = Query(..., min_length=1, description="Search query"),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100),
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Search customers across email, name, and phone fields."""
        customers, total = customer_service.search_customers(
            db, tenant_id, q, page, page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return CustomerListResponse(
            items=customers,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    @router.get(
        "/{customer_id}",
        response_model=CustomerResponse,
        summary="Get customer by ID",
    )
    async def get_customer(
        customer_id: int,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Get a single customer by ID."""
        customer = customer_service.get_customer(db, tenant_id, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        return customer
    
    @router.patch(
        "/{customer_id}",
        response_model=CustomerResponse,
        summary="Update customer",
    )
    async def update_customer(
        customer_id: int,
        data: CustomerUpdate,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Update customer information."""
        customer = customer_service.update_customer(db, tenant_id, customer_id, data)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        return customer
    
    @router.delete(
        "/{customer_id}",
        response_model=CustomerDeleteResponse,
        summary="Delete customer (soft delete by default)",
    )
    async def delete_customer(
        customer_id: int,
        request: Optional[CustomerDeleteRequest] = None,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """
        Delete customer data (GDPR compliant).
        
        By default, anonymizes the customer data instead of hard delete
        to preserve referential integrity with orders.
        """
        if not gdpr_service:
            # Fallback to simple soft delete
            success = customer_service.delete_customer(
                db, tenant_id, customer_id, soft_delete=True
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return CustomerDeleteResponse(
                customer_id=customer_id,
                anonymized=False,
                deleted_at=datetime.utcnow(),
                message="Customer soft deleted",
            )
        
        anonymize = request.anonymize if request else True
        result = gdpr_service.delete_customer_data(
            db, tenant_id, customer_id, anonymize=anonymize
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        
        return result
    
    # ========================================================================
    # GDPR Endpoints
    # ========================================================================
    
    if gdpr_service:
        @router.get(
            "/{customer_id}/export",
            response_model=dict,
            summary="Export customer data (GDPR)",
        )
        async def export_customer_data(
            customer_id: int,
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """
            Export all customer data in machine-readable format.
            
            This endpoint implements GDPR "Right to Access" - customers
            can request all their personal data.
            """
            export = gdpr_service.export_customer_data(db, tenant_id, customer_id)
            if not export:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return export
        
        @router.post(
            "/{customer_id}/consent/{consent_type}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Update customer consent",
        )
        async def update_consent(
            customer_id: int,
            consent_type: str,
            consented: bool = Query(..., description="Whether consent is given"),
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """
            Update customer consent for a specific purpose.
            
            Consent types: marketing, analytics, cookies
            """
            success = gdpr_service.update_consent(
                db, tenant_id, customer_id, consent_type, consented
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
        
        @router.get(
            "/{customer_id}/consent",
            response_model=dict,
            summary="Get customer consent status",
        )
        async def get_consent_status(
            customer_id: int,
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Get all consent records for a customer."""
            consent = gdpr_service.get_consent_status(db, tenant_id, customer_id)
            if consent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return consent
    
    # ========================================================================
    # Address Endpoints
    # ========================================================================
    
    @router.post(
        "/{customer_id}/addresses",
        response_model=AddressResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Add address to customer",
    )
    async def add_address(
        customer_id: int,
        data: AddressCreate,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Add a new address to customer."""
        address = customer_service.add_address(db, tenant_id, customer_id, data)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        return address
    
    @router.get(
        "/{customer_id}/addresses",
        response_model=List[AddressResponse],
        summary="Get customer addresses",
    )
    async def get_addresses(
        customer_id: int,
        address_type: Optional[str] = Query(None, description="Filter by type"),
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Get all addresses for a customer."""
        addresses = customer_service.get_customer_addresses(
            db, tenant_id, customer_id, address_type
        )
        return addresses
    
    # ========================================================================
    # Note Endpoints
    # ========================================================================
    
    @router.post(
        "/{customer_id}/notes",
        response_model=CustomerNoteResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Add note to customer",
    )
    async def add_note(
        customer_id: int,
        data: CustomerNoteCreate,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Add a note to customer."""
        note = customer_service.add_note(db, tenant_id, customer_id, data)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer {customer_id} not found",
            )
        return note
    
    @router.get(
        "/{customer_id}/notes",
        response_model=List[CustomerNoteResponse],
        summary="Get customer notes",
    )
    async def get_notes(
        customer_id: int,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """Get all notes for a customer."""
        notes = customer_service.get_customer_notes(db, tenant_id, customer_id)
        return notes
    
    # ========================================================================
    # Merge Endpoint
    # ========================================================================
    
    @router.post(
        "/merge",
        response_model=CustomerMergeResponse,
        summary="Merge duplicate customers",
    )
    async def merge_customers(
        request: CustomerMergeRequest,
        db: Session = Depends(get_db),
        tenant_id: str = Depends(get_tenant_id),
    ):
        """
        Merge two customers into one.
        
        This combines data from the source customer into the target customer
        and then deletes the source.
        """
        success = customer_service.merge_customers(db, tenant_id, request)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both customers not found",
            )
        
        return CustomerMergeResponse(
            target_customer_id=request.target_customer_id,
            source_customer_id=request.source_customer_id,
            merged_at=datetime.utcnow(),
            message="Customers merged successfully",
        )
    
    # ========================================================================
    # AI-Powered Analytics Endpoints
    # ========================================================================
    
    if ai_service:
        @router.post(
            "/{customer_id}/segment",
            response_model=CustomerSegmentUpdate,
            summary="Update customer segment",
        )
        async def update_segment(
            customer_id: int,
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Automatically update customer segment based on behavior."""
            segment = ai_service.update_customer_segment(db, customer_id)
            if not segment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return CustomerSegmentUpdate(segment=segment)
        
        @router.post(
            "/{customer_id}/churn-risk",
            response_model=dict,
            summary="Calculate churn risk score",
        )
        async def calculate_churn_risk(
            customer_id: int,
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Calculate churn risk score (0-1) for customer."""
            risk_score = ai_service.calculate_churn_risk(db, customer_id)
            if risk_score is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return {"customer_id": customer_id, "churn_risk_score": risk_score}
        
        @router.post(
            "/{customer_id}/clv",
            response_model=dict,
            summary="Predict customer lifetime value",
        )
        async def predict_clv(
            customer_id: int,
            months: int = Query(12, ge=1, le=60, description="Prediction months"),
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Predict customer lifetime value for next N months."""
            clv = ai_service.predict_clv(db, customer_id, months)
            if clv is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found",
                )
            return {
                "customer_id": customer_id,
                "predicted_clv": clv,
                "prediction_months": months,
            }
        
        @router.get(
            "/{customer_id}/similar",
            response_model=List[CustomerResponse],
            summary="Find similar customers",
        )
        async def find_similar_customers(
            customer_id: int,
            limit: int = Query(10, ge=1, le=50),
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Find customers similar to the given customer."""
            similar = ai_service.find_similar_customers(
                db, tenant_id, customer_id, limit
            )
            return similar
        
        @router.get(
            "/{customer_id}/recommendations",
            response_model=dict,
            summary="Get product recommendations",
        )
        async def get_recommendations(
            customer_id: int,
            limit: int = Query(10, ge=1, le=50),
            db: Session = Depends(get_db),
            tenant_id: str = Depends(get_tenant_id),
        ):
            """Get personalized product recommendations."""
            recommendations = ai_service.recommend_products_for_customer(
                db, tenant_id, customer_id, limit
            )
            return {"customer_id": customer_id, "recommendations": recommendations}
    
    return router


# Default router instance (requires configuration before use)
router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "linkbay-customers"}
