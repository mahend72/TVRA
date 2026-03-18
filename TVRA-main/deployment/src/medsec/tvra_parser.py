from typing import Dict, Any, Tuple
from tvra_asset import TVRAAsset, NetworkDomain, ControlSet, Misbehaviour, TrustworthinessAttributeSet
from logger import get_logger

# Use stdout for logging when not in Docker container
try:
    LOGGER = get_logger('TVRA', '/proc/1/fd/1')
except PermissionError:
    LOGGER = get_logger('TVRA', '/dev/stdout')



class TVRAParser:
    """Parser for TVRA JSON model files"""

    def __init__(self, json_data: Dict[str, Any]):
        self.json_data = json_data
        self.content = json_data.get("content", [])
        self.assets: Dict[str, TVRAAsset] = {}
        self.domains: Dict[str, NetworkDomain] = {}
        self.index_map: Dict[str, str] = {}
        self.misbehaviours: Dict[str, Misbehaviour] = {}
        self.control_sets: Dict[str, ControlSet] = {}
        self.twas: Dict[str, TrustworthinessAttributeSet] = {}
        # Add type mapping for easier debugging
        self.type_to_asset_map: Dict[str, str] = {}
        
        # NetworkDomain kind mapping dictionary - add more mappings as needed
        self.network_domain_kind_mapping = {
            'pollsSensor': 'polls',
            'viewsData': 'views',
        }
        
        # TVRAAsset kind mapping dictionary - add more mappings as needed
        self.tvra_asset_kind_mapping = {
        }

    def parse(self) -> Tuple[Dict[str, TVRAAsset], Dict[str, NetworkDomain]]:
        """Parse the JSON content and return assets and network domains"""
        LOGGER.debug("\n=== Starting TVRA Model Parsing ===")

        # Extract associations from the model
        self._extract_associations()

        # First pass: Build index map and parse assets
        self._parse_assets()

        # Second pass: Parse associations and other elements
        self._parse_other_elements()

        # Third pass: Resolve references
        LOGGER.debug("\n--- Third Pass: Resolving References ---")
        self._resolve_references()

        # Print summary
        self._print_summary()

        return self.assets, self.domains

    def map_network_domain_kind(self, input_kind: str) -> str:
        """
        Map input NetworkDomain kind to output kind using the network_domain_kind_mapping dictionary.
        If input_kind exists in mapping, return the mapped value.
        Otherwise, return the original input_kind.
        """
        mapped_kind = self.network_domain_kind_mapping.get(input_kind, input_kind)
        if mapped_kind != input_kind:
            LOGGER.debug(f"  Mapped NetworkDomain kind: '{input_kind}' -> '{mapped_kind}'")
        return mapped_kind

    def map_tvra_asset_kind(self, input_kind: str) -> str:
        """
        Map input TVRAAsset kind to output kind using the tvra_asset_kind_mapping dictionary.
        If input_kind exists in mapping, return the mapped value.
        Otherwise, return the original input_kind.
        
        Args:
            input_kind (str): The input kind value to map
            
        Returns:
            str: The mapped kind value or original if no mapping exists
        """
        mapped_kind = self.tvra_asset_kind_mapping.get(input_kind, input_kind)
        if mapped_kind != input_kind:
            LOGGER.debug(f"  Mapped TVRAAsset kind: '{input_kind}' -> '{mapped_kind}'")
        return mapped_kind

    def _extract_associations(self):
        """Extract all associations from the model and add them to content for processing"""
        model = next((item for item in self.content if item.get("eClass") == "uml:Model"), None)
        if model:
            packaged_elements = model.get("data", {}).get("packagedElement", [])
            LOGGER.debug(f"Found {len(packaged_elements)} packaged elements")

            # Add associations to content for processing
            for element in packaged_elements:
                if element.get("eClass") == "uml:Association":
                    self.content.append(element)

        LOGGER.debug(f"Total content elements after extracting associations: {len(self.content)}")

    def _parse_assets(self):
        """First pass: Build index map and parse TVRAAssets"""
        LOGGER.debug("\n--- First Pass: Building Index Map and Parsing Assets ---")
        for index, item in enumerate(self.content):
            eclass = item.get("eClass", "")
            item_id = item.get("id", "")
            self.index_map[str(index)] = item_id

            if eclass == "tvra:TVRAAsset":
                base_class = item.get("data", {}).get("base_Class", "")
                if base_class:
                    self.type_to_asset_map[base_class] = item_id
                asset = TVRAAsset.from_dict(item)
                
                # Apply kind mapping
                original_kind = asset.kind
                asset.kind = self.map_tvra_asset_kind(asset.kind)
                
                self.assets[item_id] = asset
                LOGGER.debug(f"Created TVRAAsset: {asset.name} (Kind: {asset.kind})")

    def _parse_other_elements(self):
        """Second pass: Parse associations and other elements"""
        LOGGER.debug("\n--- Second Pass: Parsing Associations and Other Elements ---")

        for item in self.content:
            eclass = item.get("eClass", "")
            item_id = item.get("id", "")

            if eclass == "tvra:NetworkDomain":
                self._parse_network_domain(item, item_id)
            elif eclass == "tvra:Misbehaviour":
                self._parse_misbehaviour(item, item_id)
            elif eclass == "tvra:ControlSet":
                self._parse_control_set(item, item_id)
            elif eclass == "tvra:TrustworthinessAttributeSet":
                self._parse_trustworthiness_attribute_set(item, item_id)

    def _parse_network_domain(self, item: Dict[str, Any], item_id: str):
        """Parse a NetworkDomain element"""
        LOGGER.debug(f"\nProcessing NetworkDomain {item_id}:")
        try:
            # Get the base association reference
            base_association = item.get("data", {}).get("base_Association", "")
            kind = item.get("data", {}).get("kind", "")

            # Find the corresponding uml:Association
            corresponding_association = self._find_corresponding_association(base_association)

            if corresponding_association:
                # Create NetworkDomain using the UML association data but with TVRA metadata
                domain = NetworkDomain.from_dict(corresponding_association)
                domain.id = item_id  # Use TVRA NetworkDomain ID
                
                # Keep the original name from UML association, but map the TVRA kind
                mapped_kind = self.map_network_domain_kind(kind)
                domain.kind = mapped_kind   # Set the mapped TVRA kind 
                
                self.domains[item_id] = domain

                LOGGER.debug(f"  Created NetworkDomain: {domain.name} (Kind: {domain.kind})")
                LOGGER.debug(f"  Source: {domain.source_name} ({domain.get_source_type_name()})")
                LOGGER.debug(f"  Target: {domain.target_name} ({domain.get_target_type_name()})")
                LOGGER.debug(f"  Source type path: {domain.source_type}")
                LOGGER.debug(f"  Target type path: {domain.target_type}")
            else:
                LOGGER.warning(f"  Could not find corresponding association for {base_association}")

        except Exception as e:
            LOGGER.error(f"  Failed to parse network domain {item_id}: {str(e)}")

    def _find_corresponding_association(self, base_association: str) -> Dict[str, Any]:
        """Find the corresponding uml:Association for a given base_association reference"""
        if base_association.startswith("/0/@packagedElement."):
            return self._find_by_packaged_element_path(base_association)
        else:
            return self._find_by_direct_path(base_association)

    def _find_by_packaged_element_path(self, base_association: str) -> Dict[str, Any]:
        """Find association by packaged element path reference"""
        for assoc_item in self.content:
            if assoc_item.get("eClass") == "uml:Association":
                member_ends = assoc_item.get("data", {}).get("memberEnd", [])
                for member_end in member_ends:
                    if member_end.startswith(base_association):
                        return assoc_item
        return None

    def _find_by_direct_path(self, base_association: str) -> Dict[str, Any]:
        """Find association by direct path match"""
        # First try: exact memberEnd path match
        result = self._find_by_exact_member_end_match(base_association)
        if result:
            return result

        # Second try: match by association name
        return self._find_by_association_name(base_association)

    def _find_by_exact_member_end_match(self, base_association: str) -> Dict[str, Any]:
        """Find association by exact memberEnd path match"""
        for assoc_item in self.content:
            if assoc_item.get("eClass") == "uml:Association":
                member_ends = assoc_item.get("data", {}).get("memberEnd", [])
                for member_end in member_ends:
                    if member_end.startswith(base_association + "/"):
                        return assoc_item
        return None

    def _find_by_association_name(self, base_association: str) -> Dict[str, Any]:
        """Find association by association name matching"""
        association_name = base_association.split("/")[-1] if base_association else ""
        # Handle numbered associations like "locatedIn.1" -> "locatedIn"
        if "." in association_name:
            association_name = association_name.split(".")[0]

        for assoc_item in self.content:
            if (assoc_item.get("eClass") == "uml:Association" and
                assoc_item.get("data", {}).get("name") == association_name):
                # For numbered associations, check if the memberEnd path matches
                if "." in base_association.split("/")[-1]:
                    member_ends = assoc_item.get("data", {}).get("memberEnd", [])
                    if any(member_end.startswith(base_association + "/") for member_end in member_ends):
                        return assoc_item
                else:
                    return assoc_item
        return None

    def _parse_misbehaviour(self, item: Dict[str, Any], item_id: str):
        """Parse a Misbehaviour element"""
        misb = Misbehaviour.from_dict(item)
        if not misb.has_level:
            # Set default level to Negligible when no level is specified
            misb.level = "Negligible"
            LOGGER.debug(f"  Set default level 'Negligible' for Misbehaviour: {misb.kind}")
        self.misbehaviours[item_id] = misb
        LOGGER.debug(f"  Created Misbehaviour: {misb.kind}")
        LOGGER.debug(f"  Level: {misb.level}")
        LOGGER.debug(f"  Asset ref: {misb.tvra_asset}")

    def _parse_control_set(self, item: Dict[str, Any], item_id: str):
        """Parse a ControlSet element"""
        ctrl = ControlSet.from_dict(item)
        if not ctrl.has_coverage_level:
            # Set default coverage level to VeryLow when no level is specified
            ctrl.coverage_level = "VeryLow"
            LOGGER.debug(f"  Set default coverage level 'VeryLow' for ControlSet: {ctrl.kind}")
        self.control_sets[item_id] = ctrl
        LOGGER.debug(f"  Created ControlSet: {ctrl.kind}")
        LOGGER.debug(f"  Proposed: {ctrl.is_proposed}")
        LOGGER.debug(f"  Coverage Level: {ctrl.coverage_level}")
        LOGGER.debug(f"  Asset ref: {ctrl.tvra_asset}")

    def _parse_trustworthiness_attribute_set(self, item: Dict[str, Any], item_id: str):
        """Parse a TrustworthinessAttributeSet element"""
        twa = TrustworthinessAttributeSet.from_dict(item)
        if not twa.has_level:
            # Set default trustworthiness level to VeryLow when no level is specified
            twa.trustworthiness_level = "VeryLow"
            LOGGER.debug(f"  Set default trustworthiness level 'VeryLow' for TWAS: {twa.kind}")
        self.twas[item_id] = twa
        LOGGER.debug(f"  Created TWAS: {twa.kind}")
        LOGGER.debug(f"  Level: {twa.trustworthiness_level}")
        LOGGER.debug(f"  Asset ref: {twa.tvra_asset}")

    def _print_summary(self):
        """Print parsing summary"""
        LOGGER.debug("\n=== Parsing Summary ===")
        LOGGER.debug(f"Assets created: {len(self.assets)}")
        LOGGER.debug(f"Associations created: {len(self.domains)}")
        for domain in self.domains.values():
            LOGGER.debug(f"  {domain.name}: {domain.get_from_asset()} -> {domain.get_to_asset()}")

    def _resolve_references(self):
        """Resolve index references to actual IDs"""
        LOGGER.debug("\nResolving references for each asset:")

        for asset in self.assets.values():
            LOGGER.debug(f"\nProcessing asset: {asset.name}")

            # Resolve misbehaviours
            LOGGER.debug("  Resolving misbehaviours:")
            for idx in asset.misbehaviours:
                resolved_id = self.index_map[idx.strip("/")]
                if resolved_id in self.misbehaviours:
                    asset.resolved_misbehaviours.append(self.misbehaviours[resolved_id])
                    LOGGER.debug(f"    Resolved {idx} -> {self.misbehaviours[resolved_id].kind}")
                else:
                    LOGGER.warning(f"    Failed to resolve misbehaviour {idx}")

            # Resolve trustworthiness attributes
            LOGGER.debug("  Resolving trustworthiness attributes:")
            for idx in asset.trustworthiness_attributesets:
                resolved_id = self.index_map[idx.strip("/")]
                if resolved_id in self.twas:
                    asset.resolved_twas.append(self.twas[resolved_id])
                    LOGGER.debug(f"    Resolved {idx} -> {self.twas[resolved_id].kind}")
                else:
                    LOGGER.warning(f"    Failed to resolve TWAS {idx}")

            # Resolve control sets
            LOGGER.debug("  Resolving control sets:")
            for idx in asset.controlsets:
                resolved_id = self.index_map[idx.strip("/")]
                if resolved_id in self.control_sets:
                    asset.resolved_controls.append(self.control_sets[resolved_id])
                    LOGGER.debug(f"    Resolved {idx} -> {self.control_sets[resolved_id].kind}")
                else:
                    LOGGER.warning(f"    Failed to resolve control set {idx}")

    def get_connection_counts(self) -> Dict[str, int]:
        """Count the number of connections (both incoming and outgoing) for each asset"""
        connection_counts = {}

        # Initialize counts
        for asset_id in self.assets:
            connection_counts[asset_id] = 0

        # Count both source and target connections from domains
        for domain in self.domains.values():
            source_type = domain.source_type
            target_type = domain.target_type

            # Find corresponding asset IDs
            source_asset_id = self.type_to_asset_map.get(source_type, "")
            target_asset_id = self.type_to_asset_map.get(target_type, "")

            # Count both source and target connections
            if source_asset_id:
                connection_counts[source_asset_id] = connection_counts.get(source_asset_id, 0) + 1
            if target_asset_id:
                connection_counts[target_asset_id] = connection_counts.get(target_asset_id, 0) + 1

        return connection_counts
