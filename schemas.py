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


# =========================
# CONTRATOS
# =========================
class ContratoBase(BaseModel):
    id_contrato: str
    cedula: str
    id_posicion: Optional[str] = None
    familia: Optional[str] = None
    cargo: Optional[str] = None
    rol: Optional[str] = None
    banda: Optional[str] = None
    salario: Optional[float] = None
    nivel_riesgo: Optional[str] = None
    atep: Optional[str] = None
    direccion: Optional[str] = None
    gerencia: Optional[str] = None
    area: Optional[str] = None
    subarea: Optional[str] = None
    tipo_contrato: Optional[str] = None
    numero_contrato: Optional[str] = None
    f_contrato: Optional[date] = None
    numero_otrosi: Optional[str] = None
    prorrogas: Optional[str] = None
    f_ingreso: Optional[date] = None
    f_terminacion_contrato: Optional[date] = None
    modalidad_teletrabajo: Optional[str] = None
    total_dias_teletrabajo: Optional[int] = None
    sede: Optional[str] = None
    ciudad_contratacion: Optional[str] = None
    estado: Optional[str] = None
    metodo_seleccion: Optional[str] = None
    encargo: Optional[str] = None
    motivo_ingreso: Optional[str] = None
    fecha_termi: Optional[date] = None
    causal_retiro: Optional[str] = None
    usuario: Optional[str] = None


class ContratoCreate(ContratoBase):
    """Esquema para crear contrato."""
    pass


class ContratoUpdate(BaseModel):
    """Actualizacion parcial del contrato."""
    salario: Optional[float] = None
    estado: Optional[str] = None
    causal_retiro: Optional[str] = None
    usuario: Optional[str] = None


class ContratoOut(ContratoBase):
    model_config = ConfigDict(from_attributes=True)
