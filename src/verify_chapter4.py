"""Verify an exported Chapter 4 report without fitting or predicting any model."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import numpy as np
import pandas as pd

from .evaluation import evaluate


def require(condition, message):
    if not condition:
        raise ValueError(message)


def png_dpi(path):
    """Read PNG physical resolution directly, without an optional Pillow dependency."""
    with path.open('rb') as stream:
        require(stream.read(8) == b'\x89PNG\r\n\x1a\n', f'Invalid PNG: {path}')
        while True:
            header = stream.read(8)
            if len(header) != 8:
                raise ValueError(f'PNG has no physical resolution: {path}')
            length, kind = struct.unpack('>I4s', header)
            data = stream.read(length)
            stream.read(4)
            if kind == b'pHYs':
                x, y, unit = struct.unpack('>IIB', data)
                require(unit == 1, f'PNG resolution unit is not metre: {path}')
                return x * .0254, y * .0254
            require(kind != b'IEND', f'PNG has no physical resolution: {path}')


def verify(folder, root=None):
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    for item in manifest['outputs']:
        path = (folder / item['path']).resolve()
        require(folder in path.parents, f'Output path escapes export directory: {item["path"]}')
        require(path.is_file(), f'Missing output: {item["path"]}')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Output hash mismatch: {item["path"]}')
    if root is not None:
        root = Path(root).resolve()
        for item in manifest['inputs']:
            path = (root / item['path']).resolve()
            require(root in path.parents, f'Input path escapes project directory: {item["path"]}')
            require(path.is_file(), f'Missing input: {item["path"]}')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], f'Input changed since export: {item["path"]}')
    images = list((folder / 'figures').glob('*.png'))
    require(len(images) == manifest['counts']['figures'], 'Figure count mismatch')
    require(len(list((folder / 'tables').glob('*.csv'))) == manifest['counts']['tables'], 'Table count mismatch')
    for path in images:
        require(path.with_suffix('.svg').is_file(), f'Missing SVG: {path.stem}')
        require(all(abs(value-300) < .1 for value in png_dpi(path)), f'PNG is not 300 dpi: {path.name}')
    for name in ['BAO_CAO_THUC_NGHIEM.md', 'DANH_MUC_BANG_HINH.md', 'DU_LIEU_CON_THIEU.md']:
        require((folder / name).is_file(), f'Missing required document: {name}')
        for ref in re.findall(r'\]\(([^)]+)\)', (folder / name).read_text(encoding='utf-8')):
            if ref.startswith(('https://', 'http://', '#')):
                continue
            require((folder / ref).is_file(), f'Broken relative link in {name}: {ref}')
    data = {scope: pd.read_csv(folder / 'tables' / f'source_predictions_{scope}.csv') for scope in ['oof', 'holdout']}
    require(not set(data['oof'].row_reference) & set(data['holdout'].row_reference), 'OOF and holdout overlap')
    exported_metrics = pd.read_csv(folder / 'tables' / 'metrics_two_thresholds.csv')
    require(len(exported_metrics) == 4, 'Expected two thresholds for each prediction scope')
    for scope, pred in data.items():
        require(pred.row_reference.is_unique, f'Duplicate prediction references: {scope}')
        rows = exported_metrics[exported_metrics.tap == scope]
        require(len(rows) == 2, f'Expected two thresholds: {scope}')
        np.testing.assert_allclose(sorted(rows.nguong), sorted([.5, manifest['model_selection']['threshold']]), atol=1e-14)
        for row in rows.to_dict('records'):
            require(row['n'] == len(pred), f'Prediction sample size mismatch: {scope}')
            values = evaluate(pred.observed_label, pred.probability, row['nguong'])
            for metric, value in values.items():
                np.testing.assert_allclose(row[metric], value, atol=1e-12, rtol=1e-10, err_msg=f'{scope}: {metric}')
            actual = pred.observed_label.to_numpy()
            guessed = pred.probability.to_numpy() >= row['nguong']
            for key, value in dict(TN=((actual == 0) & ~guessed).sum(), FP=((actual == 0) & guessed).sum(),
                                   FN=((actual == 1) & ~guessed).sum(), TP=((actual == 1) & guessed).sum()).items():
                require(row[key] == value, f'Confusion matrix mismatch: {scope}/{key}')
        np.testing.assert_array_equal(pred.score, np.minimum(10, 1+np.floor(10*pred.probability)).astype(int))
        for group, (lo, hi) in manifest['config']['risk_groups'].items():
            require((pred.risk_group.eq(group) == pred.score.between(lo, hi)).all(), f'Risk group mismatch: {scope}/{group}')
    require(not any(manifest[key] for key in ['retrained', 'prediction_rerun', 'bootstrap_rerun']), 'Export records additional model computation')
    return dict(status='passed', tables=manifest['counts']['tables'], figures=len(images),
                input_hashes_checked=root is not None, metrics_recomputed_from_saved_predictions=True,
                png_300_dpi=True, svg_pairs=True, relative_links=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder')
    parser.add_argument('--root', help='Also verify input hashes against this project root')
    args = parser.parse_args()
    print(json.dumps(verify(args.folder, args.root), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
