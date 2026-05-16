from pydantic import BaseModel, Field
from typing import Optional

# Esquemas para Locations
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Nombre de la ubicación")
    description: Optional[str] = Field(None, max_length=200, description="Descripción de la ubicación")

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int

    class Config:
        from_attributes = True


#Esquemas para Items
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del item")
    description: Optional[str] = Field(None, max_length=200, description="Descripción del item")
    qr_code: str = Field(..., min_length=1, max_length=100, description="Código QR del item")
    quantity: int = Field(..., ge=0, description="Cantidad del item")
    min_stock: int = Field(..., ge=0, description="Stock mínimo del item")
    location_id: int = Field(..., ge=1, description="ID de la ubicación")

class ItemCreate(ItemBase):
    location_id: int

class ItemResponse(ItemBase):
    id: int
    location_id: int

    location: Optional[LocationResponse] = None

    class Config:
        from_attributes = True

