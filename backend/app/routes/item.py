from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.security import get_current_user


from app.database import get_db
from app.models.item import Location, Item, MovementLog
from app.models.user import User
from app.schemas.item import (
    LocationCreate, LocationResponse,
    ItemCreate, ItemResponse,
    QRScanInput, MovementLogResponse
)

# Inicializamos el router. Los 'tags' agrupan los endpoints en la documentación de Swagger.
router = APIRouter(prefix="/inventory", tags=["Inventory"])

# ==========================================
#      ENDPOINTS PARA UBICACIONES (Locations)
# ==========================================

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def createLocation(location_data: LocationCreate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):

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

@router.post("/items/scan",status_code=status.HTTP_200_OK)
def scan_qr_code(scan_data: QRScanInput, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """
    Endpoint principal para la App de Android. 
    Procesa el escaneo de un código QR, actualiza el stock actual y registra el movimiento.
    """

    item = db.query(Item).filter(Item.qr_code == scan_data.qr_code).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operacion invalida. El codigo QR '{scan_data.qr_code}' no corresponde a ningun producto registrado"
        )

    if scan_data.type == "IN":
        item.quantity += scan_data.quantity

    elif scan_data.type == "OUT":
        if item.quantity < scan_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay suficiente stock para retirar. Stock disponible {item.quantity}. Intentaste retirar {scan_data.quantity}"
            )
        item.quantity -= scan_data.quantity

    
    log_entry = MovementLog(
        item_id=item.id,
        type = scan_data.type,
        quantity = scan_data.quantity,
        notes = scan_data.notes
    )

    # 4. Guardar ambos cambios en una sola transacción atómica de Base de Datos
    db.add(log_entry)
    db.commit()
    db.refresh(item)

    return {
        "status": "success",
        "message": f"Inventario actualizado correctamente para el producto: {item.name}",
        "product_details": {
            "id": item.id,
            "name": item.name,
            "new_quantity": item.quantity,
            "under_stock_alert": item.quantity < item.min_stock  # Alerta si cayó por debajo del mínimo
        }
    }


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def createItem(item_data: ItemCreate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):

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
