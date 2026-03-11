"""Tests for LayeredMemory path overrides and simple layer compatibility."""

import json

from src.core.memory_layers import LayeredMemory, MemoryLayer


class TestLayeredMemoryCompatibility:
    def test_simple_layer_round_trip_uses_flat_json(self, tmp_path):
        user_path = tmp_path / "memory.json"
        memory = LayeredMemory(
            storage_dir=tmp_path / "layers",
            layer_paths={MemoryLayer.USER: user_path},
            simple_layers={MemoryLayer.USER},
        )

        memory.set("role", "engineer", layer=MemoryLayer.USER)

        saved = json.loads(user_path.read_text(encoding="utf-8"))
        assert saved == {"role": "engineer"}

    def test_simple_layer_loads_legacy_flat_json(self, tmp_path):
        user_path = tmp_path / "memory.json"
        user_path.write_text(json.dumps({"name": "Ada"}), encoding="utf-8")

        memory = LayeredMemory(
            storage_dir=tmp_path / "layers",
            layer_paths={MemoryLayer.USER: user_path},
            simple_layers={MemoryLayer.USER},
        )

        assert memory.get("name", layer=MemoryLayer.USER) == "Ada"
