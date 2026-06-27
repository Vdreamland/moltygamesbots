"""
src/models/action.py
Tanggung jawab: Merepresentasikan seluruh perintah aksi yang diizinkan oleh game,
               memformat payload JSON standar, dan merekam narasi logika (thought).
"""

from typing import Dict, Any, Optional

class Action:
    def __init__(self, action_type: str, data: Optional[Dict[str, Any]] = None, thought: str = ""):
        self.action_type = action_type
        self.data = data or {}
        # Batasan resmi pemikiran AI: maksimal 700 karakter
        self.thought = thought[:700] if thought else ""

    def to_json(self) -> Dict[str, Any]:
        """
        Mengonversi objek aksi ke payload format resmi WebSocket.
        Format payload: { "type": "action", "data": { "type": "...", ... }, "thought": "..." }
        """
        payload = {
            "type": "action",
            "data": {
                "type": self.action_type,
                **self.data
            }
        }
        if self.thought:
            payload["thought"] = self.thought
        return payload

    def __repr__(self) -> str:
        return f"Action(type={self.action_type}, data={self.data}, thought_len={len(self.thought)})"


# Helper subclass untuk mempermudah pembuatan aksi taktis dengan autocompletion
class MoveAction(Action):
    def __init__(self, region_id: str, thought: str = ""):
        super().__init__("move", {"regionId": region_id}, thought)

class ExploreAction(Action):
    def __init__(self, thought: str = ""):
        super().__init__("explore", {}, thought)

class AttackAction(Action):
    def __init__(self, target_id: str, thought: str = ""):
        super().__init__("attack", {"targetId": target_id}, thought)

class UseItemAction(Action):
    def __init__(self, item_id: str, thought: str = ""):
        super().__init__("use_item", {"itemId": item_id}, thought)

class InteractAction(Action):
    def __init__(self, thought: str = ""):
        super().__init__("interact", {}, thought)

class RestAction(Action):
    def __init__(self, thought: str = ""):
        super().__init__("rest", {}, thought)

class PickupAction(Action):
    def __init__(self, item_id: str, thought: str = ""):
        super().__init__("pickup", {"itemId": item_id}, thought)

class EquipAction(Action):
    def __init__(self, item_id: str, thought: str = ""):
        super().__init__("equip", {"itemId": item_id}, thought)