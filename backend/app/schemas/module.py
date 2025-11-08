"""
Pydantic schemas for Module model
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.module import ModuleType


# Verilog Port Schema
class VerilogPort(BaseModel):
    """Schema for Verilog module port"""
    name: str
    direction: str  # input, output, inout
    width: Optional[int] = 1  # Bit width
    range: Optional[str] = None  # e.g., "[7:0]"


# Verilog Parameter Schema
class VerilogParameter(BaseModel):
    """Schema for Verilog module parameter"""
    name: str
    default_value: Optional[str] = None
    type: Optional[str] = None


# Python Method Schema
class PythonMethod(BaseModel):
    """Schema for Python class method"""
    name: str
    is_static: bool = False
    is_classmethod: bool = False
    docstring: Optional[str] = None
    parameters: List[str] = []


# Module Metadata Schemas
class VerilogModuleMetadata(BaseModel):
    """Metadata for Verilog modules"""
    ports: List[VerilogPort] = []
    parameters: List[VerilogParameter] = []
    instances: List[str] = []  # Instantiated submodules


class PythonModuleMetadata(BaseModel):
    """Metadata for Python modules"""
    methods: List[PythonMethod] = []
    attributes: List[str] = []
    base_classes: List[str] = []
    docstring: Optional[str] = None


# Module Creation
class ModuleCreate(BaseModel):
    """Schema for creating a new module"""
    name: str
    module_type: ModuleType
    module_metadata: Optional[Dict[str, Any]] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    description: Optional[str] = None
    file_id: int
    project_id: int


# Module Update
class ModuleUpdate(BaseModel):
    """Schema for updating a module"""
    name: Optional[str] = None
    module_metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


# Module Response
class ModuleResponse(BaseModel):
    """Schema for module data in responses"""
    id: int
    name: str
    module_type: ModuleType
    module_metadata: Optional[Dict[str, Any]] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    description: Optional[str] = None
    file_id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Module List Item
class ModuleListItem(BaseModel):
    """Schema for module in list views"""
    id: int
    name: str
    module_type: ModuleType
    description: Optional[str] = None
    file_id: int
    filename: Optional[str] = None  # Populated from join

    model_config = {"from_attributes": True}


# Module with File Info
class ModuleWithFile(ModuleResponse):
    """Module response with file information"""
    filename: str
    filepath: str

    model_config = {"from_attributes": True}


# Module Parse Result
class ModuleParseResult(BaseModel):
    """Result from parsing a file for modules"""
    success: bool
    modules_found: int
    modules: List[ModuleResponse] = []
    errors: List[str] = []
    warnings: List[str] = []
