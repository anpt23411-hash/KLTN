"""Export methodology tables and diagrams from source evidence, without model execution."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import textwrap
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

from .thesis_summary import markdown_table
from .verify_chapter4 import png_dpi


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagram(folder, name, title, nodes, edges, groups=(), note=''):
    """Render PNG/SVG and editable Mermaid from the same nodes and directed edges.

    Positions are fractions of an A4 portrait page; all edges are orthogonal.
    Blue solid boxes: implemented. Orange dashed boxes: proposed.
    """
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis('off')
    for label, x, y, w, h in groups:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.005',
                                   facecolor='#f1f5f8', edgecolor='#9caeb9', zorder=0))
        ax.text(x+w/2, y+h-.015, label, ha='center', va='top', fontsize=9, weight='bold')
    lookup = {node['id']: node for node in nodes}
    lines = ['flowchart TB', '  %% ' + title]
    for node in nodes:
        proposed = node.get('proposed', False)
        ax.add_patch(FancyBboxPatch((node['x']-node['w']/2, node['y']-node['h']/2), node['w'], node['h'],
                     boxstyle='round,pad=0.007', facecolor='#fff1db' if proposed else '#e5f1f7',
                     edgecolor='#b77420' if proposed else '#22617d', linestyle='--' if proposed else '-', zorder=3))
        ax.text(node['x'], node['y'], node['text'], ha='center', va='center', fontsize=node.get('font', 8.5), zorder=4)
        label = node['text'].replace('\n', '<br/>').replace('"', '&quot;')
        lines.append(f'  {node["id"]}["{label}"]:::{"proposed" if proposed else "implemented"}')
    for start, end, label in edges:
        a, b = lookup[start], lookup[end]
        # Vertical flows; lateral flows only connect nodes at the same height.
        if abs(a['y']-b['y']) < .005:
            direction = 1 if b['x'] > a['x'] else -1
            p = (a['x']+direction*a['w']/2, a['y'])
            q = (b['x']-direction*b['w']/2, b['y'])
        else:
            direction = 1 if b['y'] > a['y'] else -1
            p = (a['x'], a['y']+direction*a['h']/2)
            q = (b['x'], b['y']-direction*b['h']/2)
        dashed = a.get('proposed', False) or b.get('proposed', False)
        if abs(p[0]-q[0]) > .005 and abs(p[1]-q[1]) > .005:
            mid = (p[1]+q[1])/2
            ax.plot([p[0], p[0], q[0]], [p[1], mid, mid], color='#546572', lw=1, ls='--' if dashed else '-', zorder=1)
            p = (q[0], mid)
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=10, color='#546572',
                                    linestyle='--' if dashed else '-', linewidth=1, zorder=1))
        if label:
            ax.text((p[0]+q[0])/2+.006, (p[1]+q[1])/2, label, fontsize=7, va='center',
                    bbox=dict(facecolor='white', edgecolor='none', pad=1), zorder=5)
        lines.append(f'  {start} {"-.->" if dashed else "-->"}' + (f'|"{label}"|' if label else '') + f' {end}')
    lines += ['  classDef implemented fill:#e5f1f7,stroke:#22617d,color:#153a4c;',
              '  classDef proposed fill:#fff1db,stroke:#b77420,stroke-dasharray:5 4,color:#6a461a;']
    fig.suptitle(title, fontsize=13, weight='bold', y=.97)
    fig.text(.06, .035, textwrap.fill(note, 110), fontsize=8, va='bottom')
    fig.subplots_adjust(left=.035, right=.965, bottom=.12, top=.94)
    for extension in ['png', 'svg']:
        fig.savefig(folder / f'{name}.{extension}', dpi=300)
    plt.close(fig)
    (folder / f'{name}.mmd').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def node(key, text, y, x=.5, w=.84, h=.067, proposed=False):
    return dict(id=key, text=text, x=x, y=y, w=w, h=h, proposed=proposed)


def export(config_path='thesis_config.json', output=None):
    config_path = Path(config_path).resolve(); root = config_path.parent
    c = json.loads(config_path.read_text(encoding='utf-8'))
    r = root / c['report_dir']; m = root / c['model_dir']
    now = datetime.now(ZoneInfo('Asia/Ho_Chi_Minh'))
    out = Path(output).resolve() if output else root/'reports'/('chapter3_export_'+now.strftime('%Y%m%d_%H%M%S_%f'))
    if any(out == p.resolve() or p.resolve() in out.parents for p in [r, m, root/'data']):
        raise ValueError('Output must be separate from experiment artifacts')
    paths = [config_path, root/'THESIS_ALIGNMENT.md', root/'reports/thesis_extracted.txt']
    paths += list((root/'src').glob('*.py')) + list(r.rglob('*')) + list(m.glob('*'))
    hashes = {p.relative_to(root).as_posix(): sha(p) for p in paths if p.is_file()}
    def js(path):
        return json.loads(path.read_text(encoding='utf-8'))
    assert c == js(r/'config_snapshot.json')
    meta, audit, split = js(m/'metadata.json'), js(r/'data_audit.json'), js(r/'split_manifest.json')
    out.mkdir(parents=True, exist_ok=False); (out/'figures').mkdir(); (out/'tables').mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans', 'svg.fonttype':'none'})
    full = (root/'reports/thesis_extracted.txt').read_text(encoding='utf-8').splitlines()
    starts = [i for i,s in enumerate(full) if 'CHƯƠNG 3.' in s]
    start = starts[-1]; end = next(i for i in range(start+1,len(full)) if 'CHƯƠNG 4.' in full[i])
    chapter = full[start:end]
    (out/'CHUONG_3_BAN_TRICH_DOI_CHIEU.txt').write_text('\n'.join(chapter), encoding='utf-8')
    items = []
    def table(name, title, rows, section, source, status='Đã xác minh từ mã/config/artifact'):
        data = rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)
        data.to_csv(out/'tables'/f'{name}.csv',index=False,encoding='utf-8-sig')
        pd.testing.assert_frame_equal(data.reset_index(drop=True), pd.read_csv(out/'tables'/f'{name}.csv'), check_dtype=False, check_exact=False)
        text = f'# {title}\n\nVị trí: {section}.\n\nNguồn: {source}.\n\nTrạng thái: {status}.\n\n'+markdown_table(data.astype(object).fillna('không xác minh/không áp dụng'))+'\n'
        (out/'tables'/f'{name}.md').write_text(text,encoding='utf-8')
        items.append(dict(loai='Bảng',ten=title,file=f'tables/{name}.md',csv=f'tables/{name}.csv',muc=section,chu_thich=title,nguon=source,trang_thai=status))
    # Document inventory: captions and unnumbered tables were checked directly in the extract.
    comparison = [
        ['3.1','§3.2.3; 0627–0666','Đã có','Cập nhật/ghi giới hạn','Giữ 18 tên biến; đơn vị/horizon/ngữ nghĩa chỉ là mô tả trong bản trích, chưa xác minh nguồn'],
        ['3.2','Không thấy caption trong bản trích','Chưa xác minh','Chưa cấp số thay thế','Cần Word mới nhất để xác nhận bảng thiếu hay lỗi trích xuất'],
        ['3.3','§3.4.3; 0741','Đã có','Cập nhật','Tách làm sạch tất định trước split với phép học theo fold; công bố holdout từng quan sát'],
        ['3.4','§3.5.2; 0780','Đã có, chứa kết quả','Giữ phương pháp; chuyển số liệu sang Chương 4','Chi-square không correction; Fisher nếu expected<5; BH riêng các biến có thiếu trong từng fit'],
        ['3.5','§3.5.5; 0863','Đã có, chứa kết quả A–F','Giữ thiết kế A–F; chuyển AP/delta sang Chương 4','Không cố định 5 cờ hoặc 31 chiều cho mọi fold'],
        ['3.6','§3.6.1; 0903','Đã có','Cập nhật mẫu số/phạm vi','Tách dữ liệu trước/sau làm sạch, train/holdout; là mô tả dữ liệu, không phải hiệu năng'],
        ['3.7','§3.6.3; 0944','Đã có','Đối chiếu P0–P3','SMOTE-NC chỉ train; chuẩn hóa khoảng cách trước sampling, hoàn nguyên sau sampling'],
        ['Chưa đánh số','§3.7.2; 0996–1027','Đã có bảng P và cơ chế trọng số','Cập nhật/loại trùng','HGB class_weight; XGB sample_weight tính từng fit; phiên bản lấy metadata, không ghi sklearn 1.8.0'],
        ['Chưa đánh số','§3.7.4; 1048–1059','Đã có nhóm siêu tham số','Thay bằng không gian được khai báo','Chỉ RF/HGB được tuning; không gọi toàn bộ không gian các mô hình khác là đã khảo sát'],
        ['Chưa đánh số','§3.8.6; 1144–1155','Đã có bảng điểm/nhóm','Đối chiếu công thức','Ngưỡng F1 khác ranh giới nhóm cao; không công bố ngưỡng số được chọn ở Chương 3'],
        ['Chưa đánh số','§3.8.7; 1160–1180','Đã có tiêu chí chọn','Cập nhật quy tắc cụ thể','Mean AP 5 fold; SD hiệu 15 fold dùng quy tắc ưu tiên, không là kiểm định tương đương'],
        ['Agent','§3.10–3.11; 1231–1245','Chỉ có đề mục trong bản trích','Chèn kiến trúc đề xuất và trạng thái','Không có nội dung thiết kế chi tiết/triển khai/kiểm thử Agent để xác nhận']]
    table('doi_chieu_bang', 'Đối chiếu các bảng Chương 3', pd.DataFrame(comparison,columns=['Bảng','Vị trí bản trích','Hiện trạng','Xử lý đề xuất','Căn cứ/giới hạn']), 'Toàn Chương 3', 'reports/thesis_extracted.txt; THESIS_ALIGNMENT.md; mã/config/artifact', 'Đối chiếu bản trích hiện có; chưa xác nhận Word mới nhất')
    descriptions = {}
    for i,s in enumerate(chapter[:-1]):
        value = s.split(': ',1)[-1]
        if value in meta['input_columns']:
            descriptions[value] = chapter[i+1].split(': ',1)[-1]
    table('bien_dau_vao','Danh sách và kiểu xử lý 18 biến đầu vào',[
        {'Biến':col,'Kiểu đã lưu':meta['input_dtypes'][col], 'Xử lý': 'Nominal: mode, mã hóa số rồi one-hot' if col in ['Gender','MaritalStatus','PreferredLoginDevice','PreferredPaymentMode','PreferedOrderCat'] else 'Số: median; log1p nếu đủ điều kiện trong fit',
         'Mô tả theo bản trích (chưa xác minh nghiệp vụ)':descriptions.get(col,'Chưa có'), 'Trạng thái':'Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn'} for col in meta['input_columns']], '§3.2.3 — thay/cập nhật Bảng 3.1', 'models/thesis_run/metadata.json; src/thesis_preprocessing.py; đoạn 0628–0665', 'Xác minh kỹ thuật; không xác nhận các mô tả nghiệp vụ trong bản trích')
    table('chia_du_lieu_cv','Thiết kế phân chia dữ liệu và CV',[
        {'Thành phần':'Dữ liệu trước/sau sạch','Thiết lập':f"{audit['rows_before']} / {audit['rows_after']} dòng",'Phạm vi':'Dữ liệu; không phải hiệu năng'},
        {'Thành phần':'Train / holdout','Thiết lập':f"{split['train_rows']} / {split['holdout_rows']} dòng; stratify Churn, test_size=0.2, seed={c['seed']}",'Phạm vi':'Sau làm sạch; holdout từng quan sát pilot'},
        {'Thành phần':'Đặc trưng/mất cân bằng','Thiết lập':f"RepeatedStratifiedKFold {c['cv_folds']}×{c['cv_repeats']}; seed={c['seed']}",'Phạm vi':'Chỉ train; fold chồng lấn'},
        {'Thành phần':'Benchmark chọn đại diện','Thiết lập':'Fold 0–4 của repeated; 5 thuật toán×4 P + 2 dummy','Phạm vi':'Mean/SD 5 fold; không cộng thêm 110 lượt vào 330'},
        {'Thành phần':'Tuning','Thiết lập':f"RandomizedSearchCV; {c['tuning_iterations']} trial×{c['tuning_folds']} fold; refit=AP; n_jobs=1",'Phạm vi':'Hai thuật toán shortlist; giữ scenario'},
        {'Thành phần':'Sau tuning / calibration','Thiết lập':'Cùng 5-fold StratifiedKFold; sigmoid inner 3-fold','Phạm vi':'OOF ngoài; inner chỉ outer-train; không phải nested model selection độc lập'}], '§3.4.1–3.4.2; §3.7.3', 'src/thesis.py:prepare,cv,benchmark,tune; split_manifest.json; thesis_config.json')
    table('phan_bo_nhan','Phân bố nhãn và mẫu số mô tả dữ liệu',[
        {'Phạm vi':scope,'n':n,'Nhãn 0':counts['0'],'Nhãn 1':counts['1'],'Tỷ lệ nhãn 1':counts['1']/n}
        for scope,n,counts in [('Trước làm sạch',audit['rows_before'],audit['class_counts_before']),
                               ('Sau làm sạch',audit['rows_after'],audit['class_counts_after']),
                               ('Train',split['train_rows'],split['train_class_counts']),
                               ('Holdout',split['holdout_rows'],split['holdout_class_counts'])]],
        '§3.6.1 — cập nhật Bảng 3.6; chỉ mô tả dữ liệu','data_audit.json; split_manifest.json')
    table('quy_uoc_diem_nhom','Quy ước thang điểm và ba nhóm nguy cơ',[
        {'Nhóm':label,'Khoảng xác suất':interval,'Điểm':f'{c["risk_groups"][key][0]}–{c["risk_groups"][key][1]}',
         'Giới hạn':'Quy ước trình bày, chưa xác nhận ngưỡng hành động doanh nghiệp; khác ngưỡng F1'}
        for key,label,interval in [('low','Thấp','0 ≤ p < 0,2'),('medium','Trung bình','0,2 ≤ p < 0,5'),('high','Cao','0,5 ≤ p ≤ 1')]],
        '§3.8.6 — cập nhật bảng nhóm chưa đánh số','thesis_config.json:risk_groups; src/scoring.py:score_probability; src/predict.py')
    preprocessing = [
        ['Trước split','Kiểm tra nhãn 0/1, strip chuỗi, alias, kiểm tra xung đột, loại trùng bỏ ID khỏi khóa nhưng giữ Churn','src/data.py:clean','Không học tham số; alias Mobile/Mobile Phone chưa xác minh'],
        ['prepare.fit','Chọn cờ thiếu q_BH<0,05; chi-square correction=False, Fisher nếu expected<5; học median/mode/danh mục/log','src/thesis_preprocessing.py:PrepareFrame.fit','Chỉ fit trên train fold với y_train'],
        ['prepare.transform','Tỷ số (nếu cấu hình): chia OrderCount>0 trước điền; median → log1p; nominal mã số; cờ thiếu; IsNewCustomer','PrepareFrame.transform','IsNewCustomer=1 khi Tenure≤1 và không thiếu; thiếu→0; chưa xác minh đơn vị Tenure'],
        ['sample (P2/P3)','Scale biến liên tục để đo khoảng cách → SMOTE-NC → inverse scale → tính lại biến phụ thuộc','LogicalSMOTENC.fit_resample','Nominal, Complain, cờ Missing và IsNewCustomer là rời rạc; chỉ train'],
        ['finish.fit/transform','One-hot sau sampling: drop mã 0; unknown ignore; StandardScaler số nếu LR; bỏ cột __ nội bộ','FinishFrame','Tham số fit từ train đã sampling nếu có; validation chỉ transform'],
        ['model.fit/predict','Trọng số tính theo fit; huấn luyện → xác suất lớp 1 trên validation nguyên trạng','src/thesis.py:run_cv; src/experiment.py:FoldWeightedXGB','Không fit/resample validation; y_validation chỉ metric'],
        ['Toàn quy trình','Chọn đặc trưng/ứng viên/calibration/ngưỡng chỉ từ train; giữ nguyên holdout','src/thesis.py:tune,finalize','Holdout từng được quan sát pilot; CV chọn trên train vẫn có thiên lệch lựa chọn']]
    table('pipeline_kiem_soat_ro_ri','Thứ tự tiền xử lý và kiểm soát rò rỉ',pd.DataFrame(preprocessing,columns=['Bước','Thao tác','Nguồn','Ranh giới/giới hạn']), '§3.4.3 và §3.5 — cập nhật Bảng 3.3', 'src/data.py; src/thesis_preprocessing.py; src/thesis.py')
    table('thiet_ke_dac_trung','Thiết kế nhóm đặc trưng A–F',[
        {'Nhóm':k,'Thiết kế':v,'Phép so sánh':comp,'Quy tắc':rule} for k,v,comp,rule in [
        ('A','18 biến gốc; không cờ thiếu; không IsNewCustomer','Mốc','Đánh giá LR và HGB, repeated 5×3'),
        ('B','A + cờ thiếu chọn trong từng fit','B−A','Giữ nếu max(delta AP)≥0,005 và min(delta AP)≥−0,005'),
        ('C','B + CashbackPerOrder=CashbackAmount/OrderCount','C−B','Cùng quy tắc giữ; mẫu số≤0→thiếu trước impute'),
        ('D','B + CouponRate=CouponUsed/OrderCount','D−B','Cùng quy tắc giữ; mẫu số≤0→thiếu trước impute'),
        ('E','B + IsNewCustomer: Tenure≤1 và không thiếu','E−B','Cùng quy tắc giữ; không cố định số cờ từng fold'),
        ('F','B bỏ HourSpendOnApp, OrderCount, CouponUsed','F−B','Chỉ bỏ nếu cả hai delta≥−0,002; không bỏ nguồn của tỷ số được giữ')]], '§3.5.5 — phần thiết kế thay Bảng 3.5; AP thực nghiệm sang Chương 4','src/thesis.py:feature_study')
    table('phuong_an_p0_p3','Phương án xử lý mất cân bằng P0–P3',[
        {'Phương án':key,'Sampling':value['sampling'],'Trọng số':'balanced trong fit; XGB dùng sample_weight' if value['class_weight'] else 'Không',
         'Tỷ lệ minority/majority mục tiêu':str(value.get('ratio','Không áp dụng')),'k':str(value.get('k_neighbors','Không áp dụng')),'Áp dụng':'Chỉ train fold; validation/holdout không resample'} for key,value in c['scenarios'].items()], '§3.6.3 — cập nhật Bảng 3.7','thesis_config.json; src/thesis_preprocessing.py; src/experiment.py')
    table('thuat_toan_tham_so_khai_bao','Thuật toán và tham số được khai báo tường minh',[
        {'Thuật toán':'Logistic Regression','Tham số tường minh':'max_iter=3000; class_weight theo P; random_state=42','Nguồn':'src/experiment.py:model_and_space'},
        {'Thuật toán':'Decision Tree','Tham số tường minh':'class_weight theo P; random_state=42','Nguồn':'src/thesis.py:model'},
        {'Thuật toán':'Random Forest','Tham số tường minh':'n_estimators=150; class_weight theo P; random_state=42; n_jobs=1','Nguồn':'src/experiment.py:model_and_space'},
        {'Thuật toán':'HistGradientBoosting','Tham số tường minh':'class_weight theo P; random_state=42','Nguồn':'src/experiment.py:model_and_space'},
        {'Thuật toán':'XGBoost','Tham số tường minh':'n_estimators=150; max_depth=3; learning_rate=0.05; balanced theo P; random_state=42; n_jobs=1; eval_metric=logloss; tree_method=hist','Nguồn':'src/experiment.py:model_and_space; FoldWeightedXGB'},
        {'Thuật toán':'Hai dummy','Tham số tường minh':'strategy=prior / most_frequent; random_state=42; scenario=baseline','Nguồn':'src/thesis.py:benchmark'}], '§3.7.1–3.7.2','Mã constructor hiện có; các tham số không ghi ở đây không được suy ra từ default thư viện')
    table('khong_gian_tuning','Không gian tuning khai báo cho hai thuật toán thực chạy',[
        {'Thuật toán':alg,'Tham số':key,'Giá trị khai báo':json.dumps(value),'Số trial thực lưu':len(pd.read_csv(r/f'tuning_{alg}.csv'))}
        for alg,space in {
            'random_forest':{'n_estimators':[100,150,250],'max_depth':[None,4,8,12],'min_samples_split':[2,5,10],'min_samples_leaf':[1,2,4,8],'max_features':['sqrt',.7,1.]},
            'hist_gradient_boosting':{'learning_rate':[.03,.05,.1],'max_leaf_nodes':[7,15,31],'l2_regularization':[0.,1.,10.],'max_iter':[100,150,200],'max_depth':[None,3,6],'min_samples_leaf':[10,20,40]}
        }.items() for key,value in space.items()], '§3.7.4 — thay bảng nhóm tham số dự kiến','src/experiment.py:model_and_space; src/thesis.py:model; tuning_*.csv', 'Không gian xác minh từ mã; có 10 trial lưu mỗi thuật toán; không phải đã thử mọi tổ hợp')
    rules = [
        ['Đại diện từng thuật toán','Mốc=max mean AP 5 fold; duyệt P0→P1→P2→P3; giữ đầu tiên có AP giảm≤max(0,005, SD hiệu ghép cặp 15 fold) và Brier tăng≤0,005','SD là quy tắc ưu tiên; không kiểm định tương đương'],
        ['Shortlist','Xếp 5 đại diện theo mean AP; lấy 2 thuật toán khác nhau','Không lấy thẳng 2 hàng đầu toàn benchmark'],
        ['Tuning/untuned','10 trial×3 fold mỗi thuật toán; giữ scenario; đánh giá cả tuned và untuned trên cùng 5 fold','Không bảo đảm tuning cải thiện'],
        ['Ứng viên cuối','Mốc mean AP cao nhất; chỉ đổi sang Brier thấp hơn nếu AP giảm≤0,005 và ECE OOF không tăng','AP mean fold; Brier/ECE vector OOF gộp'],
        ['Sigmoid','Outer 5 fold; inner 3 fold; nhận nếu mean AP sigmoid≥mean AP mốc−0,005 và cả Brier/ECE OOF giảm','Không lưu cal_scores hay vector sigmoid OOF: chưa kiểm chứng độc lập nhánh AP'],
        ['Ngưỡng','Tối đa F1 từ vector OOF; hòa: recall cao hơn, sau đó ngưỡng thấp hơn; dự đoán 1 khi p≥t','Giữ nguyên trên holdout; t số thực nghiệm trình bày Chương 4'],
        ['Điểm/nhóm','score=min(10,1+floor(10p)); thấp 1–2; trung bình 3–5; cao 6–10','Ranh giới p=0,2/0,5; nhóm cao khác ngưỡng F1'],
        ['Đánh giá','AP sklearn average_precision_score; ECE qcut tối đa 10 bin, duplicate edges drop; bootstrap phân tầng 1000, seed42','AP mean fold khác AP OOF; CI mô hình/ngưỡng cố định, không bao gồm bất định lựa chọn']]
    table('quy_tac_lua_chon','Quy tắc benchmark, chọn mô hình, calibration và ngưỡng',pd.DataFrame(rules,columns=['Giai đoạn','Quy tắc trong mã','Giới hạn']), '§3.7.3–3.8.7','src/thesis.py:tune; src/evaluation.py; thesis_config.json')
    table('thiet_ke_dien_giai_van_hanh','Thiết kế kiểm tra độ bền, diễn giải và đo thời gian',[
        {'Thành phần':'Ablation','Thiết kế':'Bỏ Complain, DaySinceLastOrder, OrderCount, CouponUsed, CashbackAmount và dẫn xuất; full/reduced repeated5×3','Giới hạn':'Không chứng minh/bác bỏ rò rỉ thời gian'},
        {'Thành phần':'Khảo sát sampler','Thiết kế':'P2/P3 × k=3,5,7 × 5 fold trên train','Giới hạn':'Không mở lại quyết định cuối'},
        {'Thành phần':'Permutation','Thiết kế':'5 validation fold; 5 permutation/biến/fold; scoring=AP','Giới hạn':'SD fold không là CI; không phải importance in-sample'},
        {'Thành phần':'SHAP đã dùng','Thiết kế':'TreeExplainer tree_path_dependent; nền tần số nút train; 150 hồ sơ; log-odds; gộp one-hot trước abs','Giới hạn':'In-sample explanation; nhánh interventional thất bại; không phân rã sigmoid'},
        {'Thành phần':'Timing','Thiết kế':f"Fit 5; batch 5 trên {split['train_rows']} dòng; single warmup10 + 200 phép đo; giây; median/Q1/Q3/p95",'Giới hạn':'Gồm preprocessing/predict_proba; không gồm mạng/API; thiếu CPU/OS/tải lúc đo'}], '§3.7.5; §3.8.8; §3.9','src/thesis.py:robustness; src/thesis_explain.py; shap_metadata.json')
    agent = [
        ['Schema và suy luận cục bộ','Đã có','src/predict.py:predict_frame; pipeline.joblib; metadata.json','Nhận DataFrame đặc trưng; không ID/Churn/cột thừa; trả xác suất, nhãn, điểm, nhóm'],
        ['Diễn giải đã lưu','Đã có cho mẫu train','shap_local_contributions.csv; shap_metadata.json','Chưa có endpoint giải thích hồ sơ mới'],
        ['Tra cứu CRM/hồ sơ theo ID','Chưa triển khai','Không tìm thấy trong src/; Chương3 chỉ có đề mục §3.10','Đề xuất adapter truy xuất và phân quyền'],
        ['Agent điều phối/tool adapter/API','Chưa triển khai','src/predict.py là CLI; không phải API service','Đề xuất lớp gọi công cụ xác định, không tự sinh điểm'],
        ['LLM và giao diện/báo cáo cá nhân','Chưa triển khai','Không có triển khai trong mã hiện có','Đề xuất nhận kết quả công cụ, trình bày có nguồn'],
        ['Kiểm thử Agent/latency/chi phí API','Chưa có kết quả','§3.11 chỉ có đề mục trong bản trích','Cần bộ tình huống và log thực tế; không tạo số liệu']]
    table('trang_thai_agent','Trạng thái thành phần kiến trúc AI Agent',pd.DataFrame(agent,columns=['Thành phần','Trạng thái','Căn cứ','Phạm vi/đề xuất']), '§3.10.2; §3.11','src/predict.py; artifacts; reports/thesis_extracted.txt:1231–1245','Lõi ML xác minh; tích hợp Agent là kiến trúc đề xuất chưa kiểm thử')
    table('moi_truong_da_luu','Phiên bản môi trường được metadata ghi lại',[
        {'Thành phần':'Python','Phiên bản đã lưu':meta['python'],'Trạng thái':'Metadata lịch sử, không suy ra từ runtime xuất hình'},
        *[{'Thành phần':key,'Phiên bản đã lưu':value,'Trạng thái':'Metadata lịch sử'} for key,value in meta['versions'].items()]],'§3.12','models/thesis_run/metadata.json')
    # Four page-sized, code-native diagrams; no empirical result plots.
    definitions = [
        ('hinh_01_tong_the','Quy trình nghiên cứu tổng thể','§3.1.2',
         [node('A','Đọc dữ liệu thật → chuẩn hóa tất định\nKiểm tra nhãn/xung đột → loại trùng',.94),
          node('B','Chia phân tầng sau làm sạch: train 80% / holdout 20%\nGiữ holdout riêng; công bố đã từng quan sát ở pilot',.82),
          node('C','Chỉ train: EDA → nghiên cứu đặc trưng A–F\nRepeated 5×3; chọn đặc trưng theo quy tắc',.70),
          node('D','Smoke → benchmark 5 thuật toán × P0–P3 + 2 dummy\nRepeated 5×3; 5 fold đầu dùng chọn đại diện',.58),
          node('E','Shortlist → tuning và untuned → calibration → ngưỡng OOF\nFit toàn train, lưu mô hình và quyết định',.46),
          node('F','Robustness trên train → diễn giải và đo thời gian\nSau đó đánh giá holdout với quyết định đã cố định',.34),
          node('G','Xuất artifact ML và báo cáo\nHình kết quả thực nghiệm đặt tại Chương 4',.22),
          node('H','Tích hợp AI Agent và kiểm thử hệ thống\nGiai đoạn đề xuất — chưa triển khai',.10,proposed=True)],
         [('A','B',''),('B','C',''),('C','D',''),('D','E',''),('E','F',''),('F','G',''),('G','H','')],(),
         'Nguồn: src/thesis.py:prepare→features→smoke→benchmark→tune→robustness→finalize; src/data.py. Nét xanh liền: đã có mã/artifact ML; nét cam đứt: kiến trúc/giai đoạn đề xuất.'),
        ('hinh_02_fold','Tiền xử lý và đánh giá trong từng fold','§3.4.3; §3.5',
         [node('S','Train phát triển → chia chỉ số fold\nValidation không tham gia fit',.95),
          node('T','HUẤN LUYỆN: fit / resample\nX_train_fold + y_train_fold',.84,x=.26,w=.40,h=.07), node('V','VALIDATION: transform / predict\nX_validation; giữ y riêng',.84,x=.74,w=.40,h=.07),
          node('P','prepare.fit rồi transform\nHọc cờ thiếu, median/mode,\ndanh mục và log từ train',.71,x=.26,w=.40,h=.10),
          node('PV','prepare.transform\nDùng trạng thái học từ train\nKhông học cờ/median mới',.71,x=.74,w=.40,h=.10),
          node('R','Chỉ P2/P3: scale khoảng cách\nSMOTE-NC → inverse scale\nTính lại biến phụ thuộc',.55,x=.26,w=.40,h=.10),
          node('RV','Không resample validation\nGiữ nguyên phân bố lớp',.55,x=.74,w=.40,h=.08),
          node('F','finish.fit rồi transform\nOne-hot; scale số nếu LR\nSau đó model.fit',.39,x=.26,w=.40,h=.10),
          node('FV','finish.transform\nDùng encoder/scaler train\nmodel.predict_proba',.39,x=.74,w=.40,h=.10),
          node('O','Xác suất validation + y_validation → metric fold / OOF\nKhông dùng validation để học tiền xử lý hoặc sinh mẫu',.18)],
         [('S','T',''),('S','V',''),('T','P',''),('V','PV',''),('P','PV','trạng thái'),('P','R',''),('PV','RV',''),('R','F',''),('RV','FV',''),('F','FV','trạng thái'),('FV','O','')],
         [('',.035,.29,.45,.60),('',.515,.29,.45,.60)],
         'Nguồn: src/thesis.py:run_cv; PrepareFrame→[LogicalSMOTENC nếu P2/P3]→FinishFrame→model. P0/P1 bỏ qua resample. Sigmoid thêm inner3 chỉ trong outer-train. Holdout dùng cùng hợp đồng transform; từng được quan sát ở pilot.'),
        ('hinh_03_lua_chon','Benchmark, lựa chọn, calibration và ngưỡng','§3.7.3–3.8.7',
         [node('A','Benchmark: 22 cấu hình; first 5-fold mean AP/Brier\nRepeated 15 fold còn dùng SD hiệu ghép cặp',.95),
          node('B','Mỗi thuật toán: mốc AP cao nhất; duyệt P0→P1→P2→P3\nGiảm AP≤max(0,005; SD hiệu 15 fold), tăng Brier≤0,005',.84),
          node('C','Xếp 5 đại diện theo mean AP → shortlist 2 thuật toán\nGiữ scenario; không lấy trực tiếp top 2 toàn benchmark',.73),
          node('D','RandomizedSearchCV: 10 trial × inner3 / thuật toán\nĐánh giá lại tuned và untuned trên cùng 5 fold',.62),
          node('E','Giữ mốc mean AP cao nhất; đổi sang Brier thấp hơn chỉ khi\nAP giảm≤0,005 và ECE OOF không tăng',.51),
          node('F','Sigmoid: outer5, inner3 chỉ outer-train\nNhận nếu mean AP giảm≤0,005 và Brier/ECE OOF cùng giảm\nKhông đạt: giữ raw; thiếu cal_scores lưu nên chưa tái kiểm AP',.39,h=.09),
          node('G','OOF của phiên bản giữ lại → tối đa F1\nHòa: recall cao hơn, sau đó ngưỡng thấp hơn',.26),
          node('H','Cố định mô hình/calibration/ngưỡng → fit toàn train\nLưu artifact → robustness → finalize trên holdout',.13)],
         [('A','B',''),('B','C',''),('C','D',''),('D','E',''),('E','F',''),('F','G',''),('G','H','')],(),
         'Nguồn: src/thesis.py:tune; src/evaluation.py:choose_threshold. AP mean fold không phải AP OOF gộp; Brier/ECE dùng OOF gộp. SD không là CI hoặc kiểm định tương đương. CV chọn trên train vẫn có thiên lệch lựa chọn.'),
        ('hinh_04_agent','AI Agent đánh giá nguy cơ — KIẾN TRÚC ĐỀ XUẤT','§3.10.2',
         [node('U','Người dùng → giao diện nhận yêu cầu\nĐề xuất — chưa có giao diện',.95,proposed=True),
          node('A','Agent điều phối + LLM\nĐề xuất — chưa triển khai/kiểm thử',.83,proposed=True),
          node('D','Truy xuất hồ sơ / CRM\nPhân quyền, kiểm tra ID\nChưa có kết nối dữ liệu',.68,x=.26,w=.40,h=.09,proposed=True),
          node('W','Tool adapter / API service\nĐóng gói suy luận/diễn giải\nChưa triển khai',.68,x=.74,w=.40,h=.09,proposed=True),
          node('M','Lõi suy luận cục bộ ĐÃ CÓ: predict_frame\nKiểm tra schema → pipeline.joblib + metadata.json\nChỉ đặc trưng; không đưa ID/Churn vào mô hình',.51,h=.09),
          node('S','Đầu ra xác định ĐÃ CÓ\nXác suất → nhãn theo t*; điểm 1–10; ba nhóm nguy cơ',.37,h=.08),
          node('R','Đề xuất: Agent nhận kết quả có nguồn, trình bày báo cáo\nKhông tự tạo xác suất/điểm; xử lý lỗi và ghi log\nSHAP đã lưu chỉ cho mẫu train, chưa có dịch vụ hồ sơ mới',.22,h=.10,proposed=True),
          node('T','Đề xuất: kiểm thử tool/tra cứu/khớp kết quả/giải thích\nLatency và chi phí API — chưa có số liệu kiểm thử',.08,proposed=True)],
         [('U','A',''),('A','D',''),('A','W',''),('D','W','hồ sơ hợp lệ'),('W','M',''),('M','S',''),('S','R',''),('R','T','')],(),
         'Nguồn: src/predict.py; metadata/pipeline ML; bản trích §3.10–3.11 chỉ có đề mục. Xanh liền: thành phần ML cục bộ đã có, chưa tích hợp Agent. Cam đứt: đề xuất, chưa triển khai. Không ngụ ý hệ thống Agent đang hoạt động.')]
    for name,title,section,nodes,edges,groups,note in definitions:
        diagram(out/'figures',name,title,nodes,edges,groups,note)
        items.append(dict(loai='Hình',ten=title,file=f'figures/{name}.png',csv=f'figures/{name}.svg',muc=section,chu_thich=title+'. '+note,nguon=note,trang_thai='Kiến trúc đề xuất, phân biệt lõi ML đã có/chưa có' if 'agent' in name else 'Đã đối chiếu thứ tự mã thực tế'))
    intro = '# Danh mục hình, bảng và ghi chú phương pháp — Chương 3\n\n'
    intro += 'Tài liệu đối chiếu: `reports/thesis_extracted.txt`, phần thân đoạn 0580–1246. Chưa có Word/PDF gốc để xác nhận phiên bản mới nhất và số thứ tự sau dàn trang. Caption Bảng 3.2 chưa xuất hiện trong bản trích.\n\n'
    intro += 'Sơ đồ có bố cục A4 dọc, định dạng SVG và PNG 300 dpi; mã Mermaid `.mmd` lưu cùng tên. Bản vẽ và Mermaid dùng chung danh sách nút/cạnh. Biểu đồ kết quả thực nghiệm thuộc Chương 4.\n\n'
    guide = [intro]
    for item in items:
        guide += [f'## {item["ten"]}', '', f'- Mục liên quan: {item["muc"]}.',
                  f'- Tệp: [{item["file"]}]({item["file"]}); [{item["csv"]}]({item["csv"]}).',
                  f'- Chú thích: {item["chu_thich"]}.',
                  f'- Căn cứ: {item["nguon"]}.', f'- Trạng thái: {item["trang_thai"]}.', '']
        if item['loai']=='Hình':
            stem=Path(item['file']).stem
            guide += [f'- Mã nguồn sơ đồ: [Mermaid](figures/{stem}.mmd).', '', f'![{item["ten"]}]({item["file"]})','']
    guide += ['## Ghi chú đối chiếu', '',
              'Thiết kế kiểm định và nhóm đặc trưng của Bảng 3.4–3.5 thuộc phương pháp nghiên cứu; p/q, AP, delta và kết luận thực nghiệm thuộc Chương 4. Phân bố nhãn là thống kê mô tả dữ liệu, có mẫu số và phạm vi riêng.', '',
              'Phiên bản thư viện được ghi trong metadata. Số chiều và số cờ thiếu xác nhận ở lần fit toàn train không đại diện cho mọi fold. Quy tắc chọn đại diện sử dụng SD hiệu AP trên 15 fold; bản trích mới mô tả chênh lệch AP 0,005. Bảng tham số chỉ ghi các giá trị có căn cứ từ mã/config/artifact.', '',
              '## Chưa xác minh / cần bổ sung', '',
              'Word mới nhất và số trang/bảng sau dàn trang; tài liệu xác nhận nhãn, đơn vị Tenure/khoảng cách/tiền tệ, horizon và thời điểm hình thành biến; tính tương đương alias Mobile/Mobile Phone; cờ/số chiều từng fold; cal_scores/OOF sigmoid; CPU/OS/tải lúc đo; thiết kế chi tiết và kiểm thử Agent. §3.10–3.11 hiện chỉ là đề mục trong bản trích, sơ đồ là đề xuất kỹ thuật từ lõi ML và phạm vi đã nêu, không phải mô tả triển khai.', '',
              '## Phạm vi tổng hợp', '',
              'Hình và bảng được tổng hợp từ mã nguồn và artifact đã lưu. Dữ liệu thực nghiệm, mô hình và văn bản luận văn gốc không thay đổi; không phát sinh huấn luyện, suy luận hoặc bootstrap mới.']
    (out/'DANH_MUC_HINH_BANG_CHUONG_3.md').write_text('\n'.join(guide),encoding='utf-8')
    pd.DataFrame(items).to_csv(out/'DANH_MUC.csv',index=False,encoding='utf-8-sig')
    for path in (out/'figures').glob('*.png'):
        assert all(abs(v-300)<.1 for v in png_dpi(path))
        assert path.with_suffix('.svg').is_file() and path.with_suffix('.mmd').is_file()
    for path in out.rglob('*.md'):
        for ref in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            assert (path.parent/ref).is_file(), ref
    assert all(sha(root/path)==value for path,value in hashes.items()), 'Inputs modified during export'
    manifest=dict(exported_at=now.isoformat(),document_source='reports/thesis_extracted.txt',latest_chapter_verified=False,
                  config=c,inputs=[dict(path=path,sha256=value) for path,value in sorted(hashes.items())],
                  outputs=[dict(path=p.relative_to(out).as_posix(),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()],
                  retrained=False,prediction_rerun=False,diagrams=4,tables=sum(i['loai']=='Bảng' for i in items),
                  validation=dict(source_hashes_unchanged=True,png_300_dpi=True,svg_and_mermaid_pairs=True,relative_links=True,csv_roundtrip=True),
                  renderer='Matplotlib vector primitives; Mermaid node/edge source from same specification; no external renderer required')
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(out),diagrams=4,tables=manifest['tables'],validation=manifest['validation']),ensure_ascii=False,indent=2))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='thesis_config.json'); parser.add_argument('--output')
    args=parser.parse_args(); export(args.config,args.output)


if __name__=='__main__':
    main()
