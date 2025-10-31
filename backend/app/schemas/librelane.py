"""
Pydantic schemas for LibreLane flow configuration
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class PDKType(str, Enum):
    """Supported PDK (Process Design Kit) types"""
    SKY130 = "sky130A"
    SKY130_HD = "sky130_fd_sc_hd"
    SKY130_HS = "sky130_fd_sc_hs"
    SKY130_MS = "sky130_fd_sc_ms"
    SKY130_LS = "sky130_fd_sc_ls"
    SKY130_HVL = "sky130_fd_sc_hvl"
    GF180MCU = "gf180mcuC"


class FlowType(str, Enum):
    """LibreLane flow types"""
    CLASSIC = "Classic"
    CUSTOM = "Custom"


class DensityType(str, Enum):
    """Placement density options"""
    LOW = "0.3"
    MEDIUM = "0.5"
    HIGH = "0.7"
    VERY_HIGH = "0.85"


class ClockPeriod(str, Enum):
    """Common clock periods in nanoseconds"""
    FAST = "5"      # 200 MHz
    MEDIUM = "10"   # 100 MHz
    SLOW = "20"     # 50 MHz
    CUSTOM = "custom"


class LibreLaneFlowConfig(BaseModel):
    """
    Configuration for LibreLane ASIC flow
    Based on OpenLane/LibreLane configuration format
    """

    # Design basics
    design_name: str = Field(..., description="Top module name")
    verilog_files: List[str] = Field(..., description="List of Verilog source files")

    # PDK Configuration
    pdk: PDKType = Field(default=PDKType.SKY130_HD, description="Process Design Kit")
    std_cell_library: Optional[str] = Field(None, description="Standard cell library (auto-selected from PDK if not specified)")

    # Flow selection
    flow: FlowType = Field(default=FlowType.CLASSIC, description="Flow type to use")

    # Clock configuration
    clock_period: str = Field(default="10", description="Clock period in nanoseconds")
    clock_port: Optional[str] = Field("clk", description="Clock port name")

    # Die/Core area
    die_area: Optional[str] = Field(None, description="Die area coordinates (e.g., '0 0 500 500')")
    core_area: Optional[str] = Field(None, description="Core area coordinates")

    # Placement
    pl_target_density: str = Field(default="0.5", description="Target placement density (0.0-1.0)")
    pl_random_seed: int = Field(default=42, description="Placement random seed for reproducibility")

    # Synthesis options
    synth_strategy: str = Field(default="AREA 0", description="Synthesis strategy")
    synth_max_fanout: int = Field(default=10, description="Maximum fanout")
    synth_buffering: bool = Field(default=True, description="Enable synthesis buffering")
    synth_sizing: bool = Field(default=True, description="Enable synthesis sizing")

    # Floorplanning
    fp_core_util: int = Field(default=50, description="Core utilization percentage")
    fp_aspect_ratio: float = Field(default=1.0, description="Core aspect ratio")
    fp_pdn_vpitch: Optional[float] = Field(None, description="PDN vertical pitch")
    fp_pdn_hpitch: Optional[float] = Field(None, description="PDN horizontal pitch")

    # Routing
    grt_repair_antennas: bool = Field(default=True, description="Repair antenna violations during global routing")
    drt_opt_iters: int = Field(default=64, description="Detailed routing optimization iterations")

    # Power/Ground
    vdd_nets: List[str] = Field(default=["vccd1"], description="VDD net names")
    gnd_nets: List[str] = Field(default=["vssd1"], description="GND net names")

    # DRC/LVS
    run_drc: bool = Field(default=True, description="Run Design Rule Check")
    run_lvs: bool = Field(default=True, description="Run Layout vs Schematic")
    run_magic_drc: bool = Field(default=True, description="Run Magic DRC")
    run_klayout_drc: bool = Field(default=False, description="Run KLayout DRC")

    # Timing
    sta_pre_cts: bool = Field(default=True, description="Run STA before clock tree synthesis")
    sta_post_cts: bool = Field(default=True, description="Run STA after clock tree synthesis")

    # Output options
    generate_final_summary: bool = Field(default=True, description="Generate final summary report")

    # Docker options
    use_docker: bool = Field(default=True, description="Run LibreLane in Docker container")
    docker_image: str = Field(default="ghcr.io/librelane/librelane:latest", description="Docker image to use")

    # Advanced options
    extra_args: Optional[Dict[str, Any]] = Field(None, description="Additional LibreLane arguments")

    class Config:
        use_enum_values = True


class LibreLaneBuildRequest(BaseModel):
    """Request schema for starting a LibreLane build"""
    config: LibreLaneFlowConfig


class LibreLaneBuildStatus(BaseModel):
    """Status response for LibreLane build"""
    job_id: int
    status: str
    progress: Optional[str] = None
    current_step: Optional[str] = None
    progress_data: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None


class LibreLaneFlowPreset(BaseModel):
    """Preset configuration for common use cases"""
    name: str
    description: str
    config: LibreLaneFlowConfig


# Common presets
LIBRELANE_PRESETS = {
    "minimal": LibreLaneFlowPreset(
        name="Minimal Flow",
        description="Fast flow for quick iterations and testing",
        config=LibreLaneFlowConfig(
            design_name="example",
            verilog_files=["design.v"],
            pdk=PDKType.SKY130_HD,
            clock_period="20",
            pl_target_density="0.3",
            run_drc=False,
            run_lvs=False,
        )
    ),
    "balanced": LibreLaneFlowPreset(
        name="Balanced Flow",
        description="Balanced between speed and quality",
        config=LibreLaneFlowConfig(
            design_name="example",
            verilog_files=["design.v"],
            pdk=PDKType.SKY130_HD,
            clock_period="10",
            pl_target_density="0.5",
            fp_core_util=50,
            run_drc=True,
            run_lvs=True,
        )
    ),
    "high_quality": LibreLaneFlowPreset(
        name="High Quality Flow",
        description="Maximum quality for tape-out ready designs",
        config=LibreLaneFlowConfig(
            design_name="example",
            verilog_files=["design.v"],
            pdk=PDKType.SKY130_HD,
            clock_period="5",
            pl_target_density="0.7",
            fp_core_util=70,
            drt_opt_iters=128,
            run_drc=True,
            run_lvs=True,
            run_magic_drc=True,
            run_klayout_drc=True,
            sta_pre_cts=True,
            sta_post_cts=True,
        )
    ),
}
