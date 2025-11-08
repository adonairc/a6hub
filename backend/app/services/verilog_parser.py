"""
Verilog parser using Yosys

Extracts module definitions, ports, parameters from Verilog files.
"""
import subprocess
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile

from app.core.config import settings
from app.schemas.module import VerilogPort, VerilogParameter, VerilogModuleMetadata

logger = logging.getLogger(__name__)


class VerilogParser:
    """Parser for Verilog files using Yosys"""

    def __init__(self):
        self.yosys_path = settings.YOSYS_PATH

    def parse_file(self, file_content: str, filename: str = "design.v") -> List[Dict[str, Any]]:
        """
        Parse a Verilog file and extract module information

        Args:
            file_content: Verilog file content
            filename: Original filename

        Returns:
            List of module dictionaries with metadata
        """
        try:
            # Create temporary file for Verilog content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
                f.write(file_content)
                temp_file = f.name

            try:
                # Parse using simple regex first (fast path)
                modules = self._parse_with_regex(file_content)

                # Enhance with Yosys analysis (slower but more accurate)
                try:
                    modules = self._enhance_with_yosys(temp_file, modules)
                except Exception as e:
                    logger.warning(f"Yosys enhancement failed, using regex only: {e}")

                return modules

            finally:
                # Clean up temporary file
                Path(temp_file).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error parsing Verilog file: {e}")
            return []

    def _parse_with_regex(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse Verilog using regex patterns

        Args:
            content: Verilog file content

        Returns:
            List of modules with basic information
        """
        modules = []

        # Pattern to match module declarations
        # Matches: module name #(parameters) (ports);
        module_pattern = re.compile(
            r'^\s*module\s+(\w+)\s*'  # module name
            r'(?:#\s*\((.*?)\)\s*)?'   # optional parameters
            r'(?:\((.*?)\)\s*)?;',      # optional port list
            re.MULTILINE | re.DOTALL
        )

        lines = content.split('\n')
        line_num = 0

        for match in module_pattern.finditer(content):
            module_name = match.group(1)
            params_str = match.group(2) if match.group(2) else ""
            ports_str = match.group(3) if match.group(3) else ""

            # Find line number
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1

            # Find endmodule
            end_match = re.search(
                r'^\s*endmodule',
                content[match.end():],
                re.MULTILINE
            )
            end_line = start_line
            if end_match:
                end_pos = match.end() + end_match.end()
                end_line = content[:end_pos].count('\n') + 1

            # Parse parameters
            parameters = self._parse_parameters(params_str)

            # Parse ports (basic - Yosys will provide better info)
            ports = self._parse_ports_simple(ports_str, content[match.end():])

            modules.append({
                "name": module_name,
                "start_line": start_line,
                "end_line": end_line,
                "ports": ports,
                "parameters": parameters,
                "instances": []  # Will be filled by Yosys
            })

        return modules

    def _parse_parameters(self, params_str: str) -> List[Dict[str, Any]]:
        """Parse module parameters"""
        parameters = []

        if not params_str:
            return parameters

        # Pattern for parameter: parameter [type] NAME = VALUE
        param_pattern = re.compile(r'parameter\s+(?:\w+\s+)?(\w+)\s*=\s*([^,)]+)')

        for match in param_pattern.finditer(params_str):
            param_name = match.group(1)
            param_value = match.group(2).strip()

            parameters.append({
                "name": param_name,
                "default_value": param_value,
                "type": None  # Could be extracted if needed
            })

        return parameters

    def _parse_ports_simple(self, ports_str: str, module_body: str) -> List[Dict[str, Any]]:
        """
        Parse port declarations (simple version)

        Args:
            ports_str: Port list from module declaration
            module_body: Module body for port declarations

        Returns:
            List of port dictionaries
        """
        ports = []

        # Extract port names from port list
        if ports_str:
            port_names = [p.strip() for p in ports_str.split(',')]
        else:
            port_names = []

        # Find port declarations in module body
        # Pattern: input/output/inout [width] name;
        port_decl_pattern = re.compile(
            r'^\s*(input|output|inout)\s+'
            r'(?:(wire|reg)\s+)?'
            r'(?:\[([^\]]+)\]\s+)?'
            r'(\w+(?:\s*,\s*\w+)*)\s*;',
            re.MULTILINE
        )

        for match in port_decl_pattern.finditer(module_body[:500]):  # Look in first 500 chars
            direction = match.group(1)
            width_str = match.group(3)
            names = match.group(4)

            # Parse width
            width = 1
            range_str = None
            if width_str:
                range_str = f"[{width_str}]"
                # Try to calculate width
                try:
                    # Handle [N:0] or [0:N] format
                    parts = width_str.split(':')
                    if len(parts) == 2:
                        high = int(parts[0].strip())
                        low = int(parts[1].strip())
                        width = abs(high - low) + 1
                except:
                    width = None  # Unknown width

            # Handle multiple names in one declaration
            for name in names.split(','):
                name = name.strip()
                ports.append({
                    "name": name,
                    "direction": direction,
                    "width": width,
                    "range": range_str
                })

        return ports

    def _enhance_with_yosys(
        self,
        verilog_file: str,
        modules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance module information using Yosys

        Args:
            verilog_file: Path to Verilog file
            modules: List of modules from regex parsing

        Returns:
            Enhanced module list
        """
        try:
            # Create Yosys script
            yosys_script = f"""
read_verilog {verilog_file}
hierarchy -check
dump
"""

            # Run Yosys
            result = subprocess.run(
                [self.yosys_path, '-Q', '-p', yosys_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse Yosys output to extract module hierarchy and instances
                instances = self._parse_yosys_output(result.stdout)

                # Update modules with instance information
                for module in modules:
                    if module["name"] in instances:
                        module["instances"] = instances[module["name"]]

            return modules

        except Exception as e:
            logger.warning(f"Yosys enhancement failed: {e}")
            return modules

    def _parse_yosys_output(self, output: str) -> Dict[str, List[str]]:
        """
        Parse Yosys dump output to extract module instances

        Returns:
            Dict mapping module names to lists of instantiated modules
        """
        instances = {}

        # This is a simplified parser - Yosys output format can vary
        # In a production system, you'd want more robust parsing

        current_module = None
        for line in output.split('\n'):
            # Detect module blocks
            if 'module' in line and '\\' in line:
                match = re.search(r'module\s+\\(\w+)', line)
                if match:
                    current_module = match.group(1)
                    instances[current_module] = []

            # Detect cell instances (instantiated modules)
            elif current_module and 'cell' in line and '\\' in line:
                match = re.search(r'cell\s+\\(\w+)', line)
                if match:
                    cell_type = match.group(1)
                    if cell_type not in instances[current_module]:
                        instances[current_module].append(cell_type)

        return instances


# Global parser instance
verilog_parser = VerilogParser()
