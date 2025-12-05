# routers/empleados.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Empleado
from schemas import EmpleadoCreate, EmpleadoUpdate, EmpleadoOut

router = APIRouter(
    prefix="/empleados",
    tags=["empleados"],
)


@router.get("/", response_model=List[EmpleadoOut])
def listar_empleados(db: Session = Depends(get_db)):
    empleados = db.query(Empleado).all()
    return empleados


@router.get("/{cedula}", response_model=EmpleadoOut)
def obtener_empleado(cedula: str, db: Session = Depends(get_db)):
    empleado = db.query(Empleado).filter(Empleado.cedula == cedula).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con cedula {cedula} no encontrado",
        )
    return empleado


@router.post("/", response_model=EmpleadoOut, status_code=status.HTTP_201_CREATED)
def crear_empleado(datos: EmpleadoCreate, db: Session = Depends(get_db)):
    # Verificar que no exista ya esa cedula
    existe = db.query(Empleado).filter(Empleado.cedula == datos.cedula).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un empleado con cedula {datos.cedula}",
        )

    empleado = Empleado(**datos.dict())
    db.add(empleado)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.put("/{cedula}", response_model=EmpleadoOut)
def actualizar_empleado(
    cedula: str, cambios: EmpleadoUpdate, db: Session = Depends(get_db)
):
    empleado = db.query(Empleado).filter(Empleado.cedula == cedula).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con cedula {cedula} no encontrado",
        )

    datos_actualizar = cambios.dict(exclude_unset=True)
    for campo, valor in datos_actualizar.items():
        setattr(empleado, campo, valor)

    db.commit()
    db.refresh(empleado)
    return empleado


@router.delete("/{cedula}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_empleado(cedula: str, db: Session = Depends(get_db)):
    empleado = db.query(Empleado).filter(Empleado.cedula == cedula).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con cedula {cedula} no encontrado",
        )

    db.delete(empleado)
    db.commit()
    return None
