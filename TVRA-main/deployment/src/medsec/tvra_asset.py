from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from urllib.parse import unquote
from logger import get_logger

# Use stdout for logging when not in Docker container
try:
    LOGGER = get_logger('TVRA', '/proc/1/fd/1')
except PermissionError:
    LOGGER = get_logger('TVRA', '/dev/stdout')


@dataclass
class ControlSet:
    """Represents a control set from the TVRA model"""
    id: str
    kind: str  # e.g. "CSUsesNoEmail"
    base_class: str
    is_proposed: bool
    coverage_level: Optional[str]  # e.g. "High"
    tvra_asset: str  # Reference to parent asset
    
    @property
    def has_coverage_level(self) -> bool:
        """Check if control set has a valid coverage level"""
        return bool(self.coverage_level and self.coverage_level.strip())
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['ControlSet']:
        """Create ControlSet from dictionary data"""
        control_data = data.get("data", {})
        coverage_level = control_data.get("coverageLevel", "")
        return cls(
            id=data.get("id", ""),
            kind=control_data.get("kind", ""),
            base_class=control_data.get("base_Class", ""),
            is_proposed=control_data.get("isProposed", False),
            coverage_level=coverage_level,
            tvra_asset=control_data.get("tvraasset", "")
        )

@dataclass
class Misbehaviour:
    """Represents a misbehaviour from the TVRA model"""
    id: str
    kind: str  # e.g. "MSLossOfIntegrity"
    base_class: str
    level: Optional[str]  # e.g. "High"
    tvra_asset: str  # Reference to parent asset
    
    @property
    def has_level(self) -> bool:
        """Check if misbehaviour has a valid level"""
        return bool(self.level and self.level.strip())
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['Misbehaviour']:
        """Create Misbehaviour from dictionary data"""
        misb_data = data.get("data", {})
        level = misb_data.get("level", "")
        return cls(
            id=data.get("id", ""),
            kind=misb_data.get("kind", ""),
            base_class=misb_data.get("base_Class", ""),
            level=level,
            tvra_asset=misb_data.get("tvraasset", "")
        )

@dataclass
class TrustworthinessAttributeSet:
    """Represents a trustworthiness attribute set from the TVRA model"""
    id: str
    base_class: str
    kind: str  # e.g. "TWASAvailability"
    trustworthiness_level: Optional[str]  # e.g. "VeryHigh"
    tvra_asset: str  # Reference to parent asset
    
    @property
    def has_level(self) -> bool:
        """Check if trustworthiness attribute has a valid level"""
        return bool(self.trustworthiness_level and self.trustworthiness_level.strip())
    
    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrustworthinessAttributeSet']:
        """Create TrustworthinessAttributeSet from dictionary data"""
        twas_data = data.get("data", {})
        level = twas_data.get("trustworthinessLevel", "")
        return cls(
            id=data.get("id", ""),
            base_class=twas_data.get("base_Class", ""),
            kind=twas_data.get("kind", ""),
            trustworthiness_level=level,
            tvra_asset=twas_data.get("tvraasset", "")
        )

@dataclass
class TVRAAsset:
    """Represents a TVRA Asset from the JSON model"""
    id: str
    base_class: str  # e.g. "/0/Patient"
    kind: str  # e.g. "Adult"
    name: str  # Extracted from base_class
    misbehaviours: List[str]  # List of indices
    trustworthiness_attributesets: List[str]  # List of indices  
    controlsets: List[str]  # List of indices
    
    # Resolved references
    resolved_misbehaviours: List[Misbehaviour]
    resolved_twas: List[TrustworthinessAttributeSet]
    resolved_controls: List[ControlSet]

    @classmethod
    def from_dict(cls, data: dict) -> 'TVRAAsset':
        """Create TVRAAsset from dictionary data"""
        asset_data = data.get("data", {})
        base_class = asset_data.get("base_Class", "")
        name = base_class.split("/")[-1] if base_class else ""
        
        return cls(
            id=data.get("id", ""),
            base_class=base_class,
            kind=asset_data.get("kind", ""),
            name=name.replace("%20", " "),
            misbehaviours=asset_data.get("misbehaviours", []),
            trustworthiness_attributesets=asset_data.get("trustworthinessattributesets", []),
            controlsets=asset_data.get("controlsets", []),
            resolved_misbehaviours=[],
            resolved_twas=[],
            resolved_controls=[]
        )

@dataclass
class NetworkDomain:
    """Represents a connection between two assets"""
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name.replace("%20", " ") if name else ""  # Handle %20 on creation
        self.kind = ""  # TVRA kind that can be mapped
        self.source_name = ""  # Name extracted from source end
        self.target_name = ""  # Name extracted from target end
        self.source_type = ""  # Full path to source type
        self.target_type = ""  # Full path to target type
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkDomain':
        """Create NetworkDomain from dictionary data"""
        item_data = data.get("data", {})
        domain = cls(
            id=data.get("id", ""),
            name=item_data.get("name", "")  # %20 handled in __init__
        )
        
        # Get member ends and navigable end
        member_ends = item_data.get("memberEnd", [])
        navigable_end = item_data.get("navigableOwnedEnd", [])[0] if item_data.get("navigableOwnedEnd") else None
        owned_ends = item_data.get("ownedEnd", [])
        
        if len(member_ends) == 2 and navigable_end and len(owned_ends) == 2:
            # Create a map from member end paths to the actual type paths from ownedEnd
            member_to_type_map = {}
            member_to_name_map = {}
            
            for owned_end in owned_ends:
                end_data = owned_end.get("data", {})
                end_name = end_data.get("name", "")
                end_type = end_data.get("type", "")
                # Map from the association path (like "/0/manages/patient") to the type path (like "/0/Patient")
                association_path = end_data.get("association", "") + "/" + end_name.replace(" ", "%20")
                member_to_type_map[association_path] = end_type
                member_to_name_map[association_path] = end_name
            
            # The navigable end is the target, the other end is the source
            if member_ends[0] == navigable_end:
                # First member is target, second is source
                source_end = member_ends[1]
                target_end = member_ends[0]
            else:
                # Second member is target, first is source
                source_end = member_ends[0]
                target_end = member_ends[1]
            
            # Get the actual type paths and names using the member end paths
            domain.source_type = member_to_type_map.get(source_end, "")
            domain.target_type = member_to_type_map.get(target_end, "")
            # Extract asset names from type paths and URL-decode them
            import urllib.parse
            domain.source_name = urllib.parse.unquote(domain.source_type.split("/")[-1]) if domain.source_type else ""
            domain.target_name = urllib.parse.unquote(domain.target_type.split("/")[-1]) if domain.target_type else ""
                    
        return domain

    def get_from_asset(self) -> str:
        """Get the source asset name"""
        return self.source_name

    def get_to_asset(self) -> str:
        """Get the target asset name"""
        return self.target_name

    def get_source_type_name(self) -> str:
        """Get the source type name without path"""
        return self.source_type.split("/")[-1] if self.source_type else ""
        
    def get_target_type_name(self) -> str:
        """Get the target type name without path"""
        return self.target_type.split("/")[-1] if self.target_type else "" 
