# Thời khóa biểu OpenSCAD

Dự án chứa một mẫu thời khóa biểu tham số, các khối tháo rời và một số thiết kế OpenSCAD liên quan.

## Mẫu chính

Mở `thoi-khoa-bieu.scad` bằng OpenSCAD. Các thông số thường chỉnh nằm ở đầu file: số ngày, số tiết Sáng/Chiều, nội dung chữ, màu và phần cần xuất trong `output_part`.

OpenSCAD cần bật tính năng `textmetrics` để đo chiều dài Name và Slogan theo nội dung. Các bản xuất được kiểm tra bằng OpenSCAD nightly 2026.09.29 với backend Manifold; trong giao diện bật **Preferences → Experimental → textmetrics**.

Các font được lưu trong `assets/fonts/` và được tham chiếu bằng đường dẫn tương đối. Giấy phép OFL của từng font nằm cạnh file font.

## Bản 3MF

Ba bản xuất hiện tại nằm trong `exports/3mf/`:

- `board.3mf`: bảng chính.
- `name-slogan.3mf`: hai khối Name và Slogan rời nhau trên cùng mặt in.
- `all-subjects.3mf`: đủ 14 thẻ môn, gồm Thể dục, xếp chung trên một mặt in.

Các file 3MF đã được dựng lại từ source dùng dữ liệu mẫu. Đây là file hình học có màu, chưa phải print profile Bambu Studio đã kiểm chứng bằng bản in.

Khi xuất lại 3MF có màu bằng OpenSCAD CLI, thêm `-O export-3mf/material-type=color` để lưu màu dưới dạng `colorgroup`.

Chạy từ thư mục gốc dự án (thay `openscad` bằng đường dẫn executable nếu chưa có trong PATH):

```powershell
openscad --backend Manifold --enable=textmetrics --hardwarnings -O export-3mf/material-type=color -D 'output_part="board"' -o exports/3mf/board.3mf thoi-khoa-bieu.scad
openscad --backend Manifold --enable=textmetrics --hardwarnings -O export-3mf/material-type=color -D 'output_part="name_slogan"' -o exports/3mf/name-slogan.3mf thoi-khoa-bieu.scad
openscad --backend Manifold --enable=textmetrics --hardwarnings -O export-3mf/material-type=color -D 'output_part="subjects"' -o exports/3mf/all-subjects.3mf thoi-khoa-bieu.scad
```

Kiểm tra màu và gán filament trong slicer trước khi in.

## Thư mục khác

- `examples/demo/`: một thiết kế thời khóa biểu khác.
- `examples/blocks/`: khối mẫu và khung sóng.
- `tests/`: script render kiểm tra bố cục. Ảnh và STL được tạo khi chạy sẽ nằm trong thư mục `renders/` và bị Git bỏ qua.
- `thoi-khoa-bieu-presets.json`: các bộ thông số đã lưu cho Customizer.
- `thoi-khoa-bieu.json`: bộ thông số Customizer hiện tại, đã đổi tên hiển thị thành dữ liệu mẫu.

## Dữ liệu mẫu và quyền sử dụng

Tên hiển thị mặc định là **Học sinh mẫu**, không đại diện cho học sinh hoặc lịch học thực tế. Danh sách môn là dữ liệu minh họa; bạn có thể tự sửa trên máy. Không đưa preset chứa tên, trường/lớp hoặc thông tin riêng lên repo công khai.

Giấy phép OFL trong `assets/fonts/` áp dụng cho các font tương ứng. Dự án chưa chọn giấy phép riêng cho thiết kế; việc công khai source không tự cấp quyền thương mại hoặc phân phối lại thiết kế.

Để chạy script kiểm tra trên Windows, đặt biến `$env:OPENSCAD_EXECUTABLE` thành đường dẫn tới `openscad.com` nếu OpenSCAD chưa có trong `PATH`, rồi chạy `pwsh -File tests/test-demo-layout.ps1`.

## Autodesk Fusion

Bộ [script Fusion native parametric](fusion/README.md) tạo document mới gồm bảng, hai bảng tên và 14 thẻ môn. Xem hướng dẫn chạy, tham số, kiểm thử và giới hạn trong tài liệu đó.
