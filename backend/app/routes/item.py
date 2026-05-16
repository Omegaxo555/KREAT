from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List


from app.database import get_db
from app.models.item import Location, Item
from app.schemas.item import (
    LocationCreate, LocationResponse,
    ItemCreate, ItemResponse
)

# Inicializamos el router. Los 'tags' agrupan los endpoints en la documentación de Swagger.
router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ==========================================
#      ENDPOINTS PARA UBICACIONES (Locations)
# ==========================================

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def createLocation(location_data: LocationCreate, db: Session = Depends(get_db)):

    existing_location = db.query(Location).filter(Location.name == location_data.name).first()
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La ubicación con el nombre '{location_data.name}' ya está registrada."
        )

    new_location = Location(**location_data.model_dump())

    db.add(new_location)
    db.commit()
    db.refresh(new_location)

    return new_location

@router.get("/locations",response_model=List[LocationResponse])
def listLocation(db: Session = Depends(get_db)):
    return db.query(Location).all()


# ==========================================
#         ENDPOINTS PARA ÍTEMS (Items)
# ==========================================

@router.post("/items", response_model=ItemCreate, status_code=status.HTTP_201_CREATED)
def createItem(item_data: ItemCreate, db: Session = Depends(get_db)):

    location = db.query(Location).filter(Location.id == item_data.location_id ).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se puede crear el ítem. La ubicación con ID {item_data.location_id} no existe."
        )

    existing_qr = db.query(Item).filter(Item.qr_code == item_data.qr_code).first()
    if existing_qr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código QR ya está registrado en otro producto."
        )

    new_item = Item(**item_data.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item

@router.get("/items", response_model=List[ItemResponse])
def list_items(db: Session = Depends(get_db)):
    """
    Retorna la lista de todos los productos en stock, incluyendo los datos de su ubicación.
    """
    # SQLAlchemy hace un JOIN automático tras bambalinas gracias a las relaciones que definimos
    return db.query(Item).all()
