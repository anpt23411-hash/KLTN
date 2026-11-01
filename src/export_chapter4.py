"""Read-only Chapter 4 export. Never loads estimators or calls training/prediction."""
import argparse
import base64
from datetime import datetime
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import metrics

from .evaluation import evaluate
from .thesis_summary import markdown_table


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(config_path, output=None):
    config_path = Path(config_path).resolve()
    root = config_path.parent
    config = json.loads(config_path.read_text(encoding='utf-8'))
    source = (root / config['report_dir']).resolve()
    now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
    out = Path(output).resolve() if output else root / 'reports' / ('chapter4_export_' + now.strftime('%Y%m%d_%H%M%S_%f'))
    protected = [source, (root / config['model_dir']).resolve(), (root / 'data').resolve()]
    if any(out == p or p in out.parents for p in protected):
        raise ValueError('Output must be outside source artifact/data/model directories')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'figures').mkdir()
    (out / 'tables').mkdir()
    inputs = list(source.rglob('*')) + list((root / config['model_dir']).glob('*'))
    inputs += list((root / 'src').glob('*.py')) + [config_path, root / config['data_path']]
    inputs = sorted(set(p.resolve() for p in inputs if p.is_file()))
    hashes = {str(p.relative_to(root)).replace('\\', '/'): digest(p) for p in inputs}
    def read(name):
        return pd.read_csv(source / name)
    def js(name):
        return json.loads((source / name).read_text(encoding='utf-8'))
    audit, split, selection = js('data_audit.json'), js('split_manifest.json'), js('selection.json')
    assert config == js('config_snapshot.json'), 'Configuration differs from saved run'
    assert digest(root / config['data_path']) == audit['raw_sha256']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .2,
                         'axes.prop_cycle': matplotlib.cycler(color=['#176b87', '#d17a22', '#52854c', '#915b94']),
                         'svg.fonttype': 'none'})
    sections = ['# Báo cáo thực nghiệm học máy — Chương 4', '',
        f'Xuất lúc {now.isoformat()}. Chỉ đọc artifact đã lưu; không huấn luyện, không dự đoán lại hoặc thay đổi quyết định.',
        'Nguồn chính: `reports/thesis_run/`; không trộn kết quả pilot ở `reports/`.',
        'Churn quan sát trong báo cáo là nhãn kỹ thuật 1; ngữ nghĩa nghiệp vụ chưa được xác minh đầy đủ. '
        'Holdout đã được quan sát ở pilot, không phải tập kiểm định hoàn toàn mới. OOF là chẩn đoán lựa chọn trên train, có thiên lệch lựa chọn.', '']
    catalog = []
    def table(name, title, data, origin, position, show=True):
        path = 'tables/' + name + '.csv'
        data.to_csv(out / path, index=False, encoding='utf-8-sig')
        pd.testing.assert_frame_equal(pd.read_csv(out / path), data.reset_index(drop=True), check_dtype=False, check_exact=False)
        catalog.append(dict(loai='Bảng', ten=title, file=path, nguon=origin, vi_tri=position))
        if show:
            sections.extend([f'## {title}', '', f'Nguồn: {origin}. [{path}]({path})', '', markdown_table(data.astype(object).fillna('không lưu/không áp dụng')), ''])
    def figure(name, title, fig, origin, scope, n, unit, position, error='Không có thanh sai số'):
        caption = f'Nguồn: {origin}; tập: {scope}; n={n}; đơn vị: {unit}. {error}.'
        fig.suptitle(title, fontsize=13)
        fig.text(.02, .015, caption, fontsize=7, wrap=True)
        fig.tight_layout(rect=(0, .13, 1, .94))
        for extension in ['png', 'svg']:
            fig.savefig(out / 'figures' / f'{name}.{extension}', dpi=300, bbox_inches='tight')
        plt.close(fig)
        catalog.append(dict(loai='Hình', ten=title, file=f'figures/{name}.png', nguon=caption, vi_tri=position))
        sections.extend([f'![{title}](figures/{name}.png)', '', caption, '', f'[Bản SVG](figures/{name}.svg)', ''])

    # Inventory before generating anything: preserve source bytes and original relative paths.
    inventory = []
    for p in sorted((root / 'reports').rglob('*')):
        if (not p.is_file() or out in p.parents
                or any(parent.name.startswith('chapter4_export_') for parent in p.parents)
                or p.suffix not in ['.csv', '.json', '.md', '.png', '.svg']):
            continue
        inventory.append({'duong_dan': p.relative_to(root).as_posix(),
                          'loai': p.suffix[1:], 'pham_vi': 'thesis_run' if source in p.parents else 'pilot/khác; không dùng làm kết quả chính'})
    table('artifact_inventory', 'Kiểm kê bảng, hình và báo cáo có sẵn trước khi xuất', pd.DataFrame(inventory),
          'Quét reports/ trước khi xuất; đường dẫn tính từ gốc dự án', 'Phụ lục', show=False)
    sections += ['Kiểm kê đầy đủ đầu ra gốc: [artifact_inventory.csv](tables/artifact_inventory.csv).', '']
    counts = []
    for label, n, values in [('Trước làm sạch', audit['rows_before'], audit['class_counts_before']),
                             ('Sau làm sạch', audit['rows_after'], audit['class_counts_after']),
                             ('Train', split['train_rows'], split['train_class_counts']),
                             ('Holdout', split['holdout_rows'], split['holdout_class_counts'])]:
        counts.append({'Tập': label, 'n': n, 'Nhãn 0': values['0'], 'Nhãn 1': values['1'], 'Tỷ lệ Churn': values['1']/n})
    counts = pd.DataFrame(counts)
    table('data_counts', 'Dữ liệu trước/sau làm sạch và train/holdout', counts, 'data_audit.json; split_manifest.json', '4.1')
    sections += [f"Chuẩn hóa alias rồi loại {audit['duplicates_after_normalization_excluding_id']} dòng trùng, không loại ngoại lệ. "
                 f"Chia phân tầng 80/20, seed={config['seed']}; học tiền xử lý bên trong train fold. "
                 'Mobile→Mobile Phone vẫn là giả định. Xem phần đối soát chi tiết phía dưới.', '']
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(counts))
    ax.bar(x, counts['Nhãn 0'], label='Nhãn 0')
    ax.bar(x, counts['Nhãn 1'], bottom=counts['Nhãn 0'], label='Churn (nhãn 1)')
    ax.set(xticks=x, xticklabels=counts['Tập'], ylabel='Số quan sát'); ax.legend()
    figure('labels', 'Phân bố nhãn', fig, 'data_audit.json; split_manifest.json (không dùng dự đoán)', 'trước/sau sạch; train; holdout', '/'.join(counts['n'].astype(str)), 'quan sát', '4.1')
    missing = pd.DataFrame({'Biến': list(audit['missing_after']), 'Số thiếu': list(audit['missing_after'].values())})
    missing['Tỷ lệ thiếu (%)'] = missing['Số thiếu'] / audit['rows_after'] * 100
    table('missing_clean', 'Thiếu dữ liệu sau làm sạch', missing, 'data_audit.json: missing_after', '4.1')
    fig, ax = plt.subplots(figsize=(10, 7))
    t = missing.sort_values('Tỷ lệ thiếu (%)')
    ax.barh(t['Biến'], t['Tỷ lệ thiếu (%)']); ax.set_xlabel('Tỷ lệ thiếu (%)')
    figure('missing', 'Tỷ lệ thiếu theo biến', fig, 'data_audit.json (không dùng dự đoán)', 'toàn dữ liệu sau làm sạch', audit['rows_after'], '%', '4.1')

    # Copy all tabular evidence byte-for-byte, keeping provenance and no rounding loss.
    for p in sorted(source.rglob('*.csv')):
        rel = p.relative_to(source).as_posix()
        target = 'tables/source_' + rel.replace('/', '__')
        shutil.copyfile(p, out / target)
        assert digest(p) == digest(out / target)
        catalog.append(dict(loai='Bảng nguồn', ten=rel, file=target, nguon=p.relative_to(root).as_posix(),
                            vi_tri='4.2' if 'feature' in rel else '4.7' if any(s in rel for s in ['shap', 'permutation']) else '4.3–4.8 / Phụ lục'))

    features = read('feature_study.csv')
    table('feature_comparison', 'So sánh đặc trưng A–F', features, 'feature_study.csv; repeated 5×3 trên train, AP mean/SD 15 fold', '4.2')
    sections += ['A: biến gốc; B: thêm cờ thiếu chọn trong fit; C: B+CashbackPerOrder; D: B+CouponRate; '
                 'E: B+IsNewCustomer (Tenure≤1); F: B bỏ HourSpendOnApp, OrderCount, CouponUsed. '
                 'Đặc trưng cuối giữ biến gốc+cờ thiếu+IsNewCustomer, không giữ tỷ số; xem feature_selection.json và quy tắc chi tiết.', '']
    benchmark, folds = read('benchmark.csv'), read('benchmark_repeated_folds.csv')
    assert len(benchmark) == 22 and len(folds) == 330
    for row in benchmark.itertuples():
        f = folds[(folds.algorithm == row.algorithm) & (folds.scenario == row.scenario) & (folds.fold < 5)]
        for metric in ['average_precision', 'roc_auc', 'brier', 'fit_seconds', 'predict_seconds']:
            np.testing.assert_allclose([f[metric].mean(), f[metric].std()], [getattr(row, metric+'_mean'), getattr(row, metric+'_std')], rtol=1e-9)
    table('benchmark', 'Benchmark năm thuật toán × P0–P3 và hai dummy', benchmark, 'benchmark.csv; fold 0–4 của benchmark_repeated_folds.csv; train n=4058', '4.3')
    sections += ['P0: không sampling/trọng số; P1: trọng số cân bằng; P2/P3: SMOTE-NC tỷ lệ 1,0/0,5, k=3, không trọng số. '
                 'AP trung bình fold khác AP từ vector OOF gộp. SD fold chỉ mô tả biến thiên, không phải CI hay kiểm định tương đương.', '']
    fig, ax = plt.subplots(figsize=(10, 10))
    t = benchmark.sort_values('average_precision_mean')
    ax.errorbar(t.average_precision_mean, np.arange(len(t)), xerr=t.average_precision_std, fmt='o', capsize=3)
    ax.set(yticks=range(len(t)), yticklabels=t.algorithm + ' / ' + t.scenario, xlabel='AP trung bình 5 fold (0–1)')
    figure('benchmark_ap', 'So sánh AP benchmark', fig, 'benchmark.csv; dự đoán validation từng fold', 'train CV 5 fold', split['train_rows'], 'AP (0–1)', '4.3', 'Thanh ngang: ±1 SD giữa 5 fold, không phải CI')
    representatives, trace = [], []
    for algorithm in config['algorithms']:
        subset = benchmark[benchmark.algorithm == algorithm].sort_values('average_precision_mean', ascending=False)
        best = subset.iloc[0]
        paired = folds[folds.algorithm == algorithm].pivot(index='fold', columns='scenario', values='average_precision')
        for scenario in config['scenarios']:
            row = subset[subset.scenario == scenario].iloc[0]
            sd = (paired[best.scenario] - paired[scenario]).std()
            tolerance = max(config['ap_tolerance'], float(sd))
            passes = best.average_precision_mean-row.average_precision_mean <= tolerance and row.brier_mean <= best.brier_mean+config['brier_tolerance']
            trace.append(dict(algorithm=algorithm, moc=best.scenario, scenario=scenario,
                              ap_drop=best.average_precision_mean-row.average_precision_mean, paired_sd_15=sd,
                              tolerance=tolerance, brier_delta=row.brier_mean-best.brier_mean, duoc_chon=passes))
            if passes:
                representatives.append(row); break
    representatives = pd.DataFrame(representatives).reset_index(drop=True)
    shortlist = read('tuning_shortlist.csv')
    expected = representatives.sort_values('average_precision_mean', ascending=False).head(2)
    assert list(zip(expected.algorithm, expected.scenario)) == list(zip(shortlist.algorithm, shortlist.scenario))
    table('representatives', 'Đại diện từng thuật toán', representatives, 'Tái hiện đúng src/thesis.py:tune trên benchmark/fold đã lưu; không chọn lại mô hình', '4.3')
    table('selection_trace', 'Đối soát quy tắc chọn đại diện', pd.DataFrame(trace), 'AP/Brier 5 fold; SD hiệu ghép cặp trên 15 fold', '4.3')
    table('shortlist', 'Shortlist đã lưu', shortlist, 'tuning_shortlist.csv', '4.3')
    rf = pd.DataFrame(trace).query("algorithm == 'random_forest'").iloc[0]
    sections += [f"RF P1 đứng đầu benchmark, nhưng P0 được giữ: AP giảm {rf.ap_drop:.8f} ≤ "
                 f"max(0,005; SD ghép cặp 15 fold)={rf.tolerance:.8f}; Brier P0−P1={rf.brier_delta:.8f} ≤ 0,005. "
                 'Mã duyệt P0→P1→P2→P3 và giữ phương án đầu đạt điều kiện; RF P1 không vào bốn ứng viên cuối. '
                 'Đây là quy tắc thực dụng ưu tiên đơn giản, không chứng minh tương đương thống kê.', '']
    post = read('post_tuning_folds.csv')
    summary = post.groupby(['algorithm', 'scenario', 'version'])[['average_precision', 'roc_auc', 'brier', 'fit_seconds', 'predict_seconds']].agg(['mean', 'std'])
    summary.columns = ['_'.join(c) for c in summary.columns]
    summary = summary.reset_index()
    pd.testing.assert_frame_equal(summary, read('post_tuning_summary.csv'), check_exact=False, rtol=1e-9)
    table('tuning_comparison', 'Tuned và untuned trên cùng 5 fold', summary, 'post_tuning_folds.csv; train n=4058', '4.4')
    fig, ax = plt.subplots(figsize=(9, 5))
    for algorithm, t in summary.groupby('algorithm'):
        ax.errorbar(t.version, t.average_precision_mean, yerr=t.average_precision_std, marker='o', capsize=3, label=algorithm)
    ax.set_ylabel('AP trung bình 5 fold (0–1)'); ax.legend()
    figure('tuning', 'So sánh tuned/untuned', fig, 'post_tuning_folds.csv; dự đoán validation', 'train CV 5 fold', split['train_rows'], 'AP (0–1)', '4.4', 'Thanh dọc: ±1 SD fold, không phải CI')
    sections += ['Tuning làm giảm AP của cả hai thuật toán trong ngân sách đã chạy (10 trial×3 fold mỗi thuật toán). '
                 'Không khẳng định tuning luôn cải thiện. Mô hình giữ lại: HGB/P0/untuned. '
                 'Ứng viên AP gần nhau chỉ được thay bằng Brier thấp hơn nếu ECE không tăng; không mở lại lựa chọn.', '']
    raw_fold = summary[(summary.algorithm == selection['algorithm']) & (summary.version == selection['version'])]
    calibration = pd.DataFrame([dict(phien_ban=name, AP_mean_fold=raw_fold.average_precision_mean.iloc[0] if key == 'raw_oof' else np.nan,
                                     AP_OOF_gop=selection[key]['average_precision'], Brier_OOF=selection[key]['brier'], ECE_OOF=selection[key]['ece'])
                                for name, key in [('Chưa hiệu chuẩn', 'raw_oof'), ('Sigmoid', 'sigmoid_oof')]])
    table('calibration', 'Trước/sau sigmoid calibration', calibration, 'selection.json; post_tuning_folds.csv', '4.5')
    sections += ['Sigmoid bị loại vì Brier và ECE OOF đều tăng. AP mean fold sigmoid không được lưu; '
                 'không thay bằng AP OOF gộp. Quy tắc yêu cầu AP mean fold giảm≤0,005 và cả Brier/ECE cải thiện. '
                 'Không kiểm chứng độc lập được điều kiện AP sigmoid từ các artifact còn lại.', '']
    fig, ax = plt.subplots(figsize=(7, 6))
    for label, name in [('Chưa hiệu chuẩn', 'uncalibrated'), ('Sigmoid', 'sigmoid')]:
        t = read(f'calibration_bins_{name}_oof.csv')
        assert t['count'].sum() == split['train_rows']
        ax.plot(t.mean_probability, t.positive_rate, 'o-', label=label)
    ax.plot([0, 1], [0, 1], '--', color='gray'); ax.legend()
    ax.set(xlabel='Xác suất trung bình bin', ylabel='Tỷ lệ Churn quan sát')
    figure('reliability', 'Reliability trước/sau sigmoid', fig, 'calibration_bins_*_oof.csv; bin phân vị đã lưu', 'OOF train', split['train_rows'], 'xác suất/tỷ lệ (0–1)', '4.5')

    predictions, metric_rows = {}, []
    for scope, count_key in [('oof', 'train_rows'), ('holdout', 'holdout_rows')]:
        pred = read(f'predictions_{scope}.csv'); predictions[scope] = pred
        assert len(pred) == split[count_key] and pred.row_reference.is_unique
        assert set(pred.row_reference) == set(split['train_row_references' if scope == 'oof' else 'holdout_row_references'])
        y, p = pred.observed_label.to_numpy(), pred.probability.to_numpy()
        assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
        np.testing.assert_array_equal(pred.score, np.minimum(10, 1+np.floor(10*p)).astype(int))
        np.testing.assert_array_equal(pred.prediction, (p >= selection['threshold']).astype(int))
        for group, (lo, hi) in config['risk_groups'].items():
            assert pred.loc[pred.risk_group == group, 'score'].between(lo, hi).all()
            assert (pred.risk_group.eq(group) == pred.score.between(lo, hi)).all()
        origin = f'predictions_{scope}.csv; {selection["algorithm"]}/{selection["scenario"]}/{selection["version"]}'
        scope_label = 'OOF train' if scope == 'oof' else 'holdout đã quan sát ở pilot'
        for threshold_name, threshold in [('0,5', .5), ('F1 từ OOF', selection['threshold'])]:
            values = evaluate(y, p, threshold)
            tn, fp, fn, tp = metrics.confusion_matrix(y, p >= threshold, labels=[0, 1]).ravel()
            metric_rows.append(dict(tap=scope, n=len(y), nguong=threshold, ten_nguong=threshold_name, **values, TN=tn, FP=fp, FN=fn, TP=tp))
            if scope == 'holdout':
                saved = js('metrics_holdout.json')['at_0_5' if threshold == .5 else 'at_f1_threshold']
                for key in saved:
                    np.testing.assert_allclose(values[key], saved[key], atol=1e-12)
            fig, ax = plt.subplots(figsize=(6, 5))
            matrix = np.array([[tn, fp], [fn, tp]])
            ax.imshow(matrix, cmap='Blues')
            for (i, j), value in np.ndenumerate(matrix):
                ax.text(j, i, str(value), ha='center', va='center')
            ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['0', '1'], yticklabels=['0', '1'], xlabel='Nhãn dự đoán', ylabel='Nhãn quan sát')
            figure(f'confusion_{scope}_{"05" if threshold == .5 else "f1"}', f'Ma trận nhầm lẫn — {scope}, t={threshold:.6f}', fig, origin, scope_label, len(y), 'quan sát', '4.5')
        fig, ax = plt.subplots(figsize=(7, 6))
        precision, recall, _ = metrics.precision_recall_curve(y, p)
        ax.plot(recall, precision, label=f'AP gộp={metrics.average_precision_score(y, p):.4f}')
        ax.axhline(y.mean(), ls='--', color='gray', label='Tỷ lệ nhãn 1')
        ax.set(xlabel='Độ bao phủ (Recall)', ylabel='Độ chính xác dương (Precision)'); ax.legend()
        figure('pr_' + scope, 'Đường Precision–Recall — ' + scope, fig, origin, scope_label, len(y), 'tỷ lệ (0–1)', '4.5')
        fig, ax = plt.subplots(figsize=(7, 6))
        fpr, tpr, _ = metrics.roc_curve(y, p)
        ax.plot(fpr, tpr, label=f'AUC={metrics.roc_auc_score(y, p):.4f}'); ax.plot([0, 1], [0, 1], '--', color='gray')
        ax.set(xlabel='Tỷ lệ dương giả', ylabel='Tỷ lệ dương thật'); ax.legend()
        figure('roc_' + scope, 'ROC bổ trợ — ' + scope, fig, origin, scope_label, len(y), 'tỷ lệ (0–1)', '4.5')
        for column, order, label in [('score', list(range(1, 11)), 'Điểm rủi ro'), ('risk_group', list(config['risk_groups']), 'Nhóm rủi ro')]:
            t = pred.groupby(column).observed_label.agg(count='size', positive_count='sum', positive_rate='mean').reindex(order)
            t[['count', 'positive_count']] = t[['count', 'positive_count']].fillna(0).astype(int)
            table(f'{column}_{scope}', f'{label} — {scope}', t.reset_index(), origin, '4.6')
            fig, axes = plt.subplots(1, 2, figsize=(11, 5))
            labels = [str(v) for v in order] if column == 'score' else ['Thấp', 'Trung bình', 'Cao']
            axes[0].bar(labels, t['count']); axes[0].set(xlabel=label, ylabel='Số quan sát')
            axes[1].plot(labels, t.positive_rate, 'o-'); axes[1].set(xlabel=label, ylabel='Tỷ lệ Churn quan sát', ylim=(0, 1))
            figure(f'{column}_{scope}', f'Phân bố và Churn theo {label.lower()} — {scope}', fig, origin, scope_label, len(y), 'quan sát; tỷ lệ (0–1)', '4.6')
    assert not set(predictions['oof'].row_reference) & set(predictions['holdout'].row_reference)
    table('metrics_two_thresholds', 'OOF và holdout tại hai ngưỡng', pd.DataFrame(metric_rows), 'Tính từ predictions_oof.csv và predictions_holdout.csv; AP trên vector gộp', '4.5')
    sections += [f"Ngưỡng F1 cố định từ OOF là {selection['threshold']:.16f}; không tối ưu trên holdout. "
                 'Điểm=min(10,1+floor(10p)); thấp=1–2 (p<0,2), trung bình=3–5 (0,2≤p<0,5), cao=6–10 (p≥0,5). '
                 'Ranh giới nhóm cao 0,5 khác ngưỡng phân loại F1. Bin rỗng có tỷ lệ không xác định, không gán bằng 0.', '']
    table('robustness', 'Kiểm tra độ bền khi bỏ proxy thời gian', read('sensitivity_summary.csv'), 'sensitivity_folds.csv; repeated 5×3 train', '4.7')
    sections += ['Ablation đo mức phụ thuộc nhóm biến; không chứng minh hoặc bác bỏ rò rỉ thời gian. '
                 'Khảo sát k SMOTE-NC và hiệu ghép cặp mất cân bằng được giữ trong bảng nguồn; không dùng để mở lại lựa chọn.', '']
    t = read('permutation_importance.csv').sort_values('mean')
    table('permutation', 'Permutation importance', t, 'permutation_importance.csv; validation 5 fold, 5 lần hoán vị/biến/fold; delta AP', '4.7')
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(t.feature, t['mean'], xerr=t['std'], capsize=2); ax.set_xlabel('Mức giảm AP validation')
    figure('permutation', 'Permutation importance trên validation', fig, 'permutation_importance.csv; dự đoán validation sau hoán vị', 'train CV 5 fold', split['train_rows'], 'delta AP', '4.7', 'Thanh ngang: ±1 SD của trung bình hoán vị giữa 5 fold, không phải CI')
    shap_meta = js('shap_metadata.json')
    local = read('shap_local_contributions.csv').set_index('row_reference')
    context = read('shap_prediction_context.csv').set_index('row_reference').loc[local.index]
    np.testing.assert_allclose(local.sum(axis=1)+context.base_value, context.explained_output, atol=1e-10)
    shap_t = read('shap_grouped_importance.csv'); shap_t.columns = ['feature', 'mean_abs_grouped_shap']
    np.testing.assert_allclose(local.abs().mean().reindex(shap_t.feature), shap_t.mean_abs_grouped_shap, atol=1e-12)
    table('shap', 'SHAP gộp theo biến', shap_t, 'shap_grouped_importance.csv; đối soát đóng góp cục bộ đã lưu', '4.7')
    fig, ax = plt.subplots(figsize=(10, 8))
    t = shap_t.sort_values('mean_abs_grouped_shap'); ax.barh(t.feature, t.mean_abs_grouped_shap); ax.set_xlabel('Trung bình |SHAP gộp| (log-odds)')
    figure('shap_bar', 'SHAP — mức đóng góp trung bình', fig, 'shap_local_contributions.csv; không phải dự đoán đánh giá', 'train in-sample, mô hình cây cơ sở', len(local), 'log-odds', '4.7')
    fig, ax = plt.subplots(figsize=(10, 8))
    for i, name in enumerate(t.feature):
        values = np.sort(local[name].to_numpy())
        # Deterministic display jitter, no additional observations or model computation.
        ax.scatter(values, i + .18*np.sin(np.arange(len(values))*2.4), s=8, alpha=.45)
    ax.set(yticks=range(len(t)), yticklabels=t.feature, xlabel='Đóng góp SHAP có dấu (log-odds)'); ax.axvline(0, color='gray')
    figure('shap_distribution', 'Phân bố đóng góp SHAP đã lưu', fig, 'shap_local_contributions.csv; mỗi chấm là một hồ sơ, không mã hóa giá trị biến', 'train in-sample', len(local), 'log-odds', '4.7')
    sections += [f"SHAP: {shap_meta['explainer']}; nền theo tần số đường đi trong cây train; nhánh nền interventional thất bại đã được loại. "
                 'Đóng góp giải thích output log-odds của mô hình cơ sở; không phải đánh giá OOF/holdout, không phải tác động nhân quả.', '']
    table('timing', 'Thời gian vận hành đã đo (giây)', read('operational_timing.csv'), 'operational_timing.csv; operational_timing_draws.csv', '4.8')
    stages = pd.DataFrame(js('experiment_audit.json')['stages'])[['stage', 'status', 'seconds']]
    table('stage_timing', 'Thời gian từng giai đoạn đã lưu (giây)', stages, 'experiment_audit.json; stage_*.json', '4.8')
    searches = pd.DataFrame(selection['candidates'])[['algorithm', 'search_seconds']].drop_duplicates()
    table('search_timing', 'Thời gian tìm kiếm đã lưu (giây)', searches, 'selection.json: search_seconds; không cộng trùng tuned/untuned', '4.8')
    sections += ['Fit/batch: mỗi loại 5 phép đo, batch trên 4058 dòng; single: warmup 10, rồi đo 200 lần trên một dòng. '
                 'Median/Q1/Q3/p95 đều tính bằng giây; IQR=Q3−Q1. Gồm tiền xử lý và predict_proba, chưa gồm mạng/API. '
                 'Thời gian fit/predict CV nằm trong benchmark và post_tuning; không đồng nhất với search hoặc thời gian giai đoạn. '
                 'Không đo lại thời gian huấn luyện/suy luận trong lần xuất này; thiếu CPU/OS/tải hệ thống lúc đo.', '']
    # Preserve the detailed, previously audited narrative, explicitly as source evidence.
    sections += ['## Đối soát chi tiết đã lưu', '',
                 'Phần dưới trích toàn bộ báo cáo nguồn đã lưu; ngày đối soát là ngày của báo cáo nguồn. '
                 'Các đường dẫn gốc trong dấu mã tính từ gốc dự án. Các bảng nguồn đã được sao chép vào tables/.', '',
                 (source / 'RESULTS.md').read_text(encoding='utf-8')]
    missing_text = '''# Dữ liệu còn thiếu và khả năng tái lập

## Đã lưu và đã xuất

Benchmark/fold, A–F, shortlist, tuning, sensitivity/k, permutation, SHAP, timing, CI bootstrap cũ và hồ sơ rủi ro: xem tables/source_* và artifact_inventory.csv. CI cũ có mô hình/ngưỡng cố định, không gồm bất định lựa chọn; lần xuất này không chạy bootstrap mới.

## Tính lại được từ dự đoán đã lưu — đã thực hiện

AP OOF gộp, ROC, PR, các chỉ số và confusion matrix hai ngưỡng, điểm/nhóm và tỷ lệ Churn theo điểm/nhóm, kiểm tra OOF/holdout không chồng lấn. Reliability trước/sau lấy trực tiếp từ bin đã lưu. Không trộn dự đoán in-sample SHAP vào đánh giá.

## Chưa xuất được / chưa kiểm chứng đầy đủ

| Nội dung | Nguyên nhân | Artifact cần bổ sung / cách khôi phục |
|---|---|---|
| AP mean fold sigmoid và kiểm chứng nhánh AP calibration | Không lưu cal_scores hoặc vector sigmoid OOF; bin không đủ tái tạo thứ hạng | Cần cal_scores outer fold hoặc xác suất sigmoid theo row_reference và fold. Nếu không có bản sao, cần chạy lại huấn luyện calibration CV khi được cho phép; chưa thực hiện |
| PR/ROC/confusion của sigmoid bị loại, và calibration raw/sigmoid trên holdout | Chỉ có dự đoán mô hình cuối; không có xác suất sigmoid trên holdout | Cần dự đoán ứng viên theo từng hồ sơ và nguồn mô hình. Không suy ra từ các chỉ số tổng hợp; không huấn luyện/dự đoán thêm |
| OOF gộp cho mọi cấu hình benchmark/tuning | Chỉ lưu metric từng fold, không lưu xác suất mọi ứng viên | Cần prediction OOF theo cấu hình/fold; nếu mất phải chạy lại CV, chưa thực hiện |
| Danh sách cờ thiếu và số chiều từng fit CV | Metadata chỉ xác nhận mô hình fit toàn train | Cần metadata từng fold; nếu mất cần fit lại CV, chưa thực hiện |
| Beeswarm có màu theo giá trị đặc trưng biến đổi | Đóng góp gộp có sẵn nhưng ma trận đặc trưng biến đổi tương ứng không lưu | Đã xuất phân bố SHAP có dấu không mã hóa màu giá trị biến; cần ma trận biến đổi và tên biến để tái tạo chính xác beeswarm gốc |
| CPU model, OS, tải hệ thống khi đo | Không lưu trong artifact timing | Cần nhật ký môi trường lúc chạy, không dùng phần cứng hiện tại thay thế |
| Xác minh ngữ nghĩa Churn, đơn vị Tenure, horizon, thời điểm biến và alias Mobile/Mobile Phone | Thiếu tài liệu nguồn | Cần data dictionary và bằng chứng thời gian/nguồn dữ liệu; không thể giải quyết bằng huấn luyện lại |
| Kiểm định hoàn toàn mới theo thời gian, can thiệp giữ chân | Holdout từng được quan sát ở pilot | Cần cohort mới hoặc thử nghiệm can thiệp riêng |
| Kết quả AI Agent | Chưa có kiểm thử | Không đưa kết quả Agent vào báo cáo; cần bộ kiểm thử và kết quả thực tế |

Không bịa CI, p-value hoặc số liệu thiếu. SD fold không phải CI hoặc bằng chứng tương đương thống kê. Không phát sinh huấn luyện lại, thay đổi mô hình, ngưỡng, split hoặc quy tắc lựa chọn.
'''
    (out / 'DU_LIEU_CON_THIEU.md').write_text(missing_text, encoding='utf-8')
    sections += ['## Dữ liệu chưa đủ', '', '[Chi tiết và artifact cần bổ sung](DU_LIEU_CON_THIEU.md).', '']
    report = '\n'.join(sections)
    (out / 'BAO_CAO_THUC_NGHIEM.md').write_text(report, encoding='utf-8')
    catalog_df = pd.DataFrame(catalog)
    (out / 'DANH_MUC_BANG_HINH.md').write_text('# Danh mục bảng và hình\n\nĐường dẫn nguồn tính từ gốc dự án hoặc reports/thesis_run/ như ghi chú. PNG đều có bản SVG cùng tên.\n\n' + markdown_table(catalog_df), encoding='utf-8')
    # Dependency-free, self-contained HTML: render exported CSV as tables and embed PNGs.
    parts = ['<!doctype html><html lang="vi"><meta charset="utf-8"><title>Báo cáo Chương 4</title>',
             '<style>body{max-width:1200px;margin:auto;padding:30px;font-family:Arial;line-height:1.6}img{max-width:100%}table{border-collapse:collapse;font-size:12px;display:block;overflow:auto}td,th{border:1px solid #ccc;padding:5px}pre{white-space:pre-wrap}section{margin:30px 0}</style>',
             '<h1>Báo cáo thực nghiệm Chương 4</h1><p>Đồ thị và bảng được nhúng trong tệp này. Toàn văn Markdown nằm cuối trang.</p>']
    for item in catalog:
        parts.append('<section><h2>' + html.escape(item['ten']) + '</h2><p>' + html.escape(item['nguon']) + '</p>')
        if item['loai'] == 'Hình':
            encoded = base64.b64encode((out / item['file']).read_bytes()).decode('ascii')
            parts.append('<img alt="' + html.escape(item['ten']) + '" src="data:image/png;base64,' + encoded + '">')
        elif item['loai'] == 'Bảng':
            parts.append(pd.read_csv(out / item['file']).to_html(index=False, escape=True))
        parts.append('</section>')
    parts += ['<h2>Toàn văn báo cáo Markdown</h2><pre>' + html.escape(report) + '</pre>',
              '<h2>Dữ liệu còn thiếu</h2><pre>' + html.escape(missing_text) + '</pre></html>']
    (out / 'BAO_CAO_THUC_NGHIEM.html').write_text('\n'.join(parts), encoding='utf-8')
    for document in ['BAO_CAO_THUC_NGHIEM.md', 'DANH_MUC_BANG_HINH.md']:
        for ref in re.findall(r'\]\(([^)]+)\)', (out / document).read_text(encoding='utf-8')):
            assert (out / ref).is_file(), f'Broken link: {ref}'
    for rel, expected_hash in hashes.items():
        assert digest(root / rel) == expected_hash, f'Source modified: {rel}'
    manifest = dict(exported_at=now.isoformat(), source_directory=str(source), config=config,
                    model_selection={k: selection[k] for k in ['algorithm', 'scenario', 'version', 'calibrated', 'threshold']},
                    inputs=[dict(path=k, sha256=v) for k, v in hashes.items()],
                    outputs=[dict(path=p.relative_to(out).as_posix(), sha256=digest(p)) for p in sorted(out.rglob('*')) if p.is_file()],
                    validation=dict(source_hashes_unchanged=True, csv_copies_identical=True, benchmark_fold_aggregation=True,
                                    post_tuning_aggregation=True, metrics_match_saved_holdout=True, risk_scores_match=True,
                                    shap_additivity=True, relative_links_exist=True, oof_holdout_disjoint=True),
                    retrained=False, prediction_rerun=False, bootstrap_rerun=False, figures_dpi=300,
                    counts=dict(tables=len(list((out/'tables').glob('*.csv'))), figures=len(list((out/'figures').glob('*.png')))),
                    rerun='venv/Scripts/python.exe -m src.export_chapter4 --config thesis_config.json')
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    from .verify_chapter4 import verify
    verify(out, root)
    print(json.dumps(dict(output=str(out), **manifest['counts'], validation=manifest['validation']), ensure_ascii=False, indent=2))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='thesis_config.json')
    parser.add_argument('--output', help='New directory only; existing directories are rejected')
    args = parser.parse_args()
    export(args.config, args.output)


if __name__ == '__main__':
    main()
