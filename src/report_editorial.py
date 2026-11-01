"""Normalize report documentation to a descriptive academic register."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo


def neutral(text):
    replacements = {
        '# Hướng dẫn chèn hình và bảng Chương 3': '# Danh mục hình, bảng và ghi chú phương pháp — Chương 3',
        'Vị trí đề xuất:': 'Mục liên quan:',
        'Chú thích dùng trong khóa luận:': 'Chú thích:',
        'Mã sửa:': 'Mã nguồn sơ đồ:',
        'Nội dung cần cập nhật trong luận văn': 'Ghi chú đối chiếu',
        'Nguồn người dùng cung cấp': 'Nguồn dữ liệu được tham chiếu',
        'Theo chỉ dẫn người dùng, tiếp tục\nvới': 'Thực nghiệm sử dụng',
        'Người dùng đã xác nhận dùng sheet E Comm ngày 2026-10-25': 'Sheet E Comm được sử dụng trong thực nghiệm ngày 2026-10-25',
        'Thiết kế đã được người dùng chốt ngày 2026-10-25': 'Thiết kế pilot ngày 2026-10-25',
        'file Word người dùng\ncung cấp': 'bản trích luận văn hiện có',
        '(ưu tiên dùng)': '(thesis run)',
        'Không bịa CI, p-value hoặc số liệu thiếu.': 'Không có CI, p-value hoặc số liệu bổ sung ngoài các artifact được dẫn nguồn.',
        'Cài đặt và tái lập': 'Môi trường và tính tái lập',
        'HUONG_DAN_CHEN_HINH_BANG_CHUONG_3.md': 'DANH_MUC_HINH_BANG_CHUONG_3.md',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize(root):
    root = Path(root).resolve()
    changes = []
    for folder in sorted((root/'reports').glob('chapter3_export_*')):
        old = folder/'HUONG_DAN_CHEN_HINH_BANG_CHUONG_3.md'
        if not old.exists():
            continue
        original = old.read_text(encoding='utf-8')
        title_end = original.find('\n## ')
        intro = ('# Danh mục hình, bảng và ghi chú phương pháp — Chương 3\n\n'
                 'Nguồn đối chiếu: `reports/thesis_extracted.txt`. Chưa có Word/PDF gốc để xác nhận phiên bản mới nhất '
                 'và số thứ tự bảng/hình sau dàn trang. Caption Bảng 3.2 chưa xuất hiện trong bản trích.\n\n'
                 'Sơ đồ có bố cục A4 dọc, định dạng SVG và PNG 300 dpi; mã Mermaid lưu cùng tên. '
                 'Biểu đồ kết quả thực nghiệm thuộc Chương 4.\n')
        body = original[title_end:] if title_end >= 0 else ''
        body = body.split('\n## Nội dung cần cập nhật trong luận văn')[0]
        notes = ('\n## Ghi chú đối chiếu\n\n'
                 'Thiết kế kiểm định và nhóm đặc trưng của Bảng 3.4–3.5 thuộc phương pháp nghiên cứu; '
                 'p/q, AP, delta và kết luận thực nghiệm thuộc Chương 4. '
                 'Phân bố nhãn là thống kê mô tả dữ liệu, có mẫu số và phạm vi riêng.\n\n'
                 'Phiên bản thư viện được ghi trong metadata. Số chiều và số cờ thiếu xác nhận ở lần fit toàn train '
                 'không đại diện cho mọi fold. Quy tắc chọn đại diện sử dụng SD hiệu AP trên 15 fold, '
                 'khác mô tả chỉ dùng chênh lệch AP 0,005 trong bản trích. '
                 'Bảng tham số chỉ ghi các giá trị có căn cứ từ mã/config/artifact.\n\n'
                 '## Giới hạn xác minh\n\n'
                 'Chưa có Word mới nhất, tài liệu xác nhận đầy đủ ý nghĩa nhãn, đơn vị đo, horizon, thời điểm hình thành biến '
                 'và alias Mobile/Mobile Phone. Chưa lưu cờ/số chiều từng fold, cal_scores/OOF sigmoid hoặc CPU/OS/tải lúc đo. '
                 'Agent mới ở mức kiến trúc đề xuất; chưa có triển khai tích hợp hoặc kiểm thử.\n\n'
                 '## Phạm vi tổng hợp\n\n'
                 'Hình và bảng được tổng hợp từ mã nguồn và artifact đã lưu. Không phát sinh huấn luyện, suy luận '
                 'hoặc bootstrap mới; dữ liệu và mô hình thực nghiệm giữ nguyên.\n')
        new = folder/'DANH_MUC_HINH_BANG_CHUONG_3.md'
        new.write_text(neutral(intro+body+notes), encoding='utf-8')
        previous_hash = hashlib.sha256(old.read_bytes()).hexdigest()
        old.unlink()
        changes += [str(new.relative_to(root))]
        # The revision is explicit; historical input fingerprints remain historical.
        manifest_path = folder/'manifest.json'
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            manifest.setdefault('document_revisions', []).append({
                'at': datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(),
                'change': 'Instruction document replaced by descriptive catalogue; methodological notes retained',
                'previous_path': old.name, 'previous_sha256': previous_hash, 'new_path': new.name,
                'experimental_artifacts_changed': False})
            manifest['outputs'] = [dict(path=p.relative_to(folder).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                                   for p in sorted(folder.rglob('*')) if p.is_file() and p != manifest_path]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    for name in ['README.md', 'DATA_PROVENANCE.md']:
        path = root/name
        text = neutral(path.read_text(encoding='utf-8'))
        if name == 'README.md':
            # Commands remain accessible through module --help; this file describes the project.
            text = re.sub(r'```powershell\n.*?```\n?', '', text, flags=re.S)
            text = re.sub(r'(?m)^Chạy tại gốc dự án:\n?', '', text)
            text = re.sub(r'Kiểm tra độc lập một bộ báo cáo đã xuất \(thay đường dẫn bằng thư mục thực tế\):\n?',
                          'Các bộ báo cáo có verifier độc lập kiểm tra tính toàn vẹn và số liệu.\n', text)
            text = text.replace('Đặt Excel thật trong `data/raw/`. Giữ nguyên dữ liệu nguồn.',
                                'Dữ liệu nguồn được lưu trong `data/raw/`.')
            text = text.replace('Kiểm tra sheet trước; không tự chọn sheet thay thế trong cấu hình nghiên cứu.',
                                'Sheet được xác định tường minh trong cấu hình nghiên cứu.')
            text = text.replace('Môi trường hiện có là Python 3.15.1, `venv/`. Không ghi đè môi trường này.',
                                'Metadata ghi nhận Python 3.15.1; môi trường cục bộ nằm trong `venv/`.')
            text = re.sub(r'\n{3,}', '\n\n', text)
        path.write_text(text, encoding='utf-8')
        changes.append(name)
    print(json.dumps({'updated_documents': changes, 'experimental_artifacts_changed': False},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    normalize(Path(__file__).resolve().parents[1])
