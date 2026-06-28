src/
├── dashboard/
│   ├── app.js
│   ├── index.html
│   └── style.css
│
├── network/
│   ├── telemetry_server.py
│   ├── websocket.py
│   ├── frame_processor.py
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
│   │   ├── ep_recovery_strategy.py
│   │   └── hp_recovery_strategy.py
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
attack_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/combat/attack_strategy.py
combat_evaluator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/combat/combat_evaluator.py
retreat_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/combat/retreat_strategy.py
target_selector.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/combat/target_selector.py
win_probability.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/combat/win_probability.py

ai>inventory>
hp_recovery_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/hp_recovery_strategy.py
ep_recovery_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/ep_recovery_strategy.py
equip_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/equip_strategy.py
inventory_evaluator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/inventory_evaluator.py
loot_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/loot_strategy.py
weapon_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/inventory/weapon_strategy.py

ai>memory>
world_model.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/memory/world_model.py

ai>movement>
exploration_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/movement/exploration_strategy.py
movement_evaluator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/movement/movement_evaluator.py
path_scoring.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/movement/path_scoring.py
zone_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/movement/zone_strategy.py

ai>strategy>
early_game.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/strategy/early_game.py
goal_selector.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/strategy/goal_selector.py
late_game.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/strategy/late_game.py
mid_game.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/strategy/mid_game.py

ai>survival> 
danger_calculator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/survival/danger_calculator.py
healing_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/survival/healing_strategy.py
storm_strategy.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/survival/storm_strategy.py
survival_evaluator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/survival/survival_evaluator.py

ai>action_selector.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/action_selector.py
ai>brain.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/brain.py
ai>evaluator.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/evaluator.py
ai>planner.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/ai/planner.py

config>constants.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/config/constants.py

models>action.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/models/action.py
models>entities.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/models/entities.py
models>game_state.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/models/game_state.py

network>api.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/network/api.py
network>gui_logger.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/network/gui_logger.py
network>websocket.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/network/websocket.py
network>frame_processor.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/network/frame_processor.py
telemetry_server.py https://github.com/Vdreamland/moltygamesbots/blob/main/src/network/telemetry_server.py

readment.txt https://github.com/Vdreamland/moltygamesbots/blob/main/readment.txt
.env https://github.com/Vdreamland/moltygamesbots/blob/main/.env
run.py https://github.com/Vdreamland/moltygamesbots/blob/main/run.py

Dokumentasi resmi
PlayGuide https://www.clawroyale.ai/guide
GameGuide https://www.clawroyale.ai/game-guide
Doccumentation https://www.clawroyale.ai/docs
PreSesion Guide https://www.clawroyale.ai/pack-catalog
Patch Notes https://www.clawroyale.ai/news?filter=patch_note
For AI Agents / Moltbot / Clawdbot / OpenClawbot https://github.com/Vdreamland/moltygamesbots/blob/main/skill.md

Dashboard >
index.html https://github.com/Vdreamland/moltygamesbots/blob/main/dashboard/index.html
app.js https://github.com/Vdreamland/moltygamesbots/blob/main/dashboard/app.js
style.css https://github.com/Vdreamland/moltygamesbots/blob/main/dashboard/style.css