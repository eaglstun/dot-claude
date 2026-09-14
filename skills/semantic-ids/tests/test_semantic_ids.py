import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "semantic_ids.py"
SPEC = importlib.util.spec_from_file_location("semantic_ids", SCRIPT)
semantic_ids = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(semantic_ids)


class SemanticIDTests(unittest.TestCase):
    def test_base64_round_trip_uses_all_192_bits(self):
        value = (1 << semantic_ids.SEMANTIC_BITS) - 1
        encoded = semantic_ids.encode64(value)
        self.assertEqual(len(encoded), 32)
        self.assertEqual(semantic_ids.decode64(encoded), value)
        self.assertEqual(semantic_ids.SEMANTIC_BITS, 192)

    def test_mint_is_versioned_and_deterministic(self):
        vector = [1.0, -2.0, 3.0, -4.0]
        origin = [0.0] * len(vector)
        first = semantic_ids.mint(vector, origin)
        self.assertEqual(first, semantic_ids.mint(vector, origin))
        self.assertTrue(first.startswith("v2:"))
        self.assertEqual(len(first), 35)

    def test_v2_hamming_counts_the_last_bit(self):
        zero = "v2:" + semantic_ids.encode64(0)
        one = "v2:" + semantic_ids.encode64(1)
        self.assertEqual(semantic_ids.hamming(zero, one), 1)

    def test_cross_version_comparison_is_rejected(self):
        legacy = semantic_ids.encode64(0)
        current = "v2:" + semantic_ids.encode64(0)
        with self.assertRaises(ValueError):
            semantic_ids.hamming(legacy, current)

    def test_calibration_suite_is_broad(self):
        text = " ".join(semantic_ids.CALIBRATION_TEXTS).lower()
        for domain in ("software", "medicine", "family", "religion", "music", "sports"):
            self.assertIn(domain, text)
        self.assertGreaterEqual(len(semantic_ids.CALIBRATION_TEXTS), 60)

    def test_mint_builds_v2_index_without_a_mean_file(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            docs = root / "docs"
            data = root / "data"
            docs.mkdir()
            for name in ("alpha", "beta"):
                (docs / f"{name}.md").write_text(
                    f"---\nname: {name}\ndescription: {name} reference material\n---\n"
                )
            cfg = {
                "_name": "test",
                "_path": root / "context.toml",
                "_data": data,
                "embed_model": "test-model",
                "related_count": 1,
                "related_max_distance": 192,
                "source": [{
                    "name": "docs",
                    "_root": docs,
                    "glob": "*.md",
                    "frontmatter": "yaml",
                    "title_field": "name",
                    "summary_field": "description",
                    "stamp": False,
                }],
            }

            def fake_embed(_cfg, texts, **_kwargs):
                return [[((i + 1) * (j + 3) % 17) / 17 for j in range(12)]
                        for i, _ in enumerate(texts)]

            with patch.object(semantic_ids, "embed", side_effect=fake_embed):
                semantic_ids.cmd_mint(cfg, SimpleNamespace(force=False, dry_run=False))

            payload = json.loads((data / "test.index.json").read_text())
            self.assertEqual(payload["id_version"], "v2")
            self.assertEqual(payload["semantic_bits"], 192)
            self.assertTrue(all(d["id"].startswith("v2:") for d in payload["docs"]))
            self.assertFalse((data / "test.mean.json").exists())


if __name__ == "__main__":
    unittest.main()
