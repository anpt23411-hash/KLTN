"""Regression checks against saved report artifacts; no model training."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import pandas as pd

from src.export_chapter4 import export
from src.verify_chapter4 import verify


ROOT = Path(__file__).resolve().parents[1]


class Chapter4ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = sorted(p.parent for p in (ROOT / 'reports').glob('chapter4_export_*/manifest.json'))
        if not candidates:
            raise unittest.SkipTest('Run src.export_chapter4 first to generate saved report fixtures')
        cls.source = candidates[-1]

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name) / 'report'
        shutil.copytree(self.source, self.folder)

    def update_hash(self, relative):
        path = self.folder / 'manifest.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        for item in manifest['outputs']:
            if item['path'] == relative:
                item['sha256'] = hashlib.sha256((self.folder / relative).read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest), encoding='utf-8')

    def test_saved_report_passes_without_training(self):
        self.assertEqual(verify(self.folder)['status'], 'passed')

    def test_corrupted_csv_is_rejected(self):
        with (self.folder / 'tables' / 'benchmark.csv').open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            verify(self.folder)

    def test_wrong_metric_rejected_even_if_hash_is_updated(self):
        relative = 'tables/metrics_two_thresholds.csv'
        data = pd.read_csv(self.folder / relative)
        data.loc[0, 'average_precision'] = .123
        data.to_csv(self.folder / relative, index=False)
        self.update_hash(relative)
        with self.assertRaises(AssertionError):
            verify(self.folder)

    def test_missing_svg_is_rejected(self):
        next((self.folder / 'figures').glob('*.svg')).unlink()
        with self.assertRaisesRegex(ValueError, 'Missing output'):
            verify(self.folder)

    def test_existing_output_is_preserved(self):
        before = (self.folder / 'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            export(ROOT / 'thesis_config.json', self.folder)
        self.assertEqual(before, (self.folder / 'manifest.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
