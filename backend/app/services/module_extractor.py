"""
Module extraction service

Coordinates parsing of files and extraction of design modules.
"""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.module import Module, ModuleType
from app.models.project_file import ProjectFile
from app.services.verilog_parser import verilog_parser
from app.services.python_parser import python_parser
from app.schemas.module import ModuleParseResult, ModuleResponse

logger = logging.getLogger(__name__)


class ModuleExtractor:
    """Service for extracting modules from source files"""

    def extract_modules_from_file(
        self,
        file_content: str,
        file_id: int,
        project_id: int,
        filename: str,
        db: Session
    ) -> ModuleParseResult:
        """
        Extract modules from a file and save to database

        Args:
            file_content: File content as string
            file_id: File database ID
            project_id: Project database ID
            filename: Original filename
            db: Database session

        Returns:
            ModuleParseResult with extracted modules and any errors
        """
        errors = []
        warnings = []
        modules_data = []

        try:
            # Determine file type and parse accordingly
            if filename.endswith(('.v', '.vh', '.sv')):
                # Verilog file
                modules_data = verilog_parser.parse_file(file_content, filename)
                default_type = ModuleType.VERILOG_MODULE

            elif filename.endswith('.py'):
                # Python file
                modules_data = python_parser.parse_file(file_content, filename)
                default_type = None  # Type is set by parser

            elif filename.endswith('.sp') or filename.endswith('.spi'):
                # SPICE file - not yet implemented
                warnings.append(f"SPICE parsing not yet implemented for {filename}")
                return ModuleParseResult(
                    success=True,
                    modules_found=0,
                    modules=[],
                    errors=errors,
                    warnings=warnings
                )

            else:
                # Unknown file type
                warnings.append(f"Unknown file type for {filename}, skipping module extraction")
                return ModuleParseResult(
                    success=True,
                    modules_found=0,
                    modules=[],
                    errors=errors,
                    warnings=warnings
                )

            # Delete existing modules for this file
            db.query(Module).filter(Module.file_id == file_id).delete()

            # Create module records
            created_modules = []
            for module_data in modules_data:
                try:
                    # Determine module type
                    if "module_type" in module_data:
                        module_type = ModuleType(module_data["module_type"])
                    else:
                        module_type = default_type

                    # Create module
                    module = Module(
                        name=module_data["name"],
                        module_type=module_type,
                        metadata=module_data.get("metadata"),
                        start_line=module_data.get("start_line"),
                        end_line=module_data.get("end_line"),
                        description=module_data.get("description"),
                        file_id=file_id,
                        project_id=project_id
                    )

                    db.add(module)
                    db.flush()  # Get the ID
                    created_modules.append(module)

                    logger.info(f"Extracted module: {module.name} from {filename}")

                except Exception as e:
                    error_msg = f"Error creating module {module_data.get('name', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Commit all changes
            db.commit()

            # Refresh to get relationships
            for module in created_modules:
                db.refresh(module)

            # Convert to response schema
            module_responses = [
                ModuleResponse.model_validate(m) for m in created_modules
            ]

            return ModuleParseResult(
                success=len(errors) == 0,
                modules_found=len(created_modules),
                modules=module_responses,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error extracting modules from {filename}: {e}")
            db.rollback()
            errors.append(f"Module extraction failed: {str(e)}")

            return ModuleParseResult(
                success=False,
                modules_found=0,
                modules=[],
                errors=errors,
                warnings=warnings
            )

    def re_extract_all_modules(self, project_id: int, db: Session) -> ModuleParseResult:
        """
        Re-extract modules from all files in a project

        Useful when parser is updated or for bulk operations.

        Args:
            project_id: Project ID
            db: Database session

        Returns:
            Combined ModuleParseResult for all files
        """
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return ModuleParseResult(
                success=False,
                modules_found=0,
                modules=[],
                errors=[f"Project {project_id} not found"],
                warnings=[]
            )

        all_modules = []
        all_errors = []
        all_warnings = []

        for file in project.files:
            # Get file content
            if file.use_minio and file.minio_bucket and file.minio_key:
                # TODO: Download from MinIO
                all_warnings.append(f"MinIO download not yet implemented for {file.filename}")
                continue

            elif file.content:
                # Use legacy content field
                result = self.extract_modules_from_file(
                    file.content,
                    file.id,
                    project_id,
                    file.filename,
                    db
                )

                all_modules.extend(result.modules)
                all_errors.extend(result.errors)
                all_warnings.extend(result.warnings)

        return ModuleParseResult(
            success=len(all_errors) == 0,
            modules_found=len(all_modules),
            modules=all_modules,
            errors=all_errors,
            warnings=all_warnings
        )


# Global extractor instance
module_extractor = ModuleExtractor()
