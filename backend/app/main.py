from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.base import Base
from app.db.session import engine
from app.routes.auth import router as auth_router
from app.routes.item import router as item_router
from app.models import item, user

Base.metadata.create_all(bind=engine)


app = FastAPI(title="KREAT APP",
    description="Inventory Control API",
    version="0.1.0"
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(item_router)
app.include_router(auth_router)

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Bienvenido a la API de KREAT APP",
        "status": "online",
        "docs": "/docs"
    }
