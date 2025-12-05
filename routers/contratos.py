from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Contrato
from schemas_contratos import ContratoCreate, ContratoUpdate, ContratoOut


router = APIRouter(prefix="/contratos", tags=["Contratos"])


@router.post("/", response_model=ContratoOut)
def crear_contrato(data: ContratoCreate, db: Session = Depends(get_db)):

    contrato_existente = db.query(Contrato).filter(Contrato.id_contrato == data.id_contrato).first()
    if contrato_existente:
        raise HTTPException(status_code=400, detail="El contrato ya existe")

    nuevo = Contrato(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


@router.get("/", response_model=list[ContratoOut])
def listar_contratos(db: Session = Depends(get_db)):
    return db.query(Contrato).all()


@router.get("/{id_contrato}", response_model=ContratoOut)
def obtener_contrato(id_contrato: str, db: Session = Depends(get_db)):
    contrato = db.query(Contrato).filter(Contrato.id_contrato == id_contrato).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return contrato


@router.patch("/{id_contrato}", response_model=ContratoOut)
def actualizar_contrato(id_contrato: str, data: ContratoUpdate, db: Session = Depends(get_db)):
    contrato = db.query(Contrato).filter(Contrato.id_contrato == id_contrato).first()
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(contrato, field, value)

    db.commit()
    db.refresh(contrato)
    return contrato
