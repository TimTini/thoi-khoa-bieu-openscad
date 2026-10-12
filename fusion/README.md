# Script Fusion native cho bảng thời khóa biểu

`TimetableBoard/TimetableBoard.py` dựng một tài liệu Fusion mới bằng sketch,
extrude, cut, combine và rectangular pattern native. Script không nhập STL,
mesh hay hình học đã tessellate. Mỗi lần bấm **Run** tạo tài liệu parametric
mới; các biến nguồn và biến tính được xem trong **Change Parameters**. Outline
dùng cung tròn native theo bước sóng và được ràng buộc offset associative cho
viền; đây là hình học editable có chủ ý thay cho việc tessellate sinusoid.

## Cách chạy

1. Mở Fusion 360, vào **Utilities > Scripts and Add-Ins** và chạy
   `TimetableBoard.py`.
2. Trong **Change Parameters**, sửa các biến đầu vào ở bảng dưới rồi để Fusion
   recompute timeline. Các seed sketch, text boundary, pocket và magnet recess
   đều có driving expression.
3. Đặt `VERIFY_VARIANTS = True` trước khi chạy nếu muốn script thử thêm biến thể
   7 ngày và 6/4 tiết, kiểm tra body, bounding box, trạng thái feature và khôi
   phục expression mặc định.

Runtime Fusion chưa được chạy trong kiểm thử offline của repository; việc xác
nhận cuối cùng là mở script trong Fusion và quan sát timeline/Change Parameters.

## Bảng tham số chính

| Nhóm | Tham số | Mặc định | Giới hạn hoặc ý nghĩa |
|---|---|---:|---|
| Lưới | `day_count` | 5 | 1..7 ngày; pattern cột dùng biến này |
| Lưới | `morning_periods`, `afternoon_periods` | 5, 5 | Số hàng; `show_*` cho phép tắt một buổi |
| Lưới | `auto_card_length` | 1 | Tự tính chiều dài thẻ; tắt để dùng `fixed_card_length` |
| Lưới | `core_width_ref`, `max_board_width` | 240, 254 mm | Rộng lõi và giới hạn rộng ngoài |
| Lưới | `card_width`, `row_pitch` | 11, 15 mm | Rộng thẻ và bước hàng |
| Thân | `base_thickness` | 5.6 mm | Dày bảng; phải lớn hơn tổng độ sâu hốc |
| Viền | `wave_amplitude`, `wave_pitch` | 1.5, 9.8 mm | Biên độ cập nhật theo expression; đổi số cung theo pitch cần Run lại |
| Hốc | `slot_depth`, `slot_tolerance`, `slot_corner_radius` | 0.01, 0, 3.4 mm | Pocket seed bo góc native rồi pattern theo ngày/hàng |
| Nam châm | `magnet_hole_d`, `magnet_hole_depth` | 6.1, 2.2 mm | Đường kính và độ sâu; không xuyên đáy |
| Nam châm | `magnet_center_pitch`, `magnet_end_inset` | 12, 6.5 mm | Bước và khoảng hốc đầu; `magnet_count` tự tính |
| Plaque | `subtitle_block_length`, `slogan_block_length` | 90, 190 mm | Chiều dài hai plaque tháo rời |
| Plaque | `detachable_block_total_height` | 6.5 mm | Độ cao thân plaque |
| Thẻ môn | `subject_block_total_height`, `subject_text_relief` | 5.2, 0.8 mm | Độ cao thẻ và chữ nổi |

Các biến `effective_*`, `card_length`, `core_width`, `body_height`,
`overall_width`, `grid_left`, vị trí hàng, `magnet_count` và `card_height` là
biến derived. Chúng dùng biểu thức Fusion thay vì tọa độ chỉ có trong Python.

## Những phần dựng native

- Bảng chính có outline ràng buộc đầy đủ, hai lỗ treo tùy chọn, pocket lịch và
  pattern hốc nam châm theo cột/hàng.
- Viền scallop là loop cung tròn sketch native có tâm/bán kính driving; hai offset
  độc lập từ cùng loop tạo thành ring associative rồi Join vào body bảng. Offset
  cho phép topology thay đổi (`isTopologyMatched=False`) khi khoảng cách vượt bán
  kính cục bộ, và profile annular được chọn bằng diện tích thực.
- Tiêu đề, thứ trong tuần và nhãn Sáng/Chiều tạo bằng `SketchText` (Arial), rồi
  `explode` thành profile glyph và extrude `NewBody` Join vào bảng. Một underlay
  mỏng đỡ phần tiêu đề nhô khỏi mép bảng. **`SketchText` không phải rectangle
  sketch tự do** — xem mục “SketchText frame” bên dưới.
- Hai plaque và 14 thẻ môn có thân sketch riêng, chữ nổi riêng và hốc nam châm
  pattern riêng. Sheet thẻ tháo rời giữ bố cục 5 cột cố định; vị trí vẫn là
  expression theo `card_length` và `subject_sheet_gap`.
- Các rãnh/hốc lặp dùng `RectangularPatternFeature`; số lượng ngày, số hàng và
  số nam châm là expression. Nhãn thứ được tạo theo số ngày tại thời điểm Run,
  vì Fusion không thể tạo thêm chuỗi SketchText từ một vòng lặp Python sau khi
  tài liệu đã chạy.

Đơn giản hóa có chủ ý: biên scallop dùng cung tròn native thay vì giữ function
curve sinusoid, chữ dùng font hệ thống Windows qua `FUSION_TEXT_FONTS`
(ưu tiên `Arial`, rồi `Segoe UI` / `Times New Roman` / `Tahoma` / `Calibri`)
thay vì Oswald của SCAD (Oswald không cài trên máy nên Fusion báo
`invalid input font name`), và text metrics không tự đo để đổi chiều dài plaque.
Các đoạn cung kề nhau giữ đúng bước và biên ngoài nhưng có thể tạo tiếp tuyến
gãy nhẹ tại điểm nối; offset ring được kiểm tra như profile kín trong Fusion.
Các lựa chọn này giữ sketch, text và feature có thể sửa được. Arial (và các
font fallback) hỗ trợ dấu tiếng Việt trong nhãn như “Thời khóa biểu”.

Ở stage nhãn bảng, tấm đỡ tiêu đề (Profile) vẫn `JoinFeatureOperation` trực tiếp.
Chữ (title/weekday/Sáng/Chiều) không extrude từ `SketchText`: đối tượng text
**không** nằm trong `sketch.profiles`. Fusion từ chối cả
`createInput`+`setOneSideExtent(SketchText)` và `addSimple(SketchText)` với
`3 : Some input argument is invalid` (Native title). Đường đi đúng:
`SketchText.explode()` → profile glyph kín → `addSimple(Profiles)` `NewBody` →
`Combine` Join vào bảng (cùng pattern plaque/thẻ). Sketch glyph đặt tên
`* glyph sketch` và được `_check_model` miễn khóa đầy đủ.

## SketchText frame (không dùng recipe rectangle)

`SketchText` multiline có `heightParameter` (cỡ glyph) và `rectangleLines` (khung
text có cấu trúc riêng). Solver Fusion đã giữ quan hệ khung; áp recipe rectangle
thường xuyên làm dao động under/over-constraint:

| Recipe đã thử trong Fusion thật | Kết quả |
|---|---|
| Một neo + dimension width/height | Under-constrained |
| Drive cả 4 góc (8 offset) | `VCS_SKETCH_OVER_CONSTRAINTS` tại TR |
| `heightParameter` + BL + H(bottom) bắt buộc + V(left) bắt buộc + BR.x + TL.y | OVER tại `addVertical(left)` — H(bottom) đã OK, V bị implied bởi khung text |

Recipe hiện tại (`_add_text`):

1. `heightParameter` → chiều cao glyph (expression parametric)
2. Drive BL `(x, y)` → vị trí
3. Thử `Horizontal(bottom)` / `Vertical(left)` **best-effort** (`try/except`, không bắt buộc)
4. Drive `BR.x` + `TL.y` → rộng khung / cao khung `1.5 ×` glyph — không drive TR, không drive `BR.y` / `TL.x`
5. Kiểm tra cấu trúc (4 cạnh, 4 góc, height expr) — **không** đòi `sketch.isFullyConstrained`

Font: `FUSION_TEXT_FONTS` ưu tiên Arial rồi fallback Windows có dấu Việt. Mock
offline `isFullyConstrained=True` **không** mô phỏng DOF của SketchText; regression
đếm offset drives và bắt trường hợp `addVertical` raise OVER mà vẫn trả text.

## Kiểm tra lỗi

`_check_model` gọi `computeAll`, duyệt health state của timeline, kiểm tra body
bảng, bounds XY và yêu cầu sketch hình học native phải `isFullyConstrained`.
Sketch chứa `SketchText` được miễn kiểm tra khóa đầy đủ (khung text editable
thường vẫn unlocked). Khi có lỗi, message nêu feature đầu tiên cần xem.

## Giới hạn hình học và thay đổi tham số

- Mẫu mặc định tạo **17 solid**: bảng (gồm viền và chữ), hai bảng tên và 14 thẻ môn. Các part tháo rời được đặt ngoài bảng để chọn/xuất riêng, không lắp sẵn vào hốc.
- Thân và viền dùng cùng biên cung tròn native. Rectangle native giữ bốn driving dimensions của parent (x/y/width/height), sau đó thêm bốn fillet theo `slot_corner_radius`, vì vậy bbox ngoài không bị tăng khi đoạn thẳng bị trim. `wave_amplitude`, kích thước bảng và bán kính góc cập nhật theo expression. `wave_pitch` quyết định số cung lúc Run; đổi pitch cần **Run lại** để đổi topology.
- Các hốc thẻ/bảng tên và thân part rời là rounded rectangle native. `slot_corner_radius` phải nhỏ hơn nửa kích thước cạnh ngắn của từng part; nếu đổi tham số trong Change Parameters cần kiểm tra lại feature health. Dung sai thẻ mở rộng đều về hai phía.
- Tên thứ và các nhóm buổi/lỗ treo được tạo theo lựa chọn lúc Run. Đổi `day_count` vẫn cập nhật lưới, chiều dài thẻ, vị trí nhãn đã có và pattern; để thêm/bớt nhãn thứ phải sửa `DEFAULTS` rồi **Run lại**. Tương tự khi bật/tắt buổi hoặc lỗ treo. Số hàng dương của buổi đã có cập nhật bằng pattern; thêm một buổi vốn không có phải Run lại.
- Tiêu đề dùng cỡ 14 mm (`title_size`) thay cỡ 18 mm của SCAD, có tấm đỡ chữ nhật; không tái tạo biên dạng theo silhouette chữ. Nhãn Sáng/Chiều nằm ngang bên trái thay chữ xoay dọc của SCAD. Font, xuống dòng, dấu tiếng Việt và độ rộng chữ cần kiểm tra trong Fusion; không tự tính lại chiều dài bảng tên theo text metrics.
- Hai bảng tên có chiều dài mặc định 90/190 mm. Cả hốc trên bảng lẫn bảng tên rời có cùng công thức số lượng/tâm nam châm. Độ cao 6.5 mm của bảng tên và 5.2 mm của thẻ đã bao gồm chữ nổi.

## Kiểm chứng offline (2026-10-12)

Chạy từ thư mục project:

```powershell
python -m unittest discover -s tests -p test_fusion_timetable.py -v
python -m py_compile fusion/TimetableBoard/TimetableBoard.py
```

Offline unittest: layout mặc định/7 ngày/6–4 tiết, chain expression thực, một ngày và chiều dài thẻ thủ công, kế hoạch cung native, parent rectangle trước fillet, offset ring độc lập, miền tham số, mock Cut/Pattern, regression SketchText (đếm offset + nuốt OVER từ `addVertical`), và contract extrude text (`explode` → Profiles → NewBody/Combine). Mock `isFullyConstrained=True` không chứng minh DOF text. Đây không phải kiểm chứng solver hay Boolean của Autodesk.

`wave_softness` đã bỏ khỏi bộ tham số Fusion vì cung tròn native không cần độ mịn tessellation. Bản mặc định thay 688 đoạn outline bằng 84 cung; đây là số entity theo kế hoạch hình học Python, chưa phải đo từ document Fusion. Bán kính bo rectangle và biên độ sóng được kiểm tra trước khi dựng để tránh hình học suy biến.

Khi Run, hộp tiến trình báo nhóm đang dựng; lỗi extrude có tên feature và lỗi tổng có stage/traceback. Document lỗi được giữ mở để xem timeline. `_check_model` yêu cầu 17 solid, sketch đủ ràng buộc, feature healthy và bounds bảng đúng; `VERIFY_VARIANTS` kiểm tra recompute rồi khôi phục tham số bằng `finally`. Chưa chạy các kiểm tra này trong Fusion ở đợt bổ sung; chưa có bằng chứng lắp/in thực.

### Bản sửa SketchText sau Board labels (2026-10-12)

1. Constraint: Fusion dừng tại `Native title` với `VCS_SKETCH_OVER_CONSTRAINTS`
   trong `addVertical`. Đã bỏ H/V bắt buộc, giữ `heightParameter` + BL + BR.x +
   TL.y, miễn text sketch khỏi `_check_model` full-constraint.
2. Extrude lần 1: `createInput` + `setOneSideExtent(SketchText)` → error 3.
3. Extrude lần 2: `addSimple(SketchText, border_relief, NewBody)` → error 3.
   Docs ghi SketchText là đối số hợp lệ, nhưng SketchText **không** phải Profile;
   `sketch.profiles.count` vẫn 0 cho đến khi explode.
4. Đường đi hiện tại: `_extrude_text_glyphs` — `explode()` →
   `addSimple(ObjectCollection of Profiles)` → Combine Join. Giữ Arial + tiếng Việt
   (outline glyph tại thời điểm explode; đổi `title_size` sau đó không cập nhật
   lại chữ đã nổ — cần Run lại).

Cần **Run lại** trong Fusion qua Board labels (Native title) và wave trim.
