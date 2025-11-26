"""
Customer Service - Business logic for customer management.

This service is completely dynamic and works with any SQLAlchemy session
and customer model that follows the CustomerMixin pattern.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, select, update, delete

from .models import CustomerMixin, AddressMixin, CustomerNoteMixin
from .schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerSearchFilters,
    AddressCreate,
    AddressUpdate,
    CustomerNoteCreate,
    CustomerMergeRequest,
)

# Type variable for generic Customer model
T = TypeVar('T', bound=CustomerMixin)


class CustomerService:
    """
    Dynamic customer service that works with any Customer model.
    
    This service doesn't depend on a specific Customer model - it works
    with any model that uses CustomerMixin.
    
    Example:
        from linkbay_customers.service import CustomerService
        from your_app.models import Customer, Address, CustomerNote
        from your_app.database import get_db
        
        service = CustomerService(
            customer_model=Customer,
            address_model=Address,
            note_model=CustomerNote
        )
        
        # Use with dependency injection in FastAPI
        customer = service.create_customer(db, tenant_id="tenant1", data=customer_data)
    """
    
    def __init__(
        self,
        customer_model: Type[T],
        address_model: Optional[Type] = None,
        note_model: Optional[Type] = None,
    ):
        """
        Initialize service with dynamic models.
        
        Args:
            customer_model: SQLAlchemy model class that uses CustomerMixin
            address_model: SQLAlchemy model class that uses AddressMixin (optional)
            note_model: SQLAlchemy model class that uses CustomerNoteMixin (optional)
        """
        self.customer_model = customer_model
        self.address_model = address_model
        self.note_model = note_model
    
    # ========================================================================
    # Customer CRUD Operations
    # ========================================================================
    
    def create_customer(
        self,
        db: Session,
        tenant_id: str,
        data: CustomerCreate,
    ) -> T:
        """
        Create a new customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            data: Customer creation data
            
        Returns:
            Created customer instance
        """
        customer_dict = data.model_dump(exclude_unset=True)
        customer_dict["tenant_id"] = tenant_id
        
        customer = self.customer_model(**customer_dict)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        return customer
    
    def get_customer(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        include_deleted: bool = False,
    ) -> Optional[T]:
        """
        Get customer by ID.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            include_deleted: Include soft-deleted customers
            
        Returns:
            Customer instance or None
        """
        query = db.query(self.customer_model).filter(
            and_(
                self.customer_model.id == customer_id,
                self.customer_model.tenant_id == tenant_id,
            )
        )
        
        if not include_deleted:
            query = query.filter(self.customer_model.deleted_at.is_(None))
        
        return query.first()
    
    def get_customer_by_email(
        self,
        db: Session,
        tenant_id: str,
        email: str,
        include_deleted: bool = False,
    ) -> Optional[T]:
        """
        Get customer by email.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            email: Customer email
            include_deleted: Include soft-deleted customers
            
        Returns:
            Customer instance or None
        """
        query = db.query(self.customer_model).filter(
            and_(
                self.customer_model.email == email,
                self.customer_model.tenant_id == tenant_id,
            )
        )
        
        if not include_deleted:
            query = query.filter(self.customer_model.deleted_at.is_(None))
        
        return query.first()
    
    def update_customer(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Optional[T]:
        """
        Update customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            data: Customer update data
            
        Returns:
            Updated customer instance or None
        """
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return None
        
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(customer, key, value)
        
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)
        
        return customer
    
    def delete_customer(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        soft_delete: bool = True,
    ) -> bool:
        """
        Delete customer (soft or hard delete).
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            soft_delete: Use soft delete (recommended)
            
        Returns:
            True if deleted, False if not found
        """
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return False
        
        if soft_delete:
            customer.deleted_at = datetime.utcnow()
            db.commit()
        else:
            db.delete(customer)
            db.commit()
        
        return True
    
    def list_customers(
        self,
        db: Session,
        tenant_id: str,
        filters: Optional[CustomerSearchFilters] = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> tuple[List[T], int]:
        """
        List customers with pagination and filters.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            filters: Search filters
            page: Page number (1-indexed)
            page_size: Items per page
            order_by: Field to order by
            order_desc: Order descending
            
        Returns:
            Tuple of (customers list, total count)
        """
        query = db.query(self.customer_model).filter(
            self.customer_model.tenant_id == tenant_id
        )
        
        # Apply filters
        if filters:
            if filters.email:
                query = query.filter(self.customer_model.email.ilike(f"%{filters.email}%"))
            
            if filters.first_name:
                query = query.filter(self.customer_model.first_name.ilike(f"%{filters.first_name}%"))
            
            if filters.last_name:
                query = query.filter(self.customer_model.last_name.ilike(f"%{filters.last_name}%"))
            
            if filters.phone:
                query = query.filter(self.customer_model.phone.ilike(f"%{filters.phone}%"))
            
            if filters.segment:
                query = query.filter(self.customer_model.segment == filters.segment)
            
            if filters.tags:
                # Search for any of the provided tags
                for tag in filters.tags:
                    query = query.filter(self.customer_model.tags.contains([tag]))
            
            if filters.min_total_spent is not None:
                query = query.filter(self.customer_model.total_spent >= filters.min_total_spent)
            
            if filters.max_total_spent is not None:
                query = query.filter(self.customer_model.total_spent <= filters.max_total_spent)
            
            if filters.min_orders is not None:
                query = query.filter(self.customer_model.total_orders >= filters.min_orders)
            
            if filters.max_orders is not None:
                query = query.filter(self.customer_model.total_orders <= filters.max_orders)
            
            if filters.created_after:
                query = query.filter(self.customer_model.created_at >= filters.created_after)
            
            if filters.created_before:
                query = query.filter(self.customer_model.created_at <= filters.created_before)
            
            if not filters.include_deleted:
                query = query.filter(self.customer_model.deleted_at.is_(None))
        else:
            query = query.filter(self.customer_model.deleted_at.is_(None))
        
        # Count total
        total = query.count()
        
        # Order and paginate
        order_column = getattr(self.customer_model, order_by, self.customer_model.created_at)
        if order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())
        
        offset = (page - 1) * page_size
        customers = query.offset(offset).limit(page_size).all()
        
        return customers, total
    
    def search_customers(
        self,
        db: Session,
        tenant_id: str,
        query_text: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[T], int]:
        """
        Full-text search across customer fields.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            query_text: Search query
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (customers list, total count)
        """
        search_pattern = f"%{query_text}%"
        
        query = db.query(self.customer_model).filter(
            and_(
                self.customer_model.tenant_id == tenant_id,
                self.customer_model.deleted_at.is_(None),
                or_(
                    self.customer_model.email.ilike(search_pattern),
                    self.customer_model.first_name.ilike(search_pattern),
                    self.customer_model.last_name.ilike(search_pattern),
                    self.customer_model.phone.ilike(search_pattern),
                ),
            )
        )
        
        total = query.count()
        offset = (page - 1) * page_size
        customers = query.offset(offset).limit(page_size).all()
        
        return customers, total
    
    # ========================================================================
    # Customer Analytics
    # ========================================================================
    
    def update_customer_analytics(
        self,
        db: Session,
        customer_id: int,
        total_orders: Optional[int] = None,
        total_spent: Optional[float] = None,
        last_order_at: Optional[datetime] = None,
    ) -> bool:
        """
        Update customer analytics (called from order service).
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            total_orders: Total number of orders
            total_spent: Total amount spent
            last_order_at: Last order timestamp
            
        Returns:
            True if updated, False if not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer:
            return False
        
        if total_orders is not None:
            customer.total_orders = total_orders
        
        if total_spent is not None:
            customer.total_spent = total_spent
            if customer.total_orders > 0:
                customer.average_order_value = total_spent / customer.total_orders
        
        if last_order_at is not None:
            customer.last_order_at = last_order_at
            if customer.first_order_at is None:
                customer.first_order_at = last_order_at
        
        customer.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    def update_customer_segment(
        self,
        db: Session,
        customer_id: int,
        segment: str,
    ) -> bool:
        """
        Update customer segment.
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            segment: New segment value
            
        Returns:
            True if updated, False if not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer:
            return False
        
        customer.segment = segment
        customer.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    # ========================================================================
    # Address Management
    # ========================================================================
    
    def add_address(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        data: AddressCreate,
    ) -> Optional[Any]:
        """
        Add address to customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            data: Address creation data
            
        Returns:
            Created address instance or None
        """
        if not self.address_model:
            raise NotImplementedError("Address model not configured")
        
        # Verify customer exists and belongs to tenant
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return None
        
        address_dict = data.model_dump()
        address_dict["customer_id"] = customer_id
        
        # If this is set as default, unset others
        if address_dict.get("is_default"):
            db.query(self.address_model).filter(
                and_(
                    self.address_model.customer_id == customer_id,
                    self.address_model.type == address_dict["type"],
                )
            ).update({"is_default": False})
        
        address = self.address_model(**address_dict)
        db.add(address)
        db.commit()
        db.refresh(address)
        
        return address
    
    def get_customer_addresses(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        address_type: Optional[str] = None,
    ) -> List[Any]:
        """
        Get all addresses for a customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            address_type: Filter by address type (optional)
            
        Returns:
            List of address instances
        """
        if not self.address_model:
            return []
        
        # Verify customer exists and belongs to tenant
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return []
        
        query = db.query(self.address_model).filter(
            self.address_model.customer_id == customer_id
        )
        
        if address_type:
            query = query.filter(self.address_model.type == address_type)
        
        return query.all()
    
    # ========================================================================
    # Customer Notes
    # ========================================================================
    
    def add_note(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        data: CustomerNoteCreate,
    ) -> Optional[Any]:
        """
        Add note to customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            data: Note creation data
            
        Returns:
            Created note instance or None
        """
        if not self.note_model:
            raise NotImplementedError("Note model not configured")
        
        # Verify customer exists and belongs to tenant
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return None
        
        note_dict = data.model_dump()
        note_dict["customer_id"] = customer_id
        
        note = self.note_model(**note_dict)
        db.add(note)
        db.commit()
        db.refresh(note)
        
        return note
    
    def get_customer_notes(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
    ) -> List[Any]:
        """
        Get all notes for a customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            
        Returns:
            List of note instances
        """
        if not self.note_model:
            return []
        
        # Verify customer exists and belongs to tenant
        customer = self.get_customer(db, tenant_id, customer_id)
        if not customer:
            return []
        
        return db.query(self.note_model).filter(
            self.note_model.customer_id == customer_id
        ).order_by(self.note_model.created_at.desc()).all()
    
    # ========================================================================
    # Merge Customers
    # ========================================================================
    
    def merge_customers(
        self,
        db: Session,
        tenant_id: str,
        request: CustomerMergeRequest,
    ) -> bool:
        """
        Merge duplicate customers.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            request: Merge request with source and target IDs
            
        Returns:
            True if merged successfully, False otherwise
        """
        source = self.get_customer(db, tenant_id, request.source_customer_id)
        target = self.get_customer(db, tenant_id, request.target_customer_id)
        
        if not source or not target:
            return False
        
        # Merge addresses
        if request.merge_addresses and self.address_model:
            addresses = self.get_customer_addresses(db, tenant_id, source.id)
            for address in addresses:
                address.customer_id = target.id
        
        # Merge notes
        if request.merge_notes and self.note_model:
            notes = self.get_customer_notes(db, tenant_id, source.id)
            for note in notes:
                note.customer_id = target.id
        
        # Merge tags
        if request.merge_tags:
            source_tags = set(source.tags or [])
            target_tags = set(target.tags or [])
            target.tags = list(source_tags | target_tags)
        
        # Merge analytics
        target.total_orders += source.total_orders
        target.total_spent += source.total_spent
        if target.total_orders > 0:
            target.average_order_value = target.total_spent / target.total_orders
        
        if source.first_order_at:
            if not target.first_order_at or source.first_order_at < target.first_order_at:
                target.first_order_at = source.first_order_at
        
        if source.last_order_at:
            if not target.last_order_at or source.last_order_at > target.last_order_at:
                target.last_order_at = source.last_order_at
        
        # Delete source customer
        self.delete_customer(db, tenant_id, source.id, soft_delete=True)
        
        db.commit()
        return True
