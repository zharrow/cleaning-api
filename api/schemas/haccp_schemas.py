"""
HACCP Pydantic Schemas - Request/Response validation
All schemas for food safety and compliance management
"""

import uuid
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


# ==================== ENUMS ====================

class Section(str, Enum):
    """Child care sections/groups"""
    BABIES = "BABIES"
    TODDLERS = "TODDLERS"
    PRESCHOOLERS = "PRESCHOOLERS"


class MealType(str, Enum):
    """Types of meals"""
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    SNACK = "SNACK"


class Checkpoint(str, Enum):
    """Temperature control checkpoints"""
    RECEPTION = "RECEPTION"
    HOLDING = "HOLDING"
    SERVICE = "SERVICE"
    STORAGE = "STORAGE"


class CleaningFrequency(str, Enum):
    """HACCP cleaning frequency"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class NonComplianceType(str, Enum):
    """Non-compliance incident types"""
    PRODUCT = "PRODUCT"
    TEMPERATURE = "TEMPERATURE"
    HYGIENE = "HYGIENE"
    OTHER = "OTHER"


class NonComplianceStatus(str, Enum):
    """Non-compliance processing status"""
    OPEN = "OPEN"
    CORRECTED = "CORRECTED"
    CLOSED = "CLOSED"


class DocumentCategory(str, Enum):
    """Document categories"""
    TEMPERATURES = "TEMPERATURES"
    CLEANING = "CLEANING"
    TRAINING = "TRAINING"
    COMPLIANCE = "COMPLIANCE"
    OTHER = "OTHER"


# ==================== CHILD SCHEMAS ====================

class ChildCreate(BaseModel):
    """Schema for creating a child"""
    last_name: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    birth_date: date
    section: Section
    allergies: Optional[str] = None
    specific_diet: Optional[str] = None


class ChildUpdate(BaseModel):
    """Schema for updating a child"""
    last_name: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date] = None
    section: Optional[Section] = None
    allergies: Optional[str] = None
    specific_diet: Optional[str] = None
    is_active: Optional[bool] = None


class ChildResponse(BaseModel):
    """Schema for child response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    last_name: str
    first_name: str
    birth_date: date
    section: Section
    allergies: Optional[str]
    specific_diet: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== SUPPLIER SCHEMAS ====================

class SupplierCreate(BaseModel):
    """Schema for creating a supplier"""
    name: str = Field(..., max_length=150)
    contact_name: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = None
    haccp_certified: bool = False
    validation_date: Optional[date] = None


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier"""
    name: Optional[str] = Field(None, max_length=150)
    contact_name: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    address: Optional[str] = None
    haccp_certified: Optional[bool] = None
    validation_date: Optional[date] = None


class SupplierResponse(BaseModel):
    """Schema for supplier response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    name: str
    contact_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    haccp_certified: bool
    validation_date: Optional[date]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== PRODUCT SCHEMAS ====================

class ProductCreate(BaseModel):
    """Schema for creating a product"""
    supplier_id: Optional[uuid.UUID] = None
    name: str = Field(..., max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    allergens: Optional[str] = None
    stock_unit: Optional[str] = Field(None, max_length=20)
    current_stock: Optional[Decimal] = None
    expiry_date: Optional[date] = None


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    supplier_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(None, max_length=150)
    category: Optional[str] = Field(None, max_length=100)
    allergens: Optional[str] = None
    stock_unit: Optional[str] = Field(None, max_length=20)
    current_stock: Optional[Decimal] = None
    expiry_date: Optional[date] = None


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    supplier_id: Optional[uuid.UUID]
    name: str
    category: Optional[str]
    allergens: Optional[str]
    stock_unit: Optional[str]
    current_stock: Optional[Decimal]
    expiry_date: Optional[date]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== BATCH SCHEMAS ====================

class BatchCreate(BaseModel):
    """Schema for creating a batch"""
    product_id: uuid.UUID
    batch_code: str = Field(..., max_length=100)
    reception_date: date
    received_quantity: Decimal
    reception_temperature: Optional[Decimal] = None
    is_compliant: bool = True
    observations: Optional[str] = None


class BatchUpdate(BaseModel):
    """Schema for updating a batch"""
    batch_code: Optional[str] = Field(None, max_length=100)
    reception_date: Optional[date] = None
    received_quantity: Optional[Decimal] = None
    reception_temperature: Optional[Decimal] = None
    is_compliant: Optional[bool] = None
    observations: Optional[str] = None


class BatchResponse(BaseModel):
    """Schema for batch response"""
    id: uuid.UUID
    product_id: uuid.UUID
    batch_code: str
    reception_date: date
    received_quantity: Decimal
    reception_temperature: Optional[Decimal]
    is_compliant: bool
    observations: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== MEAL SCHEMAS ====================

class MealCreate(BaseModel):
    """Schema for creating a meal"""
    supplier_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    responsible_id: Optional[uuid.UUID] = None
    date: date
    meal_type: MealType
    description: Optional[str] = None


class MealUpdate(BaseModel):
    """Schema for updating a meal"""
    supplier_id: Optional[uuid.UUID] = None
    batch_id: Optional[uuid.UUID] = None
    responsible_id: Optional[uuid.UUID] = None
    date: Optional[date] = None
    meal_type: Optional[MealType] = None
    description: Optional[str] = None


class MealResponse(BaseModel):
    """Schema for meal response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    supplier_id: Optional[uuid.UUID]
    batch_id: Optional[uuid.UUID]
    responsible_id: Optional[uuid.UUID]
    date: date
    meal_type: MealType
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== TEMPERATURE SCHEMAS ====================

class TemperatureCreate(BaseModel):
    """Schema for creating a temperature record"""
    meal_id: uuid.UUID
    responsible_id: Optional[uuid.UUID] = None
    checkpoint: Checkpoint
    temperature: Decimal
    is_compliant: bool = True
    observations: Optional[str] = None
    control_date: datetime


class TemperatureUpdate(BaseModel):
    """Schema for updating a temperature record"""
    checkpoint: Optional[Checkpoint] = None
    temperature: Optional[Decimal] = None
    is_compliant: Optional[bool] = None
    observations: Optional[str] = None
    control_date: Optional[datetime] = None


class TemperatureResponse(BaseModel):
    """Schema for temperature response"""
    id: uuid.UUID
    meal_id: uuid.UUID
    responsible_id: Optional[uuid.UUID]
    checkpoint: Checkpoint
    temperature: Decimal
    is_compliant: bool
    observations: Optional[str]
    control_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== EQUIPMENT SCHEMAS ====================

class EquipmentCreate(BaseModel):
    """Schema for creating equipment"""
    name: str = Field(..., max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    last_control_date: Optional[date] = None
    target_temperature: Optional[Decimal] = None
    is_compliant: bool = True
    observations: Optional[str] = None


class EquipmentUpdate(BaseModel):
    """Schema for updating equipment"""
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    last_control_date: Optional[date] = None
    target_temperature: Optional[Decimal] = None
    is_compliant: Optional[bool] = None
    observations: Optional[str] = None


class EquipmentResponse(BaseModel):
    """Schema for equipment response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    name: str
    type: Optional[str]
    last_control_date: Optional[date]
    target_temperature: Optional[Decimal]
    is_compliant: bool
    observations: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== CLEANING HACCP SCHEMAS ====================

class CleaningHaccpCreate(BaseModel):
    """Schema for creating HACCP cleaning record"""
    responsible_id: Optional[uuid.UUID] = None
    zone: str = Field(..., max_length=100)
    product_used: Optional[str] = Field(None, max_length=100)
    frequency: CleaningFrequency
    cleaning_date: datetime
    observations: Optional[str] = None


class CleaningHaccpUpdate(BaseModel):
    """Schema for updating HACCP cleaning record"""
    zone: Optional[str] = Field(None, max_length=100)
    product_used: Optional[str] = Field(None, max_length=100)
    frequency: Optional[CleaningFrequency] = None
    cleaning_date: Optional[datetime] = None
    observations: Optional[str] = None


class CleaningHaccpResponse(BaseModel):
    """Schema for HACCP cleaning response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    responsible_id: Optional[uuid.UUID]
    zone: str
    product_used: Optional[str]
    frequency: CleaningFrequency
    cleaning_date: datetime
    observations: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== NON-COMPLIANCE SCHEMAS ====================

class NonComplianceCreate(BaseModel):
    """Schema for creating non-compliance record"""
    responsible_id: Optional[uuid.UUID] = None
    type: NonComplianceType
    description: str
    report_date: datetime
    corrective_action: Optional[str] = None
    status: NonComplianceStatus = NonComplianceStatus.OPEN


class NonComplianceUpdate(BaseModel):
    """Schema for updating non-compliance record"""
    type: Optional[NonComplianceType] = None
    description: Optional[str] = None
    corrective_action: Optional[str] = None
    status: Optional[NonComplianceStatus] = None


class NonComplianceResponse(BaseModel):
    """Schema for non-compliance response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    responsible_id: Optional[uuid.UUID]
    type: NonComplianceType
    description: str
    report_date: datetime
    corrective_action: Optional[str]
    status: NonComplianceStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== DOCUMENT SCHEMAS ====================

class DocumentCreate(BaseModel):
    """Schema for creating document"""
    responsible_id: Optional[uuid.UUID] = None
    name: str = Field(..., max_length=150)
    category: DocumentCategory
    file_path: str = Field(..., max_length=255)
    creation_date: date
    retention_period: Optional[str] = Field(None, max_length=50)


class DocumentUpdate(BaseModel):
    """Schema for updating document"""
    name: Optional[str] = Field(None, max_length=150)
    category: Optional[DocumentCategory] = None
    file_path: Optional[str] = Field(None, max_length=255)
    retention_period: Optional[str] = Field(None, max_length=50)


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: uuid.UUID
    enterprise_id: uuid.UUID
    responsible_id: Optional[uuid.UUID]
    name: str
    category: DocumentCategory
    file_path: str
    creation_date: date
    retention_period: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== MEAL CHILDREN SCHEMAS ====================

class MealChildrenCreate(BaseModel):
    """Schema for creating meal-children association"""
    meal_id: uuid.UUID
    child_id: uuid.UUID
    portion: Optional[str] = Field(None, max_length=50)
    observations: Optional[str] = None


class MealChildrenUpdate(BaseModel):
    """Schema for updating meal-children association"""
    portion: Optional[str] = Field(None, max_length=50)
    observations: Optional[str] = None


class MealChildrenResponse(BaseModel):
    """Schema for meal-children response"""
    id: uuid.UUID
    meal_id: uuid.UUID
    child_id: uuid.UUID
    portion: Optional[str]
    observations: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
