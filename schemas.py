# schemas.py
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class EmpleadoBase(BaseModel):
    cedula: str
    p_apellido: Optional[str] = None
    s_apellido: Optional[str] = None
    p_nombre: Optional[str] = None
    s_nombre: Optional[str] = None
    correo_electronico: Optional[EmailStr] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    estado_civil: Optional[str] = None
    tipo_sangre: Optional[str] = None
    gestacion: Optional[str] = None
    direccion_residencia: Optional[str] = None
    barrio_localidad: Optional[str] = None
    departamento_residencia: Optional[str] = None
    ciudad_residencia: Optional[str] = None
    usuario: Optional[str] = None


class EmpleadoCreate(EmpleadoBase):
    """
    Esquema para crear empleado.
    Cedula es obligatoria, el resto opcional.
    """
    pass


class EmpleadoUpdate(BaseModel):
    """
    Esquema para actualizacion parcial.
    Ningun campo es obligatorio; solo lo que quieras cambiar.
    """
    p_apellido: Optional[str] = None
    s_apellido: Optional[str] = None
    p_nombre: Optional[str] = None
    s_nombre: Optional[str] = None
    correo_electronico: Optional[EmailStr] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    estado_civil: Optional[str] = None
    tipo_sangre: Optional[str] = None
    gestacion: Optional[str] = None
    direccion_residencia: Optional[str] = None
    barrio_localidad: Optional[str] = None
    departamento_residencia: Optional[str] = None
    ciudad_residencia: Optional[str] = None
    usuario: Optional[str] = None


class EmpleadoOut(EmpleadoBase):
    modificacion: Optional[date] = None  # o datetime si prefieres

    # Nueva forma en Pydantic v2
    model_config = ConfigDict(from_attributes=True)
