"""
AI-powered features for customer analytics and segmentation.

This module provides AI capabilities like:
- Customer embeddings for semantic similarity
- Customer Lifetime Value (CLV) prediction
- Churn risk scoring
- Product recommendations based on similar customers
- Automatic customer segmentation

Note: This module is designed to integrate with LinkBay-AI for ML predictions.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import CustomerMixin


class AIService:
    """
    AI service for customer analytics and predictions.
    
    This service provides AI-powered features that can integrate with
    external ML services (like LinkBay-AI) or use local heuristics.
    
    Example:
        from linkbay_customers.ai import AIService
        from your_app.models import Customer
        
        ai_service = AIService(customer_model=Customer)
        
        # Update customer segment based on behavior
        ai_service.update_customer_segment(db, customer_id)
        
        # Calculate churn risk
        churn_score = ai_service.calculate_churn_risk(db, customer_id)
        
        # Find similar customers
        similar = ai_service.find_similar_customers(db, tenant_id, customer_id)
    """
    
    def __init__(
        self,
        customer_model: Type[CustomerMixin],
        ai_client: Optional[Any] = None,
    ):
        """
        Initialize AI service.
        
        Args:
            customer_model: SQLAlchemy model class that uses CustomerMixin
            ai_client: Optional AI client (e.g., LinkBay-AI) for ML predictions
        """
        self.customer_model = customer_model
        self.ai_client = ai_client
    
    # ========================================================================
    # Customer Segmentation
    # ========================================================================
    
    def update_customer_segment(
        self,
        db: Session,
        customer_id: int,
    ) -> Optional[str]:
        """
        Automatically update customer segment based on behavior.
        
        Segments:
        - new: First order within 30 days
        - active: Regular purchases (orders in last 90 days)
        - high_value: Total spent > threshold and active
        - at_risk: Was active but no orders in 90-180 days
        - dormant: No orders in 180-365 days
        - churned: No orders in 365+ days
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            
        Returns:
            New segment or None if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer:
            return None
        
        now = datetime.utcnow()
        segment = "new"
        
        if customer.total_orders == 0:
            segment = "new"
        elif customer.last_order_at:
            days_since_order = (now - customer.last_order_at).days
            
            # High value: spent > $1000 and ordered in last 90 days
            if customer.total_spent > 1000 and days_since_order <= 90:
                segment = "high_value"
            # Active: ordered in last 90 days
            elif days_since_order <= 90:
                segment = "active"
            # At risk: was active but no orders in 90-180 days
            elif days_since_order <= 180:
                segment = "at_risk"
            # Dormant: no orders in 180-365 days
            elif days_since_order <= 365:
                segment = "dormant"
            # Churned: no orders in 365+ days
            else:
                segment = "churned"
        
        customer.segment = segment
        customer.updated_at = now
        db.commit()
        
        return segment
    
    def segment_all_customers(
        self,
        db: Session,
        tenant_id: str,
        batch_size: int = 100,
    ) -> Dict[str, int]:
        """
        Update segments for all customers in a tenant.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            batch_size: Number of customers to process at once
            
        Returns:
            Dictionary with segment counts
        """
        offset = 0
        segment_counts = {}
        
        while True:
            customers = db.query(self.customer_model).filter(
                self.customer_model.tenant_id == tenant_id,
                self.customer_model.deleted_at.is_(None),
            ).offset(offset).limit(batch_size).all()
            
            if not customers:
                break
            
            for customer in customers:
                segment = self.update_customer_segment(db, customer.id)
                if segment:
                    segment_counts[segment] = segment_counts.get(segment, 0) + 1
            
            offset += batch_size
        
        return segment_counts
    
    # ========================================================================
    # Churn Risk Prediction
    # ========================================================================
    
    def calculate_churn_risk(
        self,
        db: Session,
        customer_id: int,
    ) -> Optional[float]:
        """
        Calculate churn risk score (0-1, higher = more risk).
        
        This uses a simple heuristic model. For production, integrate
        with a proper ML model (e.g., LinkBay-AI).
        
        Factors:
        - Days since last order
        - Order frequency
        - Spending trend
        - Engagement (newsletter opens, website visits, etc.)
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            
        Returns:
            Churn risk score (0-1) or None if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer or customer.total_orders == 0:
            return None
        
        # If using external AI service
        if self.ai_client:
            # Call external AI service for prediction
            try:
                return self._predict_churn_with_ai(customer)
            except Exception:
                pass  # Fall back to heuristic
        
        # Simple heuristic model
        risk_score = 0.0
        
        if customer.last_order_at:
            days_since_order = (datetime.utcnow() - customer.last_order_at).days
            
            # Days since last order (0-0.5 points)
            if days_since_order > 365:
                risk_score += 0.5
            elif days_since_order > 180:
                risk_score += 0.4
            elif days_since_order > 90:
                risk_score += 0.3
            elif days_since_order > 60:
                risk_score += 0.2
            elif days_since_order > 30:
                risk_score += 0.1
        
        # Order frequency (0-0.3 points)
        if customer.first_order_at:
            days_as_customer = (datetime.utcnow() - customer.first_order_at).days
            if days_as_customer > 0:
                orders_per_month = (customer.total_orders / days_as_customer) * 30
                if orders_per_month < 0.5:  # Less than 1 order per 2 months
                    risk_score += 0.3
                elif orders_per_month < 1:  # Less than 1 order per month
                    risk_score += 0.2
                elif orders_per_month < 2:
                    risk_score += 0.1
        
        # Spending (0-0.2 points)
        if customer.average_order_value < 50:
            risk_score += 0.2
        elif customer.average_order_value < 100:
            risk_score += 0.1
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Update customer record
        customer.churn_risk_score = risk_score
        customer.updated_at = datetime.utcnow()
        db.commit()
        
        return risk_score
    
    def _predict_churn_with_ai(self, customer: Any) -> float:
        """
        Predict churn using external AI service.
        
        Args:
            customer: Customer instance
            
        Returns:
            Churn risk score (0-1)
        """
        # Example integration with LinkBay-AI
        # This would call an external ML model
        features = {
            "total_orders": customer.total_orders,
            "total_spent": customer.total_spent,
            "average_order_value": customer.average_order_value,
            "days_since_last_order": (
                (datetime.utcnow() - customer.last_order_at).days
                if customer.last_order_at else 999
            ),
            "days_as_customer": (
                (datetime.utcnow() - customer.first_order_at).days
                if customer.first_order_at else 0
            ),
        }
        
        # Call AI service (placeholder)
        # response = self.ai_client.predict("churn_risk", features)
        # return response["score"]
        
        raise NotImplementedError("AI client integration not configured")
    
    # ========================================================================
    # Customer Lifetime Value (CLV) Prediction
    # ========================================================================
    
    def predict_clv(
        self,
        db: Session,
        customer_id: int,
        prediction_months: int = 12,
    ) -> Optional[float]:
        """
        Predict Customer Lifetime Value for next N months.
        
        This uses a simple formula. For production, integrate with
        a proper ML model.
        
        Simple formula:
        CLV = (Average Order Value × Purchase Frequency) × Customer Lifespan
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            prediction_months: Months to predict forward
            
        Returns:
            Predicted CLV or None if customer not found
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer or customer.total_orders == 0:
            return None
        
        # If using external AI service
        if self.ai_client:
            try:
                return self._predict_clv_with_ai(customer, prediction_months)
            except Exception:
                pass  # Fall back to heuristic
        
        # Simple heuristic model
        if customer.first_order_at:
            days_as_customer = (datetime.utcnow() - customer.first_order_at).days
            if days_as_customer > 0:
                # Calculate purchase frequency (orders per month)
                orders_per_month = (customer.total_orders / days_as_customer) * 30
                
                # Predict CLV
                clv = customer.average_order_value * orders_per_month * prediction_months
                
                # Apply retention factor based on churn risk
                if customer.churn_risk_score:
                    retention_factor = 1 - (customer.churn_risk_score * 0.5)
                    clv *= retention_factor
                
                # Update customer record
                customer.customer_lifetime_value = clv
                customer.updated_at = datetime.utcnow()
                db.commit()
                
                return clv
        
        return None
    
    def _predict_clv_with_ai(self, customer: Any, months: int) -> float:
        """
        Predict CLV using external AI service.
        
        Args:
            customer: Customer instance
            months: Prediction period in months
            
        Returns:
            Predicted CLV
        """
        # Example integration with LinkBay-AI
        raise NotImplementedError("AI client integration not configured")
    
    # ========================================================================
    # Customer Embeddings and Similarity
    # ========================================================================
    
    def generate_customer_embedding(
        self,
        db: Session,
        customer_id: int,
    ) -> Optional[List[float]]:
        """
        Generate embedding vector for customer.
        
        Embeddings capture customer characteristics and can be used for:
        - Finding similar customers
        - Customer clustering
        - Personalized recommendations
        
        This requires an embedding model (e.g., from LinkBay-AI).
        
        Args:
            db: SQLAlchemy database session
            customer_id: Customer ID
            
        Returns:
            Embedding vector or None
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id
        ).first()
        
        if not customer:
            return None
        
        if not self.ai_client:
            # Can't generate embeddings without AI client
            return None
        
        # Generate embedding from customer features
        # This would use an embedding model
        features = {
            "total_orders": customer.total_orders,
            "total_spent": customer.total_spent,
            "average_order_value": customer.average_order_value,
            "segment": customer.segment,
            "tags": customer.tags or [],
            "preferences": customer.preferences or {},
        }
        
        # Call AI service to generate embedding (placeholder)
        # embedding = self.ai_client.embed("customer", features)
        # customer.embedding = embedding
        # db.commit()
        # return embedding
        
        raise NotImplementedError("AI client integration not configured")
    
    def find_similar_customers(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        limit: int = 10,
        use_embeddings: bool = False,
    ) -> List[Any]:
        """
        Find customers similar to the given customer.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID to find similar customers for
            limit: Maximum number of similar customers to return
            use_embeddings: Use vector similarity (requires pgvector)
            
        Returns:
            List of similar customer instances
        """
        customer = db.query(self.customer_model).filter(
            self.customer_model.id == customer_id,
            self.customer_model.tenant_id == tenant_id,
        ).first()
        
        if not customer:
            return []
        
        # If using embeddings and pgvector
        if use_embeddings and customer.embedding:
            # Use vector similarity search
            # This requires pgvector extension
            # query = db.query(self.customer_model).filter(
            #     self.customer_model.tenant_id == tenant_id,
            #     self.customer_model.id != customer_id,
            #     self.customer_model.deleted_at.is_(None),
            # ).order_by(
            #     self.customer_model.embedding.cosine_distance(customer.embedding)
            # ).limit(limit)
            # return query.all()
            raise NotImplementedError("Vector similarity requires pgvector")
        
        # Fallback: Rule-based similarity
        # Find customers with similar characteristics
        similar = db.query(self.customer_model).filter(
            self.customer_model.tenant_id == tenant_id,
            self.customer_model.id != customer_id,
            self.customer_model.deleted_at.is_(None),
            self.customer_model.segment == customer.segment,
        )
        
        # Similar spending range (±30%)
        if customer.total_spent > 0:
            min_spent = customer.total_spent * 0.7
            max_spent = customer.total_spent * 1.3
            similar = similar.filter(
                self.customer_model.total_spent.between(min_spent, max_spent)
            )
        
        # Similar order frequency (±30%)
        if customer.total_orders > 0:
            min_orders = int(customer.total_orders * 0.7)
            max_orders = int(customer.total_orders * 1.3)
            similar = similar.filter(
                self.customer_model.total_orders.between(min_orders, max_orders)
            )
        
        return similar.limit(limit).all()
    
    def recommend_products_for_customer(
        self,
        db: Session,
        tenant_id: str,
        customer_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Recommend products based on similar customers.
        
        This is a placeholder that shows how you would integrate with
        an order/product service to generate recommendations.
        
        Args:
            db: SQLAlchemy database session
            tenant_id: Tenant identifier
            customer_id: Customer ID
            limit: Maximum number of products to recommend
            
        Returns:
            List of product recommendations
        """
        # Find similar customers
        similar_customers = self.find_similar_customers(
            db, tenant_id, customer_id, limit=20
        )
        
        if not similar_customers:
            return []
        
        # In a real implementation, you would:
        # 1. Get orders from similar customers
        # 2. Find most popular products
        # 3. Exclude products already purchased by this customer
        # 4. Return ranked product recommendations
        
        # Placeholder return
        similar_customer_ids = [c.id for c in similar_customers]
        
        return [
            {
                "customer_id": customer_id,
                "similar_customer_ids": similar_customer_ids,
                "message": "Integrate with order service to get product recommendations",
            }
        ]
