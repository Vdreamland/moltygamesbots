"""
src/models/entities.py
Tanggung jawab: Representasi entitas game (Player, Enemy, Region, Item, Weapon, Potion, Armor, Ruin)
dan parser data tangguh yang memisahkan pembacaan Type Luar dan Nama Dalam Bersarang
serta melakukan parsing data taktis dengan Type-Safe checking.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

def safe_int(value: Any, default: int = 0) -> int:
    """[REVISI AUDIT]: Fail-safe type checking untuk parsing data integer."""
    try:
        if value is None:
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

@dataclass
class Item:
    id: str
    name: str
    type: str # weapon, recovery_hp, recovery_ep, relic, utility, armor
    tier: int
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        if not data:
            return cls(id="", name="Unknown Item", type="utility", tier=1)
        
        nested_item = data.get("item")
        source_name = nested_item if isinstance(nested_item, dict) else data
        
        outer_type = str(data.get("type", "utility")).lower()
        inner_type = str(source_name.get("type", outer_type)).lower()
        
        if "weapon" in [outer_type, inner_type]:
            resolved_type = "weapon"
        elif "armor" in [outer_type, inner_type]:
            resolved_type = "armor"
        elif "recovery_hp" in [outer_type, inner_type]:
            resolved_type = "recovery_hp"
        elif "recovery_ep" in [outer_type, inner_type]:
            resolved_type = "recovery_ep"
        else:
            resolved_type = outer_type
        
        return cls(
            id=data.get("id", source_name.get("id", "")),
            name=source_name.get("name", "Unknown Item"),
            type=resolved_type,
            tier=safe_int(source_name.get("tier", data.get("tier", 1)), 1),
            raw_data=data
        )


@dataclass
class Weapon(Item):
    damage: int = 0
    range: int = 1
    ep_cost: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Weapon":
        if not data:
            return cls(id="", name="Fists", type="weapon", tier=0, damage=5, range=1, ep_cost=1)
        
        nested_item = data.get("item")
        source_name = nested_item if isinstance(nested_item, dict) else data
        stats = source_name.get("stats", data.get("stats", {})) or {}
        
        return cls(
            id=data.get("id", source_name.get("id", "")),
            name=source_name.get("name", "Fists"),
            type="weapon",
            tier=safe_int(source_name.get("tier", data.get("tier", 1)), 1),
            damage=safe_int(stats.get("damage", data.get("damage", 5)), 5),
            range=safe_int(stats.get("range", data.get("range", 1)), 1),
            ep_cost=safe_int(stats.get("epCost", data.get("ep_cost", 1)), 1),
            raw_data=data
        )


@dataclass
class Armor(Item):
    defense: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Armor":
        if not data:
            return cls(id="", name="Tattered Clothes", type="armor", tier=0, defense=0)
        
        nested_item = data.get("item")
        source_name = nested_item if isinstance(nested_item, dict) else data
        stats = source_name.get("stats", data.get("stats", {})) or {}
        
        return cls(
            id=data.get("id", source_name.get("id", "")),
            name=source_name.get("name", "Armor"),
            type="armor",
            tier=safe_int(source_name.get("tier", data.get("tier", 1)), 1),
            defense=safe_int(stats.get("defense", source_name.get("defense", 5)), 5),
            raw_data=data
        )


@dataclass
class Potion(Item):
    recovery_type: str = "hp"
    recovery_amount: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Potion":
        if not data:
            return cls(id="", name="Empty Vial", type="recovery_hp", tier=1)
        
        nested_item = data.get("item")
        source_name = nested_item if isinstance(nested_item, dict) else data
        stats = source_name.get("stats", {}) or {}
        iname = str(source_name.get("name", "")).lower()
        
        is_ep = any(keyword in iname for keyword in ["food", "smoltz", "snack", "energy", "candy", "soda", "potion_ep"])
        rec_type = "ep" if is_ep else "hp"
        
        default_amount = 30 if "bandage" in iname else (50 if "medkit" in iname else 30)
        amount = safe_int(stats.get("recoveryAmount", source_name.get("recovery_amount", default_amount)), default_amount)
        
        return cls(
            id=data.get("id", source_name.get("id", "")),
            name=source_name.get("name", "Potion"),
            type=str(data.get("type", "recovery_hp")).lower(),
            tier=safe_int(source_name.get("tier", data.get("tier", 1)), 1),
            recovery_type=rec_type,
            recovery_amount=amount,
            raw_data=data
        )


@dataclass
class Ruin:
    ruin_id: str
    is_empty: bool
    gauge: int
    max_gauge: int
    content_type: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ruin":
        if not data:
            return cls(ruin_id="", is_empty=True, gauge=0, max_gauge=100, content_type="none")
        return cls(
            ruin_id=data.get("ruinId", data.get("id", "")),
            is_empty=bool(data.get("isEmpty", True)),
            gauge=safe_int(data.get("gauge", 0)),
            max_gauge=safe_int(data.get("maxGauge", 100), 100),
            content_type=data.get("contentType", "none")
        )


@dataclass
class Region:
    id: str
    name: str
    is_death_zone: bool
    connections: List[str] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    ruin_gauge: int = 0
    ruin_occupant: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Region":
        if not data:
            return cls(id="", name="Unknown Region", is_death_zone=True)
        
        raw_items = data.get("items", []) or []
        parsed_items = []
        for item_data in raw_items:
            nested_item = item_data.get("item")
            source_name = nested_item if isinstance(nested_item, dict) else item_data
            
            outer_type = str(item_data.get("type", "")).lower()
            inner_type = str(source_name.get("type", outer_type)).lower() if isinstance(nested_item, dict) else outer_type
            
            if "weapon" in [outer_type, inner_type]:
                itype = "weapon"
            elif "armor" in [outer_type, inner_type]:
                itype = "armor"
            elif "recovery_hp" in [outer_type, inner_type]:
                itype = "recovery_hp"
            elif "recovery_ep" in [outer_type, inner_type]:
                itype = "recovery_ep"
            else:
                itype = outer_type
            
            iname = str(source_name.get("name", "")).lower()
            
            is_weapon_by_name = any(keyword in iname for keyword in ["sword", "dagger", "knife", "pistol", "rifle", "axe", "bow", "spear"])
            is_armor_by_name = any(keyword in iname for keyword in ["armor", "chainmail", "plate", "shield", "helmet", "vest"])
            is_hp_recovery = any(keyword in iname for keyword in ["bandage", "medkit", "medical", "first-aid", "potion_hp"])
            is_ep_recovery = any(keyword in iname for keyword in ["food", "smoltz", "snack", "energy", "candy", "soda", "potion_ep"])

            if itype == "weapon" or is_weapon_by_name:
                parsed_items.append(Weapon.from_dict(item_data))
            elif itype == "armor" or is_armor_by_name:
                parsed_items.append(Armor.from_dict(item_data))
            elif "recovery_hp" in itype or is_hp_recovery:
                parsed_items.append(Potion.from_dict(item_data))
            elif "recovery_ep" in itype or is_ep_recovery:
                parsed_items.append(Potion.from_dict(item_data))
            else:
                parsed_items.append(Item.from_dict(item_data))

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown Region"),
            is_death_zone=bool(data.get("isDeathZone", False)),
            connections=data.get("connections", []) or [],
            items=parsed_items,
            ruin_gauge=safe_int(data.get("ruinGauge", 0)),
            ruin_occupant=data.get("ruinOccupant")
        )


@dataclass
class Agent:
    id: str
    name: str
    hp: int
    max_hp: int
    ep: int
    max_ep: int
    alert_gauge: int
    alert_active: bool
    equipped_weapon: Optional[Weapon] = None
    equipped_armor: Optional[Armor] = None
    inventory: List[Item] = field(default_factory=list)
    is_alive: bool = True
    region_id: str = ""
    kills: int = 0 
    defense: int = 0 

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        if not data:
            return cls(id="", name="Unknown", hp=0, max_hp=100, ep=0, max_ep=100, alert_gauge=0, alert_active=False)
        
        raw_weapon = data.get("equippedWeapon")
        parsed_weapon = Weapon.from_dict(raw_weapon) if raw_weapon else None

        raw_armor = data.get("equippedArmor")
        parsed_armor = Armor.from_dict(raw_armor) if raw_armor else None

        raw_inv = data.get("inventory", []) or []
        parsed_inventory = []
        for item_data in raw_inv:
            nested_item = item_data.get("item")
            source_name = nested_item if isinstance(nested_item, dict) else item_data
            
            outer_type = str(item_data.get("type", "")).lower()
            inner_type = str(source_name.get("type", outer_type)).lower() if isinstance(nested_item, dict) else outer_type
            
            if "weapon" in [outer_type, inner_type]:
                itype = "weapon"
            elif "armor" in [outer_type, inner_type]:
                itype = "armor"
            elif "recovery_hp" in [outer_type, inner_type]:
                itype = "recovery_hp"
            elif "recovery_ep" in [outer_type, inner_type]:
                itype = "recovery_ep"
            else:
                itype = outer_type
            
            iname = str(source_name.get("name", "")).lower()
            
            is_weapon_by_name = any(keyword in iname for keyword in ["sword", "dagger", "knife", "pistol", "rifle", "axe", "bow", "spear"])
            is_armor_by_name = any(keyword in iname for keyword in ["armor", "chainmail", "plate", "shield", "helmet", "vest"])
            is_hp_recovery = any(keyword in iname for keyword in ["bandage", "medkit", "medical", "first-aid", "potion_hp"])
            is_ep_recovery = any(keyword in iname for keyword in ["food", "smoltz", "snack", "energy", "candy", "soda", "potion_ep"])

            if itype == "weapon" or is_weapon_by_name:
                parsed_inventory.append(Weapon.from_dict(item_data))
            elif itype == "armor" or is_armor_by_name:
                parsed_inventory.append(Armor.from_dict(item_data))
            elif "recovery_hp" in itype or is_hp_recovery:
                parsed_inventory.append(Potion.from_dict(item_data))
            elif "recovery_ep" in itype or is_ep_recovery:
                parsed_inventory.append(Potion.from_dict(item_data))
            else:
                parsed_inventory.append(Item.from_dict(item_data))

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Agent"),
            hp=safe_int(data.get("hp", 0)),
            max_hp=safe_int(data.get("maxHp", 100), 100),
            ep=safe_int(data.get("ep", 0)),
            max_ep=safe_int(data.get("maxEp", 100), 100),
            alert_gauge=safe_int(data.get("alertGauge", 0)),
            alert_active=bool(data.get("alertActive", False)),
            equipped_weapon=parsed_weapon,
            equipped_armor=parsed_armor,
            inventory=parsed_inventory,
            is_alive=bool(data.get("isAlive", True)),
            region_id=data.get("regionId", ""),
            kills=safe_int(data.get("kills", 0)),
            defense=safe_int(data.get("defense", 0))
        )