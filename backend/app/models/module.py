"""
Module database model for design modules extracted from files

Modules represent reusable design components:
- Verilog modules (digital design)
- Python classes/functions (analog layout, parameterized designs)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class ModuleType(str, enum.Enum):
    """Types of design modules"""
    VERILOG_MODULE = "verilog_module"  # Verilog digital module
    VERILOG_PACKAGE = "verilog_package"  # SystemVerilog package
    PYTHON_CLASS = "python_class"  # Python class for analog layout
    PYTHON_FUNCTION = "python_function"  # Python function for design generation
    SPICE_SUBCIRCUIT = "spice_subcircuit"  # SPICE subcircuit


class Module(Base):
    """
    Module model representing parsed design modules

    Modules are extracted from files and represent reusable design components.
    Each file can contain multiple modules.
    """

    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)

    # Module identification
    name = Column(String, nullable=False, index=True)
    module_type = Column(Enum(ModuleType), nullable=False)

    # Module metadata (JSON structure depends on type)
    # For Verilog: {ports: [{name, direction, width}], parameters: [...]}
    # For Python: {methods: [...], attributes: [...], docstring: "..."}
    metadata = Column(JSON, nullable=True)

    # Source information
    start_line = Column(Integer, nullable=True)  # Line where module starts in file
    end_line = Column(Integer, nullable=True)  # Line where module ends

    # Documentation
    description = Column(Text, nullable=True)  # Extracted from comments/docstrings

    # Relationships
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    file = relationship("File", back_populates="modules")

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="modules")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Module(name={self.name}, type={self.module_type}, file_id={self.file_id})>"
