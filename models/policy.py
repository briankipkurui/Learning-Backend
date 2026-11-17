from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel


class PolicyTypeModel(BaseModel):
    """
    Policy Type Model
    
    Represents different types of policies (e.g., Privacy Policy, Terms of Service, Cookie Policy)
    """
    __tablename__ = "policy_types"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    policies = relationship("PolicyModel", back_populates="policy_type", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PolicyType(Id={self.Id}, name={self.name})>"


class PolicyModel(BaseModel):
    """
    Policy Model
    
    Represents a version of a policy document
    """
    __tablename__ = "policies"
    
    title = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    effective_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    policy_type_id = Column(UUID(as_uuid=True), ForeignKey("policy_types.Id", ondelete="CASCADE"), nullable=False, index=True)
    replaced_by_id = Column(UUID(as_uuid=True), ForeignKey("policies.Id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    policy_type = relationship("PolicyTypeModel", back_populates="policies")
    replaced_by = relationship("PolicyModel", remote_side="PolicyModel.Id", foreign_keys=[replaced_by_id])
    acknowledgements = relationship("PolicyAcknowledgementModel", back_populates="policy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Policy(Id={self.Id}, version={self.version}, type={self.policy_type_id})>"


class PolicyAcknowledgementModel(BaseModel):
    """
    Policy Acknowledgement Model
    
    Tracks when users acknowledge/accept policies
    """
    __tablename__ = "policy_acknowledgements"
    __table_args__ = (
        UniqueConstraint('user_id', 'policy_id', name='uq_user_policy_acknowledgement'),
    )
    
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.Id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    user_ip_address = Column(String(45), nullable=True)  # IPv6 max length is 45
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    policy = relationship("PolicyModel", back_populates="acknowledgements")
    user = relationship("UserModel", back_populates="policy_acknowledgements")
    
    def __repr__(self):
        return f"<PolicyAcknowledgement(Id={self.Id}, user_id={self.user_id}, policy_id={self.policy_id})>"
