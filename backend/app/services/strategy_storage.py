"""
F1 Strategy Platform v5.0 - Strategy Storage & Persistence
Save, retrieve, and manage user strategy results.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.auth.models import Base, User


@dataclass
class StrategyResult:
    """Represents a saved strategy result."""
    id: str
    user_id: int
    circuit: str
    strategy_type: str
    total_time: float
    total_time_formatted: str
    pit_laps: List[int]
    tires_used: List[str]
    explanation: str
    weather: str
    created_at: str
    name: str = ""
    tags: List[str] = None
    notes: str = ""
    comparison_baseline: bool = False
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['tags'] = data.get('tags') or []
        return data


class SavedStrategy(Base):
    """Database model for saved strategies."""
    __tablename__ = "saved_strategies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Strategy details
    name = Column(String(200), nullable=True)
    circuit = Column(String(50), nullable=False)
    strategy_type = Column(String(20), nullable=False)
    total_time = Column(Float, nullable=False)
    total_time_formatted = Column(String(20), nullable=False)
    pit_laps = Column(JSON, default=list)
    tires_used = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    weather = Column(String(20), default="dry")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # Comparison
    is_baseline = Column(String, default="false")  # For strategy comparison
    comparison_group = Column(String(50), nullable=True)
    
    # Full result JSON for reconstruction
    full_result = Column(JSON, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="saved_strategies")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name or f"{self.circuit} - {self.strategy_type}",
            "circuit": self.circuit,
            "strategy_type": self.strategy_type,
            "total_time": self.total_time,
            "total_time_formatted": self.total_time_formatted,
            "pit_laps": self.pit_laps or [],
            "tires_used": self.tires_used or [],
            "explanation": self.explanation,
            "weather": self.weather,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tags": self.tags or [],
            "notes": self.notes,
            "is_baseline": self.is_baseline == "true"
        }


# Add relationship to User model
User.saved_strategies = relationship("SavedStrategy", back_populates="user", cascade="all, delete-orphan")


class StrategyStorageService:
    """
    Service for managing saved strategies.
    Provides CRUD operations and comparison features.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def save_strategy(
        self,
        user_id: int,
        result: Dict[str, Any],
        name: str = None,
        tags: List[str] = None,
        notes: str = None
    ) -> SavedStrategy:
        """
        Save a strategy result.
        
        Args:
            user_id: User ID
            result: Strategy result dict
            name: Optional custom name
            tags: Optional tags
            notes: Optional notes
        
        Returns:
            SavedStrategy object
        """
        strategy = SavedStrategy(
            user_id=user_id,
            name=name or f"{result.get('circuit', 'Unknown')} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            circuit=result.get('circuit', ''),
            strategy_type=result.get('best_strategy', result.get('strategy_type', 'unknown')),
            total_time=result.get('total_time', 0),
            total_time_formatted=result.get('total_time_formatted', ''),
            pit_laps=result.get('pit_laps', []),
            tires_used=result.get('tires_used', []),
            explanation=result.get('explanation', ''),
            weather=result.get('weather', 'dry'),
            tags=tags or [],
            notes=notes,
            full_result=result  # Store complete result
        )
        
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        
        return strategy
    
    def get_user_strategies(
        self,
        user_id: int,
        circuit: str = None,
        strategy_type: str = None,
        tags: List[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get saved strategies for a user.
        
        Args:
            user_id: User ID
            circuit: Optional circuit filter
            strategy_type: Optional strategy type filter
            tags: Optional tags filter
            limit: Maximum results
        
        Returns:
            List of strategy dicts
        """
        query = self.db.query(SavedStrategy).filter(
            SavedStrategy.user_id == user_id
        )
        
        if circuit:
            query = query.filter(SavedStrategy.circuit == circuit)
        
        if strategy_type:
            query = query.filter(SavedStrategy.strategy_type == strategy_type)
        
        strategies = query.order_by(SavedStrategy.created_at.desc()).limit(limit).all()
        
        result = []
        for s in strategies:
            strategy_dict = s.to_dict()
            
            # Check tags filter
            if tags:
                strategy_tags = set(s.tags or [])
                if not any(tag in strategy_tags for tag in tags):
                    continue
            
            result.append(strategy_dict)
        
        return result
    
    def get_strategy(self, strategy_id: str, user_id: int) -> Optional[Dict]:
        """Get a specific strategy by ID."""
        strategy = self.db.query(SavedStrategy).filter(
            SavedStrategy.id == strategy_id,
            SavedStrategy.user_id == user_id
        ).first()
        
        if strategy:
            result = strategy.to_dict()
            result['full_result'] = strategy.full_result
            return result
        
        return None
    
    def update_strategy(
        self,
        strategy_id: str,
        user_id: int,
        name: str = None,
        tags: List[str] = None,
        notes: str = None
    ) -> Optional[Dict]:
        """Update strategy metadata."""
        strategy = self.db.query(SavedStrategy).filter(
            SavedStrategy.id == strategy_id,
            SavedStrategy.user_id == user_id
        ).first()
        
        if not strategy:
            return None
        
        if name is not None:
            strategy.name = name
        if tags is not None:
            strategy.tags = tags
        if notes is not None:
            strategy.notes = notes
        
        self.db.commit()
        return strategy.to_dict()
    
    def delete_strategy(self, strategy_id: str, user_id: int) -> bool:
        """Delete a strategy."""
        strategy = self.db.query(SavedStrategy).filter(
            SavedStrategy.id == strategy_id,
            SavedStrategy.user_id == user_id
        ).first()
        
        if not strategy:
            return False
        
        self.db.delete(strategy)
        self.db.commit()
        return True
    
    def compare_strategies(self, strategy_ids: List[str], user_id: int) -> Dict:
        """
        Compare multiple strategies.
        
        Args:
            strategy_ids: List of strategy IDs to compare
            user_id: User ID
        
        Returns:
            Comparison results
        """
        strategies = []
        
        for sid in strategy_ids:
            strategy = self.db.query(SavedStrategy).filter(
                SavedStrategy.id == sid,
                SavedStrategy.user_id == user_id
            ).first()
            
            if strategy:
                strategies.append(strategy)
        
        if len(strategies) < 2:
            return {"error": "Need at least 2 strategies to compare"}
        
        # Build comparison
        comparison = {
            "strategies": [s.to_dict() for s in strategies],
            "summary": {}
        }
        
        # Find fastest
        fastest = min(strategies, key=lambda s: s.total_time)
        comparison["summary"]["fastest"] = {
            "id": fastest.id,
            "name": fastest.name,
            "time": fastest.total_time_formatted
        }
        
        # Find most aggressive (most pit stops)
        most_pits = max(strategies, key=lambda s: len(s.pit_laps or []))
        comparison["summary"]["most_aggressive"] = {
            "id": most_pits.id,
            "name": most_pits.name,
            "pit_stops": len(most_pits.pit_laps or [])
        }
        
        # Time differences
        base_time = strategies[0].total_time
        for s in strategies:
            s.comparison_data = {
                "time_diff_seconds": s.total_time - base_time,
                "time_diff_percentage": ((s.total_time - base_time) / base_time * 100) if base_time > 0 else 0
            }
        
        return comparison
    
    def get_strategy_stats(self, user_id: int) -> Dict:
        """Get statistics about user's strategies."""
        strategies = self.db.query(SavedStrategy).filter(
            SavedStrategy.user_id == user_id
        ).all()
        
        if not strategies:
            return {
                "total_strategies": 0,
                "circuits_used": [],
                "most_common_strategy": None
            }
        
        circuits = {}
        strategy_types = {}
        
        for s in strategies:
            circuits[s.circuit] = circuits.get(s.circuit, 0) + 1
            strategy_types[s.strategy_type] = strategy_types.get(s.strategy_type, 0) + 1
        
        return {
            "total_strategies": len(strategies),
            "circuits_used": list(circuits.keys()),
            "circuit_counts": circuits,
            "most_common_strategy": max(strategy_types, key=strategy_types.get),
            "strategy_type_counts": strategy_types,
            "first_strategy_date": min(s.created_at for s in strategies).isoformat(),
            "last_strategy_date": max(s.created_at for s in strategies).isoformat()
        }
    
    def export_strategy(self, strategy_id: str, user_id: int, format: str = "json") -> Optional[Dict]:
        """
        Export a strategy in various formats.
        
        Args:
            strategy_id: Strategy ID
            user_id: User ID
            format: Export format (json, csv, pdf)
        
        Returns:
            Export data dict
        """
        strategy = self.db.query(SavedStrategy).filter(
            SavedStrategy.id == strategy_id,
            SavedStrategy.user_id == user_id
        ).first()
        
        if not strategy:
            return None
        
        base_data = {
            "id": strategy.id,
            "name": strategy.name,
            "circuit": strategy.circuit,
            "strategy_type": strategy.strategy_type,
            "total_time": strategy.total_time,
            "pit_laps": strategy.pit_laps,
            "tires_used": strategy.tires_used,
            "explanation": strategy.explanation,
            "weather": strategy.weather,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
            "notes": strategy.notes
        }
        
        if format == "json":
            return {
                "format": "json",
                "filename": f"strategy_{strategy.circuit}_{strategy.id[:8]}.json",
                "data": base_data
            }
        
        elif format == "csv":
            # CSV format for spreadsheet import
            csv_data = [
                ["Property", "Value"],
                ["Circuit", strategy.circuit],
                ["Strategy", strategy.strategy_type],
                ["Total Time", strategy.total_time_formatted],
                ["Pit Laps", ", ".join(map(str, strategy.pit_laps or []))],
                ["Tires", ", ".join(strategy.tires_used or [])],
                ["Weather", strategy.weather],
                ["Explanation", strategy.explanation]
            ]
            
            return {
                "format": "csv",
                "filename": f"strategy_{strategy.circuit}_{strategy.id[:8]}.csv",
                "data": csv_data
            }
        
        elif format == "pdf":
            # Return data for PDF generation (frontend would handle actual PDF creation)
            return {
                "format": "pdf",
                "filename": f"strategy_{strategy.circuit}_{strategy.id[:8]}.pdf",
                "template": "strategy_report",
                "data": base_data
            }
        
        return None
    
    def generate_share_link(self, strategy_id: str, user_id: int, 
                          expiry_hours: int = 24) -> Optional[str]:
        """
        Generate a shareable link for a strategy.
        
        Args:
            strategy_id: Strategy ID
            user_id: User ID
            expiry_hours: Link expiry time
        
        Returns:
            Shareable URL or None
        """
        strategy = self.db.query(SavedStrategy).filter(
            SavedStrategy.id == strategy_id,
            SavedStrategy.user_id == user_id
        ).first()
        
        if not strategy:
            return None
        
        # Generate token (in production, store in Redis/database)
        import secrets
        
        token = secrets.token_urlsafe(32)
        
        # Create share URL
        share_url = f"/shared/strategy/{strategy_id}?token={token}"
        
        return share_url


if __name__ == "__main__":
    print("Strategy Storage Service")
    print("=" * 60)
    print("This module provides:")
    print("  ✓ Save strategy results")
    print("  ✓ Retrieve user strategies")
    print("  ✓ Compare strategies")
    print("  ✓ Export (JSON, CSV, PDF)")
    print("  ✓ Shareable links")
    print("  ✓ Strategy statistics")
    print("\nReady for integration with FastAPI endpoints.")
