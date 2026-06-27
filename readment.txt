src/
│
├── network/
│   ├── websocket.py
│   ├── gui_logger.py
│   └── api.py
│
├── models/
│   ├── game_state.py
│   ├── entities.py
│   └── action.py
│
├── ai/
│   ├── brain.py
│   ├── action_selector.py
│   ├── planner.py
│   ├── evaluator.py
│   │
│   ├── combat/
│   │   ├── combat_evaluator.py
│   │   ├── attack_strategy.py
│   │   ├── retreat_strategy.py
│   │   ├── target_selector.py
│   │   └── win_probability.py
│   │
│   ├── movement/
│   │   ├── movement_evaluator.py
│   │   ├── exploration_strategy.py
│   │   ├── zone_strategy.py
│   │   └── path_scoring.py
│   │
│   ├── inventory/
│   │   ├── inventory_evaluator.py
│   │   ├── loot_strategy.py
│   │   ├── equip_strategy.py
│   │   ├── weapon_strategy.py
│   │   └── consumable_strategy.py
│   │
│   ├── survival/
│   │   ├── survival_evaluator.py
│   │   ├── danger_calculator.py
│   │   ├── storm_strategy.py
│   │   └── healing_strategy.py
│   │
│   ├── strategy/
│   │   ├── early_game.py
│   │   ├── mid_game.py
│   │   ├── late_game.py
│   │   └── goal_selector.py
│   │
│   └── memory/
│       └── world_model.py
│
├── config/
│   └── constants.py
│
└── run.py


link url

ai>combat>
attack_strategy.py
combat_evaluator.py
retreat_strategy.py
target_selector.py
win_probability.py

ai>inventory>
consumable_strategy.py
equip_strategy.py
inventory_evaluator.py
loot_strategy.py
weapon_strategy.py

ai>memory>
world_model.py

ai>movement>
exploration_strategy.py
movement_evaluator.py
path_scoring.py
zone_strategy.py

ai>strategy>
early_game.py
goal_selector.py
late_game.py
mid_game.py

ai>survival>
danger_calculator.py
healing_strategy.py
storm_strategy.py
survival_evaluator.py

ai>action_selector.py
ai>brain.py
ai>evaluator.py
ai>planner.py

config>constants.py

models>action.py
models>entities.py
models>game_state.py

network>api.py
network>gui_logger.py
network>websocket.py

.env
run.py
