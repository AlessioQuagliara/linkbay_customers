"""
GDPR Compliance utilities for LinkBay Customers.

This module provides tools for GDPR compliance including data export,
data deletion/anonymization, and consent tracking.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from sqlalchemy.orm import Session

from .models import CustomerMixin, AddressMixin, CustomerNoteMixin
from .schemas import CustomerDataExport, CustomerDeleteResponse


class GDPRService:
    """
    GDPR compliance service for customer data management.
    
    This service handles:
    - Right to access (data export)
    - Right to erasure (data deletion/anonymization)
    - Consent tracking
    
    Example:
        from linkbay_customers.gdpr import GDPRService
        from your_app.models import Customer, Address, CustomerNote
        
        gdpr_service = GDPRService(
            customer_model=Customer,
            address_model=Address,
            note_model=CustomerNote
        )
        
        # Export customer data
        export = gdpr_service.export_customer_data(db, tenant_id, customer_id)
        
        # Delete/anonymize customer data
        result = gdpr_service.delete_customer_data(db, tenant_id, customer_id)
    """
    
    def __init__(
        self,
        customer_model: Type[CustomerMixin],
        address_model: Optional[Type[AddressMixin]] = None,
        note_model: Optional[Type[CustomerNoteMixin]] = None,
    ):
        """
        Initialize GDPR service with dynamic models.
        
        Args:
            customer_model: SQLAlchemy model class that uses CustomerMixin
            address_model: SQLAlchemy model class that uses AddressMixin (optional)
            note_model: SQLAlchemy model class that uses CustomerNoteMixin (optional)
        """
        self.customer_model = customer_model
        self.address_model = address_model
        self.note_model = note_model
    
    def export_customer_data(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Export all customer data (GDPR Right to Access).
        
        This exports all personal data stored about the customer in a
        machine-readable format (JSON).
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            
        Returns:
            Dictionary containing all customer data or None if not found
        """
        # Get customer
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id,
            self.customer_model.tenant_id == tenant_id,
        ).first()
        
        if not customer:
            return None
        
        # Export customer data
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "export_format": "json",
            "customer": {
                "id": customer.id,
                "email": customer.email,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone": customer.phone,
                "birthday": customer.birthday.isoformat() if customer.birthday else None,
                "gender": customer.gender,
                "preferences": customer.preferences,
                "tags": customer.tags,
                "total_orders": customer.total_orders,
                "total_spent": customer.total_spent,
                "average_order_value": customer.average_order_value,
                "last_order_at": customer.last_order_at.isoformat() if customer.last_order_at else None,
                "first_order_at": customer.first_order_at.isoformat() if customer.first_order_at else None,
                "customer_lifetime_value": customer.customer_lifetime_value,
                "churn_risk_score": customer.churn_risk_score,
                "segment": customer.segment,
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat(),
                "consent_data": customer.consent_data,
            },
            "addresses": [],
            "notes": [],
        }
        
        # Export addresses
        if self.address_model:
            addresses = db.query(self.address_model).filter(
                self.address_model.customer_id == customer_id
            ).all()
            
            export_data["addresses"] = [
                {
                    "id": addr.id,
                    "type": addr.type,
                    "address_line1": addr.address_line1,
                    "address_line2": addr.address_line2,
                    "city": addr.city,
                    "state": addr.state,
                    "postal_code": addr.postal_code,
                    "country": addr.country,
                    "is_default": addr.is_default,
                    "created_at": addr.created_at.isoformat(),
                    "updated_at": addr.updated_at.isoformat(),
                }
                for addr in addresses
            ]
        
        # Export notes
        if self.note_model:
            notes = db.query(self.note_model).filter(
                self.note_model.customer_id == customer_id
            ).all()
            
            export_data["notes"] = [
                {
                    "id": note.id,
                    "note": note.note,
                    "created_by": note.created_by,
                    "created_at": note.created_at.isoformat(),
                }
                for note in notes
            ]
        
        return export_data
    
    def delete_customer_data(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        anonymize: bool = True,
    ) -> Optional[CustomerDeleteResponse]:
        """
        Delete or anonymize customer data (GDPR Right to Erasure).
        
        By default, this anonymizes the customer data instead of deleting it
        to preserve referential integrity with orders and other data.
        
        Anonymization:
        - Replaces email with anonymized version
        - Clears all PII fields (name, phone, birthday, etc.)
        - Keeps analytics data (orders, spending) for business reporting
        - Marks customer as anonymized
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            anonymize: If True, anonymize instead of delete
            
        Returns:
            Delete response or None if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id,
            self.customer_model.tenant_id == tenant_id,
        ).first()
        
        if not customer:
            return None
        
        if anonymize:
            # Anonymize personal data
            customer.email = f"deleted-{customer.id}@anonymized.local"
            customer.first_name = None
            customer.last_name = None
            customer.phone = None
            customer.birthday = None
            customer.gender = None
            customer.preferences = {}
            customer.tags = []
            customer.embedding = None
            customer.consent_data = {}
            customer.is_anonymized = True
            customer.deleted_at = datetime.utcnow()
            
            # Delete addresses
            if self.address_model:
                db.query(self.address_model).filter(
                    self.address_model.customer_id == customer_id
                ).delete()
            
            # Keep notes but anonymize creator
            if self.note_model:
                db.query(self.note_model).filter(
                    self.note_model.customer_id == customer_id
                ).update({"created_by": "anonymized"})
            
            db.commit()
            
            return CustomerDeleteResponse(
                customer_id=customer_id,
                anonymized=True,
                deleted_at=customer.deleted_at,
                message="Customer data has been anonymized. Analytics data preserved for reporting.",
            )
        else:
            # Hard delete - remove all data
            if self.address_model:
                db.query(self.address_model).filter(
                    self.address_model.customer_id == customer_id
                ).delete()
            
            if self.note_model:
                db.query(self.note_model).filter(
                    self.note_model.customer_id == customer_id
                ).delete()
            
            db.delete(customer)
            db.commit()
            
            return CustomerDeleteResponse(
                customer_id=customer_id,
                anonymized=False,
                deleted_at=datetime.utcnow(),
                message="Customer data has been permanently deleted.",
            )
    
    def update_consent(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        consent_type: str,
        consented: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update customer consent for a specific purpose.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            consent_type: Type of consent (e.g., 'marketing', 'analytics', 'cookies')
            consented: Whether consent was given or revoked
            metadata: Optional metadata (e.g., IP address, user agent)
            
        Returns:
            True if updated, False if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id,
            self.customer_model.tenant_id == tenant_id,
        ).first()
        
        if not customer:
            return False
        
        if customer.consent_data is None:
            customer.consent_data = {}
        
        consent_record = {
            "consented": consented,
            "date": datetime.utcnow().isoformat(),
        }
        
        if metadata:
            consent_record.update(metadata)
        
        customer.consent_data[consent_type] = consent_record
        customer.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def get_consent_status(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Get all consent records for a customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            
        Returns:
            Dictionary of consent records or None if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id,
            self.customer_model.tenant_id == tenant_id,
        ).first()
        
        if not customer:
            return None
        
        return customer.consent_data or {}
    
    def has_consent(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        consent_type: str,
    ) -> bool:
        """
        Check if customer has given consent for a specific purpose.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            consent_type: Type of consent to check
            
        Returns:
            True if consented, False otherwise
        """
        consent_data = self.get_consent_status(db, tenant_id, customer_id)
        
        if not consent_data:
            return False
        
        consent_record = consent_data.get(consent_type)
        if not consent_record:
            return False
        
        return consent_record.get("consented", False)
