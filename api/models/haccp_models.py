"""
HACCP Models - Food Safety and Compliance Management
All models scoped by enterprise_id for data isolation
"""

from sqlalchemy import Column, String, ForeignKey, Text, Boolean, Date, DateTime, Enum, DECIMAL, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from api.models.base import TimestampedModel, BaseModel


# ==================== ENUMS ====================

class Section(PyEnum):
    """Child care sections/groups"""
    BABIES = "BABIES"
    TODDLERS = "TODDLERS"
    PRESCHOOLERS = "PRESCHOOLERS"


class MealType(PyEnum):
    """Types of meals"""
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    SNACK = "SNACK"


class Checkpoint(PyEnum):
    """Temperature control checkpoints"""
    RECEPTION = "RECEPTION"
    HOLDING = "HOLDING"
    SERVICE = "SERVICE"
    STORAGE = "STORAGE"


class CleaningFrequency(PyEnum):
    """HACCP cleaning frequency"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class NonComplianceType(PyEnum):
    """Non-compliance incident types"""
    PRODUCT = "PRODUCT"
    TEMPERATURE = "TEMPERATURE"
    HYGIENE = "HYGIENE"
    OTHER = "OTHER"


class NonComplianceStatus(PyEnum):
    """Non-compliance processing status"""
    OPEN = "OPEN"
    CORRECTED = "CORRECTED"
    CLOSED = "CLOSED"


class DocumentCategory(PyEnum):
    """Document categories"""
    TEMPERATURES = "TEMPERATURES"
    CLEANING = "CLEANING"
    TRAINING = "TRAINING"
    COMPLIANCE = "COMPLIANCE"
    OTHER = "OTHER"


# ==================== MODELS ====================

class Child(TimestampedModel):
    """
    Children enrolled in daycare with allergen tracking
    Scoped by enterprise_id
    """
    __tablename__ = "child"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    section = Column(Enum(Section), nullable=False)
    allergies = Column(Text, nullable=True, comment="Known allergies (comma-separated)")
    specific_diet = Column(Text, nullable=True, comment="Special diet requirements")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="children")

    def __repr__(self):
        return f"<Child(id='{self.id}', name='{self.first_name} {self.last_name}', section='{self.section.value}')>"


class Supplier(TimestampedModel):
    """
    Food suppliers with HACCP certification tracking
    Scoped by enterprise_id
    """
    __tablename__ = "supplier"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    name = Column(String(150), nullable=False)
    contact_name = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    address = Column(Text, nullable=True)
    haccp_certified = Column(Boolean, default=False, nullable=False, comment="HACCP compliant supplier")
    validation_date = Column(Date, nullable=True, comment="Last verification date")

    # Relationships
    enterprise = relationship("Enterprise", back_populates="suppliers")

    def __repr__(self):
        return f"<Supplier(id='{self.id}', name='{self.name}', haccp='{self.haccp_certified}')>"


class Product(TimestampedModel):
    """
    Food products with allergen and stock tracking
    Scoped by enterprise_id
    """
    __tablename__ = "product"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier.id"),
        nullable=True
    )

    name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=True, comment="Category (meat, dairy, vegetable, etc.)")
    allergens = Column(Text, nullable=True, comment="List of allergens (comma-separated)")
    stock_unit = Column(String(20), nullable=True, comment="Unit (kg, L, etc.)")
    current_stock = Column(DECIMAL(10, 2), nullable=True, comment="Quantity in stock")
    expiry_date = Column(Date, nullable=True, comment="Expiry date")

    # Relationships
    enterprise = relationship("Enterprise", back_populates="products")
    supplier = relationship("Supplier", backref="products")

    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', category='{self.category}')>"


class Batch(BaseModel):
    """
    Product batches with reception tracking
    Linked to product
    """
    __tablename__ = "batch"

    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product.id"),
        nullable=False
    )

    batch_code = Column(String(100), nullable=False, comment="Batch reference")
    reception_date = Column(Date, nullable=False)
    received_quantity = Column(DECIMAL(10, 2), nullable=False)
    reception_temperature = Column(DECIMAL(5, 2), nullable=True, comment="Temperature at reception (°C)")
    is_compliant = Column(Boolean, default=True, nullable=False, comment="Compliant at reception")
    observations = Column(Text, nullable=True)

    # Relationships
    product = relationship("Product", backref="batches")

    def __repr__(self):
        return f"<Batch(id='{self.id}', code='{self.batch_code}', compliant='{self.is_compliant}')>"


class Meal(TimestampedModel):
    """
    Daily meals with traceability
    Scoped by enterprise_id
    """
    __tablename__ = "meal"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("supplier.id"),
        nullable=True
    )

    batch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch.id"),
        nullable=True
    )

    responsible_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="User who validated the meal"
    )

    date = Column(Date, nullable=False, index=True)
    meal_type = Column(Enum(MealType), nullable=False)
    description = Column(Text, nullable=True, comment="Meal details (menu, ingredients)")

    # Relationships
    enterprise = relationship("Enterprise", back_populates="meals")
    supplier = relationship("Supplier", backref="meals")
    batch = relationship("Batch", backref="meals")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="meals")

    def __repr__(self):
        return f"<Meal(id='{self.id}', date='{self.date}', type='{self.meal_type.value}')>"


class Temperature(BaseModel):
    """
    Temperature control records for meals
    Multiple checkpoints per meal
    """
    __tablename__ = "temperature"

    meal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal.id"),
        nullable=False,
        index=True
    )

    responsible_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="User who recorded temperature"
    )

    checkpoint = Column(Enum(Checkpoint), nullable=False, comment="Control stage")
    temperature = Column(DECIMAL(5, 2), nullable=False, comment="Measured temperature (°C)")
    is_compliant = Column(Boolean, default=True, nullable=False)
    observations = Column(Text, nullable=True)
    control_date = Column(DateTime(timezone=True), nullable=False, comment="Date/time of reading")

    # Relationships
    meal = relationship("Meal", backref="temperatures")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="temperatures")

    def __repr__(self):
        return f"<Temperature(id='{self.id}', checkpoint='{self.checkpoint.value}', temp='{self.temperature}°C')>"


class Equipment(TimestampedModel):
    """
    Kitchen equipment maintenance tracking
    Scoped by enterprise_id
    """
    __tablename__ = "equipment"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=True, comment="Category (fridge, oven, warmer, etc.)")
    last_control_date = Column(Date, nullable=True)
    target_temperature = Column(DECIMAL(5, 2), nullable=True, comment="Target temperature for fridges/freezers")
    is_compliant = Column(Boolean, default=True, nullable=False)
    observations = Column(Text, nullable=True, comment="Maintenance details")

    # Relationships
    enterprise = relationship("Enterprise", back_populates="equipment")

    def __repr__(self):
        return f"<Equipment(id='{self.id}', name='{self.name}', type='{self.type}')>"


class CleaningHaccp(BaseModel):
    """
    HACCP-specific cleaning records (kitchen zones)
    Different from cLean module cleaning_log
    Scoped by enterprise_id
    """
    __tablename__ = "cleaning_haccp"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    responsible_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="User who performed cleaning"
    )

    zone = Column(String(100), nullable=False, comment="Cleaned area (kitchen, refrigerator, floor, etc.)")
    product_used = Column(String(100), nullable=True, comment="Disinfectant or detergent used")
    frequency = Column(Enum(CleaningFrequency), nullable=False)
    cleaning_date = Column(DateTime(timezone=True), nullable=False)
    observations = Column(Text, nullable=True)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="cleaning_haccp")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="cleaning_haccp_records")

    def __repr__(self):
        return f"<CleaningHaccp(id='{self.id}', zone='{self.zone}', date='{self.cleaning_date}')>"


class NonCompliance(TimestampedModel):
    """
    Non-compliance incident tracking
    Scoped by enterprise_id
    """
    __tablename__ = "non_compliance"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    responsible_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="User responsible for incident"
    )

    type = Column(Enum(NonComplianceType), nullable=False)
    description = Column(Text, nullable=False, comment="Non-compliance details")
    report_date = Column(DateTime(timezone=True), nullable=False, comment="Incident date")
    corrective_action = Column(Text, nullable=True, comment="Corrective measure taken")
    status = Column(Enum(NonComplianceStatus), default=NonComplianceStatus.OPEN, nullable=False)

    # Relationships
    enterprise = relationship("Enterprise", back_populates="non_compliances")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="non_compliances")

    def __repr__(self):
        return f"<NonCompliance(id='{self.id}', type='{self.type.value}', status='{self.status.value}')>"


class Document(BaseModel):
    """
    Compliance documentation (PDFs, images, records)
    Scoped by enterprise_id
    """
    __tablename__ = "document"

    enterprise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enterprises.id"),
        nullable=False,
        index=True
    )

    responsible_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        comment="User who uploaded document"
    )

    name = Column(String(150), nullable=False, comment="Document name")
    category = Column(Enum(DocumentCategory), nullable=False)
    file_path = Column(String(255), nullable=False, comment="Link to file (PDF, image, etc.)")
    creation_date = Column(Date, nullable=False)
    retention_period = Column(String(50), nullable=True, comment="Retention period (e.g. '5 years')")

    # Relationships
    enterprise = relationship("Enterprise", back_populates="documents")
    responsible = relationship("User", foreign_keys=[responsible_id], back_populates="documents")

    def __repr__(self):
        return f"<Document(id='{self.id}', name='{self.name}', category='{self.category.value}')>"


class MealChildren(BaseModel):
    """
    Associative table: tracks which children ate which meals
    With portion and observations
    """
    __tablename__ = "meal_children"

    meal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("meal.id"),
        nullable=False
    )

    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("child.id"),
        nullable=False
    )

    portion = Column(String(50), nullable=True, comment="Portion served (e.g. '1/2', 'full', 'small')")
    observations = Column(Text, nullable=True, comment="Notes (refusal, appetite, incident)")

    # Relationships
    meal = relationship("Meal", backref="meal_children")
    child = relationship("Child", backref="meals_eaten")

    def __repr__(self):
        return f"<MealChildren(id='{self.id}', meal_id='{self.meal_id}', child_id='{self.child_id}')>"
