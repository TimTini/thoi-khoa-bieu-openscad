"""Create a native, editable timetable board in Autodesk Fusion.

Run from Utilities > Scripts and Add-Ins. Dimensions are millimetres in the
public parameter table; Fusion stores them internally in centimetres. The
script creates a new parametric document on every run. Board, trim, plaques,
and cards use sketches and native extrude/cut features.

The source SCAD uses text metrics to size plaques and a sinusoidal outline.
Fusion's text metrics are not consistently exposed to scripts, so plaque
widths are explicit parameters. The scalloped outline uses editable native
circular arcs and an associative offset ring; it intentionally preserves the
outer bounds and pitch topology without tessellating the source curve. Board
dimensions, grid positions, recess sizes, and feature heights remain linked to
Change Parameters expressions. Rerun after changing wave pitch/amplitude when
a different scallop count is wanted.
"""
import math
import ast
import traceback


VERIFY_VARIANTS = False

# Fusion SketchText only accepts fonts registered with Windows/Fusion.
# The SCAD model uses Oswald from assets/fonts/, which is not a system font
# here and raises "RuntimeError: 3 : invalid input font name". Prefer common
# Windows fonts that include Vietnamese glyphs (ơ, ư, ế, ộ, ...).
FUSION_TEXT_FONTS = (
    "Arial",
    "Segoe UI",
    "Times New Roman",
    "Tahoma",
    "Calibri",
)

SUBJECT_NAMES = [
    "Tiếng Việt", "Toán", "Tiếng Anh", "Hoạt động trải nghiệm",
    "Tiếng Anh bổ trợ", "Tiếng Anh Giao tiếp", "Tự nhiên xã hội",
    "Giáo dục thể chất", "Âm nhạc", "Kỹ năng sống", "STEM",
    "Đạo đức", "Mỹ thuật", "Thể dục",
]
SUBJECT_LABELS = [
    "Tiếng Việt", "Toán", "Tiếng Anh", "HĐTN", "TA BT", "TA GT",
    "TN&XH", "GDTC", "Âm nhạc", "KNS", "STEM", "Đạo đức", "Mỹ thuật", "Thể dục",
]

# Values are millimetres unless explicitly marked as a count or a switch.
DEFAULTS = {
    "title_relief": 1.2, "title_size": 14.0,
    "day_count": 5, "morning_periods": 5, "afternoon_periods": 5,
    "show_morning": 1, "show_afternoon": 1, "show_wall_holes": 1,
    "auto_card_length": 1, "fixed_card_length": 31.0,
    "core_width_ref": 240.0, "max_board_width": 254.0,
    "base_thickness": 5.6, "border_width": 1.6, "border_edge_gap": 2.0,
    "border_relief": 1.2, "wave_amplitude": 1.5, "wave_pitch": 9.8,
    "corner_radius": 15.0,
    "wall_hole_d": 4.0, "wall_hole_margin": 12.0,
    "card_width": 11.0, "row_pitch": 15.0,
    "slot_corner_radius": 3.4, "slot_depth": 0.01, "slot_tolerance": 0.0,
    "magnet_hole_d": 6.1, "magnet_hole_depth": 2.2,
    "magnet_center_pitch": 12.0, "magnet_end_inset": 6.5,
    "subtitle_block_length": 90.0, "subtitle_block_width": 17.0,
    "slogan_block_length": 190.0, "slogan_block_width": 14.0,
    "block_wall": 1.2, "detachable_block_total_height": 6.5,
    "subject_block_total_height": 5.2, "subject_text_relief": 0.8,
    "subject_sheet_gap": 4.0,
    "baseline_body_h": 216.2, "baseline_periods": 10.0,
    "grid_core_margin": 16.34, "min_column_gap": 2.0,
    "afternoon_y_ref": 12.50, "middle_y_ref": 84.64,
    "morning_y_ref": 101.00, "weekday_y_ref": 179.20,
    "subtitle_y_ref": 185.80, "title_y_ref": 214.60,
}

COMMENTS = {
    "title_relief":"Độ nổi chữ plaque; mm; trừ khỏi thân để giữ tổng chiều cao",
    "title_size":"Cỡ chữ tiêu đề; mm; mặc định14 để nằm trong tấm đỡ227mm",
    "day_count": "Số ngày hiển thị, giới hạn 1..7", "morning_periods": "Số tiết buổi sáng",
    "afternoon_periods": "Số tiết buổi chiều", "show_morning": "Bật lưới buổi sáng (1/0)",
    "show_afternoon": "Bật lưới buổi chiều (1/0)", "show_wall_holes": "Bật hai lỗ treo tường (1/0)",
    "auto_card_length": "Tự tính chiều dài thẻ theo chiều rộng bảng (1/0)",
    "fixed_card_length": "Chiều dài thẻ khi tắt tự tính", "core_width_ref": "Chiều rộng lõi bảng theo SCAD",
    "max_board_width": "Giới hạn chiều rộng ngoài của bảng", "base_thickness": "Độ dày thân bảng",
    "border_width": "Bề rộng viền nổi", "border_edge_gap": "Khoảng cách viền tới mép lõi",
    "border_relief": "Chiều cao viền nổi", "wave_amplitude": "Biên độ sóng mép",
    "wave_pitch": "Bước sóng mép; đổi số cung cần Run lại",
    "corner_radius": "Bán kính góc ngoài", "wall_hole_d": "Đường kính lỗ treo",
    "wall_hole_margin": "Khoảng cách tâm lỗ tới mép lõi", "card_width": "Chiều rộng thẻ",
    "row_pitch": "Bước tâm giữa các hàng",
    "slot_depth": "Độ sâu rãnh thẻ", "slot_tolerance": "Dung sai rãnh",
    "slot_corner_radius": "Bán kính bo góc rãnh, plaque và thẻ; mm",
    "magnet_hole_d": "Đường kính hốc nam châm", "magnet_hole_depth": "Độ sâu hốc nam châm",
    "magnet_center_pitch": "Bước tâm nam châm", "magnet_end_inset": "Khoảng cách hốc đầu tới mép thẻ",
    "subtitle_block_length": "Chiều dài plaque tên", "subtitle_block_width": "Chiều rộng plaque tên",
    "slogan_block_length": "Chiều dài plaque khẩu hiệu", "slogan_block_width": "Chiều rộng plaque khẩu hiệu",
    "block_wall": "Vật liệu tối thiểu quanh hốc plaque",
    "detachable_block_total_height": "Chiều cao plaque tổng thể",
    "subject_block_total_height": "Chiều cao thẻ môn tổng thể", "subject_text_relief": "Độ nổi nhãn môn",
    "subject_sheet_gap": "Khoảng cách các thẻ khi xếp rời",
}

# Simple Fusion expressions keep geometry ownership in Change Parameters.
DERIVED = {
    "effective_morning_rows": ("if(show_morning == 1; morning_periods; 0)", ""),
    "effective_afternoon_rows": ("if(show_afternoon == 1; afternoon_periods; 0)", ""),
    "period_delta": ("(effective_morning_rows + effective_afternoon_rows) - baseline_periods", ""),
    "vertical_delta": ("period_delta * row_pitch", "mm"),
    "grid_margin": ("if(day_count >= 7; 14 mm; grid_core_margin)", "mm"),
    "min_gap": ("if(day_count >= 7; 1 mm; min_column_gap)", "mm"),
    "card_length": ("if(auto_card_length == 1; (if(day_count >= 7; max_board_width - 2 * wave_amplitude; core_width_ref) - 2 * grid_margin - (day_count - 1) * min_gap) / day_count; fixed_card_length)", "mm"),
    "core_width": ("max(core_width_ref; max(2 * grid_margin + day_count * card_length + (day_count - 1) * min_gap; max(subtitle_block_length; slogan_block_length) + 2 * (border_edge_gap + border_width + wave_amplitude + 1 mm)))", "mm"),
    "overall_width": ("core_width + 2 * wave_amplitude", "mm"),
    "body_height": ("baseline_body_h + vertical_delta", "mm"),
    "approx_overall_height": ("227 mm + vertical_delta", "mm"),
    "column_gap": ("if(day_count > 1; (core_width - 2 * grid_margin - day_count * card_length) / (day_count - 1); 0 mm)", "mm"), "grid_left": ("wave_amplitude + grid_margin", "mm"),
    "afternoon_y": ("afternoon_y_ref", "mm"),
    "middle_y": ("middle_y_ref + (effective_afternoon_rows - 5) * row_pitch", "mm"),
    "morning_y": ("morning_y_ref + (effective_afternoon_rows - 5) * row_pitch", "mm"),
    "weekday_y": ("weekday_y_ref + (effective_afternoon_rows + effective_morning_rows - 10) * row_pitch", "mm"),
    "subtitle_y": ("subtitle_y_ref + (effective_afternoon_rows + effective_morning_rows - 10) * row_pitch", "mm"),
    "title_y": ("title_y_ref + (effective_afternoon_rows + effective_morning_rows - 10) * row_pitch", "mm"),
    "magnet_count": ("floor((card_length - 2 * magnet_end_inset) / magnet_center_pitch) + 1", ""),
    "card_height": ("subject_block_total_height - subject_text_relief", "mm"),
}


def validate(parameters):
    """Validate source limits before Fusion creates document geometry."""
    p = dict(DEFAULTS)
    p.update(parameters)
    positive = ("base_thickness", "core_width_ref", "max_board_width", "wave_pitch",
                "card_width", "row_pitch", "magnet_hole_d", "magnet_hole_depth",
                "magnet_center_pitch", "subtitle_block_length", "slogan_block_length",
                "title_size", "title_relief", "corner_radius", "slot_corner_radius", "slot_depth",
                "wave_amplitude", "border_edge_gap", "border_width", "border_relief",
                "subtitle_block_width", "slogan_block_width", "subject_text_relief")
    if any(not math.isfinite(float(p[name])) or float(p[name]) <= 0 for name in positive):
        raise ValueError("Kích thước phải là số dương hữu hạn.")
    for name in ("day_count", "morning_periods", "afternoon_periods"):
        if not math.isfinite(float(p[name])) or float(p[name]) != int(p[name]):
            raise ValueError(name + " phải là số nguyên hữu hạn.")
    if p["slot_tolerance"] < 0:
        raise ValueError("slot_tolerance không được âm.")
    if p["detachable_block_total_height"] - p["title_relief"] <= p["magnet_hole_depth"]:
        raise ValueError("Thân bảng tên không đủ dày cho hốc nam châm.")
    if p["subject_block_total_height"] - p["subject_text_relief"] <= p["magnet_hole_depth"]:
        raise ValueError("Thân thẻ không đủ dày cho hốc nam châm.")
    if not 1 <= int(p["day_count"]) <= 7:
        raise ValueError("day_count phải nằm trong 1..7.")
    if int(p["morning_periods"]) < 0 or int(p["afternoon_periods"]) < 0:
        raise ValueError("Số tiết không được âm.")
    if not int(p["show_morning"]) and not int(p["show_afternoon"]):
        raise ValueError("Phải bật ít nhất một buổi.")
    if p["magnet_hole_depth"] + p["slot_depth"] >= p["base_thickness"]:
        raise ValueError("Hốc nam châm không được xuyên qua bảng.")
    if p["magnet_hole_d"] > p["card_width"]:
        raise ValueError("Đường kính nam châm vượt chiều rộng thẻ.")
    if p["fixed_card_length"] < 2 * p["magnet_end_inset"] + p["magnet_hole_d"]:
        raise ValueError("Thẻ cố định không đủ chỗ cho hốc nam châm.")
    result = layout(p, _validate=False)
    if 2 * p["slot_corner_radius"] >= min(p["card_width"], result["card_length"],
                                          p["subtitle_block_width"], p["subtitle_block_length"],
                                          p["slogan_block_width"], p["slogan_block_length"], 23.4):
        raise ValueError("slot_corner_radius phải nhỏ hơn nửa cạnh ngắn của các rectangle.")
    if 2 * p["corner_radius"] >= min(result["core_width"],
                                     result["body_height"] - 2 * p["wave_amplitude"]):
        raise ValueError("corner_radius quá lớn: không còn đoạn mép để tạo cung sóng.")
    if result["overall_width"] > p["max_board_width"] + 1e-9:
        raise ValueError("Bảng vượt max_board_width.")
    if result["card_length"] <= 2 * p["magnet_end_inset"] + p["magnet_hole_d"]:
        raise ValueError("Chiều dài thẻ không đủ chỗ cho hốc nam châm.")
    if result["column_gap"] < 0:
        raise ValueError("Các cột không vừa bảng; tăng max_board_width hoặc giảm card_length.")
    return result


def layout(parameters, _validate=True):
    """Return the SCAD-equivalent layout in millimetres for offline checks."""
    p = dict(DEFAULTS)
    p.update(parameters)
    if _validate:
        validate(p)
    days = int(p["day_count"])
    morning = int(p["morning_periods"]) if int(p["show_morning"]) else 0
    afternoon = int(p["afternoon_periods"]) if int(p["show_afternoon"]) else 0
    margin = 14.0 if days >= 7 else p["grid_core_margin"]
    gap_min = 1.0 if days >= 7 else p["min_column_gap"]
    available = (p["max_board_width"] - 2 * p["wave_amplitude"]
                 if days >= 7 and int(p["auto_card_length"]) else p["core_width_ref"])
    card = ((available - 2 * margin - max(days - 1, 0) * gap_min) / days
            if int(p["auto_card_length"]) else p["fixed_card_length"])
    core_width = max(p["core_width_ref"],
                     2 * margin + days * card + max(days - 1, 0) * gap_min,
                     p["subtitle_block_length"] + 2 * (p["border_edge_gap"] + p["border_width"] + p["wave_amplitude"] + 1),
                     p["slogan_block_length"] + 2 * (p["border_edge_gap"] + p["border_width"] + p["wave_amplitude"] + 1))
    overall_width = core_width + 2 * p["wave_amplitude"]
    gap = ((core_width - 2 * margin - days * card) / (days - 1) if days > 1 else 0.0)
    afternoon_delta, morning_delta = afternoon - 5, morning - 5
    return {
        "days": days, "morning_rows": morning, "afternoon_rows": afternoon,
        "core_width": core_width, "overall_width": overall_width,
        "card_length": card, "column_gap": gap, "grid_left": p["wave_amplitude"] + margin,
        "body_height": p["baseline_body_h"] + (morning + afternoon - p["baseline_periods"]) * p["row_pitch"],
        "approx_overall_height": 227.0 + (morning + afternoon - p["baseline_periods"]) * p["row_pitch"],
        "afternoon_y": p["afternoon_y_ref"],
        "middle_y": p["middle_y_ref"] + afternoon_delta * p["row_pitch"],
        "morning_y": p["morning_y_ref"] + afternoon_delta * p["row_pitch"],
        "weekday_y": p["weekday_y_ref"] + (afternoon_delta + morning_delta) * p["row_pitch"],
        "subtitle_y": p["subtitle_y_ref"] + (afternoon_delta + morning_delta) * p["row_pitch"],
        "title_y": p["title_y_ref"] + (afternoon_delta + morning_delta) * p["row_pitch"],
        "magnet_count": math.floor((card - 2 * p["magnet_end_inset"]) / p["magnet_center_pitch"]) + 1,
        "effective_morning_rows": morning, "effective_afternoon_rows": afternoon,
    }


def subject_sheet_layout(parameters):
    p = dict(DEFAULTS)
    p.update(parameters)
    result = layout(p)
    # Detached cards use a documented fixed five-column sheet.  Their
    # positions are still expressions of card_length and subject_sheet_gap.
    cols = 5
    cards, count = [], result["magnet_count"]
    for index, label in enumerate(SUBJECT_LABELS):
        x = (index % cols) * (result["card_length"] + p["subject_sheet_gap"])
        y = (index // cols) * (p["card_width"] + p["subject_sheet_gap"])
        first = (result["card_length"] - (count - 1) * p["magnet_center_pitch"]) / 2
        cards.append({"index": index, "label": label, "x": x, "y": y,
                      "magnet_x": [first + n * p["magnet_center_pitch"] for n in range(count)]})
    return {"columns": cols, "cards": cards}


def derived_values(parameters):
    """Evaluate the ACTUAL Fusion expression strings, using lazy if branches."""
    class Conditional(ast.NodeTransformer):
        def visit_Call(self,node):
            self.generic_visit(node)
            if isinstance(node.func,ast.Name) and node.func.id=='_if':
                return ast.copy_location(ast.IfExp(node.args[0],node.args[1],node.args[2]),node)
            return node
    values=dict(DEFAULTS,**parameters)
    for name,(expression,_) in DERIVED.items():
        expr=expression.replace(' mm','').replace('if(','_if(').replace(';',',')
        tree=Conditional().visit(ast.parse(expr,mode='eval'))
        ast.fix_missing_locations(tree)
        values[name]=eval(compile(tree,'<Fusion expression>','eval'),
                          {'__builtins__':{},'floor':math.floor,'max':max,'min':min},values)
    return values

def analytic_outline_plan(p):
    """Return the compact native-arc plan used by the Fusion builder.

    Each straight edge is made from circular scallops whose chord is the
    actual pitch after the run-time count is selected.  The radius is the
    circular-arc radius for the requested sagitta (``wave_amplitude``), not a
    polyline sample.  The final inner boundary uses Fusion's associative
    offset constraint, which may trim/change topology at scallop junctions.
    """
    result = layout(p, _validate=False)
    horizontal_length = result["core_width"] - 2 * p["corner_radius"]
    vertical_length = result["body_height"] - 2 * p["wave_amplitude"] - 2 * p["corner_radius"]
    horizontal_count = max(1, round(horizontal_length / p["wave_pitch"]))
    vertical_count = max(1, round(vertical_length / p["wave_pitch"]))
    horizontal_pitch = horizontal_length / horizontal_count
    vertical_pitch = vertical_length / vertical_count
    amp = p["wave_amplitude"]
    horizontal_radius = horizontal_pitch * horizontal_pitch / (8 * amp) + amp / 2
    vertical_radius = vertical_pitch * vertical_pitch / (8 * amp) + amp / 2
    return {
        "kind": "analytic-arcs",
        "horizontal_count": horizontal_count,
        "vertical_count": vertical_count,
        "horizontal_pitch": horizontal_pitch,
        "vertical_pitch": vertical_pitch,
        "horizontal_radius": horizontal_radius,
        "vertical_radius": vertical_radius,
        "scallop_radius": min(horizontal_radius, vertical_radius),
        "bounds": (0.0, result["overall_width"], 0.0, result["body_height"]),
    }


def _arc_spec(center, start, sweep, center_x, center_y, radius_expression,
              expected_end):
    return {"center": center, "start": start, "sweep": sweep,
            "center_x": center_x, "center_y": center_y,
            "radius_expression": radius_expression, "end": expected_end}


def _analytic_arc_specs(p):
    """Build native arc descriptors without sampled model vertices."""
    plan = analytic_outline_plan(p)
    result = layout(p, _validate=False)
    amp, corner = p["wave_amplitude"], p["corner_radius"]
    x0, x1 = amp, amp + result["core_width"]
    y0, y1 = amp, result["body_height"] - amp
    cx_l, cx_r = x0 + corner, x1 - corner
    cy_b, cy_t = y0 + corner, y1 - corner
    specs = []
    hp, vp = plan["horizontal_pitch"], plan["vertical_pitch"]
    hr, vr = plan["horizontal_radius"], plan["vertical_radius"]
    hsweep = 2 * math.asin(hp / (2 * hr))
    vsweep = 2 * math.asin(vp / (2 * vr))
    h_pitch_expr = "(core_width - 2 * corner_radius) / {}".format(plan["horizontal_count"])
    v_pitch_expr = "(body_height - 2 * wave_amplitude - 2 * corner_radius) / {}".format(plan["vertical_count"])
    h_radius_expr = "(({} * {}) / (8 * wave_amplitude) + wave_amplitude / 2)".format(h_pitch_expr, h_pitch_expr)
    v_radius_expr = "(({} * {}) / (8 * wave_amplitude) + wave_amplitude / 2)".format(v_pitch_expr, v_pitch_expr)
    for i in range(plan["horizontal_count"]):
        left = cx_l + i * hp
        right = cx_l + (i + 1) * hp
        center = ((left + right) / 2, y0 + hr - amp)
        specs.append(_arc_spec(center, (left, y0), hsweep,
                               "wave_amplitude + corner_radius + ({} + 0.5) * ({})".format(i, h_pitch_expr),
                               "wave_amplitude + ({}) - wave_amplitude".format(h_radius_expr),
                               h_radius_expr, (right, y0)))
    specs.append(_arc_spec((cx_r, cy_b), (cx_r, y0), math.pi / 2,
                           "wave_amplitude + core_width - corner_radius", "wave_amplitude + corner_radius",
                           "corner_radius", (x1, cy_b)))
    for i in range(plan["vertical_count"]):
        bottom = cy_b + i * vp
        top = cy_b + (i + 1) * vp
        center = (x1 - vr + amp, (bottom + top) / 2)
        specs.append(_arc_spec(center, (x1, bottom), vsweep,
                               "wave_amplitude + core_width - ({}) + wave_amplitude".format(v_radius_expr),
                               "wave_amplitude + corner_radius + ({} + 0.5) * ({})".format(i, v_pitch_expr),
                               v_radius_expr, (x1, top)))
    specs.append(_arc_spec((cx_r, cy_t), (x1, cy_t), math.pi / 2,
                           "wave_amplitude + core_width - corner_radius", "body_height - wave_amplitude - corner_radius",
                           "corner_radius", (cx_r, y1)))
    for i in range(plan["horizontal_count"]):
        right = cx_r - i * hp
        left = cx_r - (i + 1) * hp
        center = ((left + right) / 2, y1 - hr + amp)
        specs.append(_arc_spec(center, (right, y1), hsweep,
                               "wave_amplitude + core_width - corner_radius - ({} + 0.5) * ({})".format(i, h_pitch_expr),
                               "body_height - wave_amplitude - ({}) + wave_amplitude".format(h_radius_expr),
                               h_radius_expr, (left, y1)))
    specs.append(_arc_spec((cx_l, cy_t), (cx_l, y1), math.pi / 2,
                           "wave_amplitude + corner_radius", "body_height - wave_amplitude - corner_radius",
                           "corner_radius", (x0, cy_t)))
    for i in range(plan["vertical_count"]):
        top = cy_t - i * vp
        bottom = cy_t - (i + 1) * vp
        center = (x0 + vr - amp, (bottom + top) / 2)
        specs.append(_arc_spec(center, (x0, top), vsweep,
                               "wave_amplitude + ({}) - wave_amplitude".format(v_radius_expr),
                               "body_height - wave_amplitude - corner_radius - ({} + 0.5) * ({})".format(i, v_pitch_expr),
                               v_radius_expr, (x0, bottom)))
    specs.append(_arc_spec((cx_l, cy_b), (x0, cy_b), math.pi / 2,
                           "wave_amplitude + corner_radius", "wave_amplitude + corner_radius",
                           "corner_radius", (cx_l, y0)))
    return specs

def _value(core, expression):
    return core.ValueInput.createByString(expression)


def _collection(core, items):
    result = core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result


def _drive_coordinate(sketch, core, axes, point, axis, expression):
    """Drive one coordinate of a sketch point from a construction datum."""
    coordinate = point.geometry.x if axis == 0 else point.geometry.y
    if abs(coordinate) < 1e-8:
        if axis == 0:
            sketch.geometricConstraints.addVerticalPoints(sketch.originPoint, point)
        else:
            sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint, point)
        return
    dimension = sketch.sketchDimensions.addOffsetDimension(
        axes[axis], point, core.Point3D.create(point.geometry.x + .03,
                                               point.geometry.y + .03, 0), True)
    dimension.parameter.expression = "abs(" + expression + ")"


def _drive_point(sketch, core, axes, point, x_expression, y_expression):
    """Drive one sketch point from the shared construction datums."""
    _drive_coordinate(sketch, core, axes, point, 0, x_expression)
    _drive_coordinate(sketch, core, axes, point, 1, y_expression)


def _add_analytic_loop(sketch, core, fusion, p):
    """Create the board outline from native circular arcs and constraints."""
    axes = _coordinate_axes(sketch, core)
    arcs = []
    specs = _analytic_arc_specs(p)
    for spec in specs:
        center = core.Point3D.create(spec["center"][0] / 10,
                                     spec["center"][1] / 10, 0)
        start = core.Point3D.create(spec["start"][0] / 10,
                                    spec["start"][1] / 10, 0)
        arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(
            center, start, spec["sweep"])
        if arc is None:
            raise RuntimeError("Không tạo được cung native của outline.")
        _drive_point(sketch, core, axes, arc.centerSketchPoint,
                     spec["center_x"], spec["center_y"])
        radius_dimension = sketch.sketchDimensions.addRadialDimension(
            arc, core.Point3D.create(spec["center"][0] / 10 + .03,
                                     spec["center"][1] / 10 + .03, 0))
        radius_dimension.parameter.expression = spec["radius_expression"]
        arcs.append((arc, spec))

    def endpoint(arc, target):
        target = (target[0] / 10, target[1] / 10)
        candidates = (arc.startSketchPoint, arc.endSketchPoint)
        return min(candidates, key=lambda point: (
            (point.geometry.x - target[0]) ** 2 +
            (point.geometry.y - target[1]) ** 2))

    for index, (arc, spec) in enumerate(arcs):
        next_arc, next_spec = arcs[(index + 1) % len(arcs)]
        join_point = spec["end"]
        sketch.geometricConstraints.addCoincident(
            endpoint(arc, join_point), endpoint(next_arc, join_point))
    if not sketch.isFullyConstrained:
        raise RuntimeError("Sketch outline cung tròn chưa đủ ràng buộc.")
    return [arc for arc, _ in arcs]


def _anchored_rectangle_sketch(comp, core, fusion, x, y, width, height, name,
                               plane=None, x_expression=None, y_expression=None,
                               width_expression=None, height_expression=None):
    """Create a parent rectangle, then fillet it without changing its bbox.

    Drive every parent corner from the fixed construction axes.  One-anchor plus
    width/height (or diagonal) dims assumes addTwoPointRectangle installs H/V
    edge constraints; through the Fusion API those are unreliable and leave
    shear DOF.  Fillet still trims only the independent model-copy lines, so
    parent corners stay out of the fillet and the outer bbox remains stable.

    `fusion` is kept for call-site compatibility with other sketch helpers.
    """
    sketch = comp.sketches.add(plane or comp.xYConstructionPlane)
    sketch.name = name
    point = core.Point3D.create
    x_expression = x_expression or "{} mm".format(x)
    y_expression = y_expression or "{} mm".format(y)
    width_expression = width_expression or "{} mm".format(width)
    height_expression = height_expression or "{} mm".format(height)
    x_right = "({}) + ({})".format(x_expression, width_expression)
    y_top = "({}) + ({})".format(y_expression, height_expression)
    axes = _coordinate_axes(sketch, core)
    # Four corners, CCW from lower-left: each gets its own axis offsets so the
    # parent cannot shear even when API edge H/V constraints are missing.
    parent_corners = (
        (x / 10, y / 10, x_expression, y_expression),
        ((x + width) / 10, y / 10, x_right, y_expression),
        ((x + width) / 10, (y + height) / 10, x_right, y_top),
        (x / 10, (y + height) / 10, x_expression, y_top),
    )
    parent_points = []
    for px, py, x_expr, y_expr in parent_corners:
        corner = sketch.sketchPoints.add(point(px, py, 0))
        _drive_point(sketch, core, axes, corner, x_expr, y_expr)
        parent_points.append(corner)
    parent_lines = []
    for index in range(4):
        line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            parent_points[index], parent_points[(index + 1) % 4])
        if line is None:
            raise RuntimeError("Không tạo được parent rectangle: " + name)
        line.isConstruction = True
        parent_lines.append(line)

    # Independent model endpoints: collinear to the driven parent, then fillet.
    # Parent corners are never passed to addFillet.
    model_lines = []
    for index, parent_line in enumerate(parent_lines):
        start = parent_points[index].geometry
        end = parent_points[(index + 1) % 4].geometry
        model_line = sketch.sketchCurves.sketchLines.addByTwoPoints(
            point(start.x, start.y, 0), point(end.x, end.y, 0))
        if model_line is None:
            raise RuntimeError("Không tạo được model rectangle: " + name)
        sketch.geometricConstraints.addCollinear(model_line, parent_line)
        model_lines.append(model_line)
    for index, model_line in enumerate(model_lines):
        sketch.geometricConstraints.addCoincident(
            model_line.endSketchPoint,
            model_lines[(index + 1) % 4].startSketchPoint)

    # Process corners in the line flow order so each subsequent fillet uses
    # the opposite, still-untrimmed endpoint of its shared line.
    for index, line_a in enumerate(model_lines):
        line_b = model_lines[(index + 1) % 4]
        point_a = line_a.endSketchPoint.geometry
        point_b = line_b.startSketchPoint.geometry
        arc = sketch.sketchCurves.sketchArcs.addFillet(
            line_a, point_a, line_b, point_b,
            float(DEFAULTS["slot_corner_radius"] / 10))
        if arc is None:
            raise RuntimeError("Không tạo được fillet parent rectangle: " + name)
        radius_dimension = sketch.sketchDimensions.addRadialDimension(
            arc, core.Point3D.create(arc.centerSketchPoint.geometry.x + .03,
                                     arc.centerSketchPoint.geometry.y + .03, 0))
        radius_dimension.parameter.expression = "slot_corner_radius"
    if not sketch.isFullyConstrained:
        raise RuntimeError("Sketch chưa đủ ràng buộc: " + name)
    return sketch


def _anchored_circle_sketch(comp, core, fusion, x, y, diameter, name, plane,
                            x_expression=None, y_expression=None,
                            diameter_expression=None):
    sketch = comp.sketches.add(plane)
    sketch.name = name
    point = core.Point3D.create
    x_expression = x_expression or "{} mm".format(x)
    y_expression = y_expression or "{} mm".format(y)
    diameter_expression = diameter_expression or "{} mm".format(diameter)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(x / 10, y / 10, 0), diameter / 20)
    axes = _coordinate_axes(sketch,core)
    for axis, expression in enumerate((x_expression, y_expression)):
        dim = sketch.sketchDimensions.addOffsetDimension(
            axes[axis], circle.centerSketchPoint,
            point(x / 10 + 0.3, y / 10 + 0.3, 0),True)
        dim.parameter.expression = 'abs(' + expression + ')'
    diameter_dim = sketch.sketchDimensions.addDiameterDimension(
        circle, point(x / 10 + 0.3, y / 10 + 0.3, 0))
    diameter_dim.parameter.expression = diameter_expression
    if not sketch.isFullyConstrained:
        raise RuntimeError("Sketch chưa đủ ràng buộc: " + name)
    return sketch


def _add_user_parameters(design, core):
    value = core.ValueInput.createByString
    for name, number in DEFAULTS.items():
        units = "" if name in ("day_count", "morning_periods", "afternoon_periods",
                                "show_morning", "show_afternoon", "show_wall_holes",
                                "auto_card_length", "baseline_periods") else "mm"
        design.userParameters.add(name, value(str(number) + (" mm" if units else "")), units,
                                  COMMENTS.get(name, "Tham số nguồn SCAD."))
    for name, (expression, units) in DERIVED.items():
        try:
            design.userParameters.add(name, value(expression), units, "Giá trị tự tính theo tham số nguồn.")
        except Exception as error:
            raise RuntimeError("User Parameter {} = {} [{}]: {}".format(
                name, expression, units or 'unitless', error)) from error


def _rectangle_sketch(comp, core, x, y, width, height, name, plane=None,
                      fusion=None, width_expression=None, height_expression=None,
                      x_expression=None, y_expression=None):
    if fusion is None:
        raise RuntimeError("Rectangle sketches require Fusion dimension orientations.")
    return _anchored_rectangle_sketch(
        comp, core, fusion, x, y, width, height, name, plane,
        x_expression, y_expression, width_expression, height_expression)


def _coordinate_axes(sketch, core):
    """Fixed construction datums; Y datum measures X and X datum measures Y."""
    axes=[]
    for start,end in (((0,-1,0),(0,1,0)),((-1,0,0),(1,0,0))):
        line=sketch.sketchCurves.sketchLines.addByTwoPoints(
            core.Point3D.create(*start),core.Point3D.create(*end))
        line.isConstruction=True
        line.isFixed=True
        # Fixing a line leaves its endpoints free to slide along it in Fusion.
        line.startSketchPoint.isFixed=True
        line.endSketchPoint.isFixed=True
        axes.append(line)
    return axes


def _text_frame_corners(result, text):
    """Return BL/BR/TL/TR and edges from SketchText rectangleLines."""
    lines = result.definition.rectangleLines
    if not lines or len(lines) != 4:
        raise RuntimeError('Text has no native rectangular boundary: ' + text)
    unique = {}
    for line in lines:
        for pt in (line.startSketchPoint, line.endSketchPoint):
            unique[(round(pt.geometry.x, 8), round(pt.geometry.y, 8))] = pt
    if len(unique) != 4:
        raise RuntimeError('Text boundary is not a four-corner rectangle: ' + text)
    xmin = min(x for x, y in unique)
    xmax = max(x for x, y in unique)
    ymin = min(y for x, y in unique)
    ymax = max(y for x, y in unique)
    bl = unique[(xmin, ymin)]
    br = unique[(xmax, ymin)]
    tl = unique[(xmin, ymax)]
    tr = unique[(xmax, ymax)]

    def edge_on(coord_index, value):
        for line in lines:
            a = line.startSketchPoint.geometry
            b = line.endSketchPoint.geometry
            ca = a.x if coord_index == 0 else a.y
            cb = b.x if coord_index == 0 else b.y
            if abs(ca - value) < 1e-6 and abs(cb - value) < 1e-6:
                return line
        raise RuntimeError('Text boundary edge missing for: ' + text)

    return {
        'lines': lines,
        'bl': bl, 'br': br, 'tl': tl, 'tr': tr,
        'bottom': edge_on(1, ymin),
        'left': edge_on(0, xmin),
        'top': edge_on(1, ymax),
        'right': edge_on(0, xmax),
    }


def _try_orientation(sketch, fusion, line, horizontal):
    """Best-effort H/V on a SketchText frame edge.

    Real Fusion: Horizontal(bottom) often succeeds; Vertical(left) then raises
    VCS_SKETCH_OVER_CONSTRAINTS because the text frame already implies
    orientation. Never treat either as required.
    """
    constraint_type = (fusion.HorizontalConstraint if horizontal
                       else fusion.VerticalConstraint)
    try:
        existing = list(line.geometricConstraints)
    except Exception:
        existing = []
    if any(isinstance(c, constraint_type) for c in existing):
        return False
    try:
        if horizontal:
            sketch.geometricConstraints.addHorizontal(line)
        else:
            sketch.geometricConstraints.addVertical(line)
        return True
    except Exception:
        return False


def _add_text(sketch, core, text, height_mm, x_mm, y_mm, width_mm,
              height_expression=None, x_expression=None, y_expression=None,
              width_expression=None):
    """Add a native SketchTexts text block (Fusion 2026 createInput3 API).

    SketchText is not a free construction rectangle. Fusion owns glyph height
    via heightParameter and keeps rectangleLines as a structured text frame.
    Rectangle recipes oscillate in real Fusion:

      - one-anchor + width/height distance dims → under-constrained
      - drive all 4 corners (8 offsets) → VCS_SKETCH_OVER_CONSTRAINTS at TR
      - BL + required H + required V + BR.x + TL.y → OVER at addVertical(left)
        after Horizontal(bottom) already succeeded (V implied by text frame)

    Fusion-safe recipe:
      1. heightParameter → glyph height (parametric)
      2. drive BL (x, y) → position
      3. try H(bottom) / V(left) best-effort only — never required
      4. drive BR.x + TL.y → frame width / 1.5× height pad
      5. never drive TR; never drive BR.y or TL.x
      6. validate structure only — do NOT require full sketch lock
         (editable SketchText often stays unlocked in the browser)
    """
    import adsk.fusion as fusion
    texts = sketch.sketchTexts  # SketchTexts API collection
    quoted = "'{}'".format(text.replace("'", "''"))
    height_value = _value(core, "{} mm".format(height_mm))
    corner_a = core.Point3D.create(x_mm / 10, y_mm / 10, 0)
    corner_b = core.Point3D.create((x_mm + width_mm) / 10,
                                   (y_mm + height_mm * 1.5) / 10, 0)
    # Recreate the input on each attempt: a rejected fontName fails on add().
    last_error = None
    result = None
    for font_name in FUSION_TEXT_FONTS:
        inp = texts.createInput3(quoted, height_value)
        inp.setAsMultiLine(
            corner_a, corner_b,
            core.HorizontalAlignments.CenterHorizontalAlignment,
            core.VerticalAlignments.MiddleVerticalAlignment, 0)
        inp.fontName = font_name
        try:
            result = texts.add(inp)
            break
        except Exception as err:
            last_error = err
    if result is None:
        raise RuntimeError(
            "Fusion rejected all text fonts {}; last error: {}".format(
                FUSION_TEXT_FONTS, last_error))
    height_expr = height_expression or "{} mm".format(height_mm)
    width_expr = width_expression or "{} mm".format(width_mm)
    x_expr = x_expression or "{} mm".format(x_mm)
    y_expr = y_expression or "{} mm".format(y_mm)
    result.heightParameter.expression = height_expr

    frame = _text_frame_corners(result, text)
    # Box height is 1.5× glyph height so multiline padding stays parametric.
    x_right = "({}) + ({})".format(x_expr, width_expr)
    y_top = "({}) + (({}) * 1.5)".format(y_expr, height_expr)
    axes = _coordinate_axes(sketch, core)

    # Position, optional orientation, then the two free size axes only.
    _drive_point(sketch, core, axes, frame['bl'], x_expr, y_expr)
    _try_orientation(sketch, fusion, frame['bottom'], True)
    _try_orientation(sketch, fusion, frame['left'], False)
    _drive_coordinate(sketch, core, axes, frame['br'], 0, x_right)
    _drive_coordinate(sketch, core, axes, frame['tl'], 1, y_top)
    _try_orientation(sketch, fusion, frame['top'], True)
    _try_orientation(sketch, fusion, frame['right'], False)

    # Structural contract only — SketchText DOF is not a free rectangle.
    if not result.heightParameter.expression:
        raise RuntimeError('Text heightParameter missing: ' + text)
    if len(frame['lines']) != 4:
        raise RuntimeError('Text frame lost rectangleLines: ' + text)
    return result


def _extrude(comp, fusion, core, sketch, operation, distance, name, target=None):
    profiles = _collection(core, [sketch.profiles.item(i) for i in range(sketch.profiles.count)])
    if profiles.count == 0:
        raise RuntimeError("{}: sketch không có profile kín.".format(name))
    inp = comp.features.extrudeFeatures.createInput(profiles, operation)
    inp.setOneSideExtent(fusion.DistanceExtentDefinition.create(_value(core, distance)),
                         fusion.ExtentDirections.PositiveExtentDirection)
    if target is not None:
        inp.participantBodies = [target]
    try:
        feature = comp.features.extrudeFeatures.add(inp)
    except Exception as error:
        raise RuntimeError('Extrude failed: '+name) from error
    feature.name, sketch.isVisible = name, False
    return feature


def _extrude_entity(comp, fusion, core, entity, operation, distance, name, target=None):
    """Extrude a Profile or ObjectCollection of Profiles (not SketchText).

    SketchText is a separate sketch entity: it does not appear in
    sketch.profiles, and Fusion rejects both createInput+setOneSideExtent and
    addSimple(SketchText) with "Some input argument is invalid" on our
    createInput3 multiline board labels. Use _extrude_text_glyphs for text.
    """
    distance_value = _value(core, distance)
    try:
        if target is None:
            feature = comp.features.extrudeFeatures.addSimple(
                entity, distance_value, operation)
        else:
            inp = comp.features.extrudeFeatures.createInput(entity, operation)
            inp.setOneSideExtent(
                fusion.DistanceExtentDefinition.create(distance_value),
                fusion.ExtentDirections.PositiveExtentDirection)
            inp.participantBodies = [target]
            feature = comp.features.extrudeFeatures.add(inp)
    except Exception as error:
        raise RuntimeError('Extrude failed: '+name) from error
    feature.name = name
    return feature


def _extrude_text_glyphs(comp, fusion, core, text, sketch, operation, distance,
                         name, target=None):
    """Raise lettering by exploding SketchText into closed glyph Profiles.

    Exact reason addSimple(SketchText) fails here: SketchText is not a Profile.
    Docs list SketchText as a legal addSimple/createInput argument, but real
    Fusion still returns error 3 for createInput3 multiline text after frame
    drives. Forum workaround that matches Profile extrudes (scallop ring):

      1. nudge text into a finished compute state
      2. text.explode() → glyph curves (deletes SketchText)
      3. sketch.profiles now holds closed glyph loops
      4. addSimple / createInput those Profiles

    Keeps Vietnamese + Arial outlines baked at explode time. Glyph sketches
    are named "* glyph sketch" so _check_model can exempt them (no SketchText
    left, and explode curves are not fully constrained).
    """
    # API quirk: unfinished SketchText can explode to zero curves until touched.
    try:
        text.isHorizontalFlip = text.isHorizontalFlip
    except Exception:
        pass
    curves = text.explode()
    if not curves:
        raise RuntimeError(
            '{}: SketchText.explode produced no curves (font/glyphs?).'.format(
                name))
    if sketch.profiles.count == 0:
        raise RuntimeError(
            '{}: no closed glyph profiles after explode.'.format(name))
    profiles = _collection(
        core, [sketch.profiles.item(i) for i in range(sketch.profiles.count)])
    sketch.name = name + ' glyph sketch'
    feature = _extrude_entity(
        comp, fusion, core, profiles, operation, distance, name, target)
    sketch.isVisible = False
    return feature


def _join_body(comp, fusion, core, target, tools, name):
    inp = comp.features.combineFeatures.createInput(target, _collection(core, tools))
    inp.operation = fusion.FeatureOperations.JoinFeatureOperation
    inp.isKeepToolBodies = False
    result = comp.features.combineFeatures.add(inp)
    result.name = name
    return result.bodies.item(0)


def _cut_body(comp, fusion, core, target, tools, name):
    """Subtract tool bodies from target; tools are consumed."""
    inp = comp.features.combineFeatures.createInput(target, _collection(core, tools))
    inp.operation = fusion.FeatureOperations.CutFeatureOperation
    inp.isKeepToolBodies = False
    result = comp.features.combineFeatures.add(inp)
    result.name = name
    return result.bodies.item(0)


def _bodies_of(feature):
    return [feature.bodies.item(index) for index in range(feature.bodies.count)]


def _pattern_feature(comp, fusion, core, feature, axis, quantity, distance, name,
                     second_axis=None, second_quantity=None, second_distance=None):
    patterns = comp.features.rectangularPatternFeatures
    inp = patterns.createInput(_collection(core, [feature]), axis,
                               _value(core, quantity), _value(core, distance),
                               fusion.PatternDistanceType.SpacingPatternDistanceType)
    if second_axis is not None:
        inp.setDirectionTwo(second_axis, _value(core, second_quantity),
                            _value(core, second_distance))
    # Identical: copy pocket Cut features as-is. Optimized/Adjust can fail with
    # PATTERN_FEATURES_NO_PASTE_INT_EDGES when paste edges are missing.
    # Blind magnet Cuts still fail even with Identical — use _pattern_bodies.
    inp.patternComputeOption = fusion.PatternComputeOptions.IdenticalPatternCompute
    result = patterns.add(inp)
    result.name = name
    return result


def _pattern_bodies(comp, fusion, core, bodies, axis, quantity, distance, name,
                    second_axis=None, second_quantity=None, second_distance=None):
    """Pattern solid bodies. Skips feature paste/intersect (magnet Cut path)."""
    patterns = comp.features.rectangularPatternFeatures
    inp = patterns.createInput(_collection(core, bodies), axis,
                               _value(core, quantity), _value(core, distance),
                               fusion.PatternDistanceType.SpacingPatternDistanceType)
    if second_axis is not None:
        inp.setDirectionTwo(second_axis, _value(core, second_quantity),
                            _value(core, second_distance))
    result = patterns.add(inp)
    result.name = name
    return result


def _offset_plane(comp, core, expression, name):
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(comp.xYConstructionPlane, _value(core, expression))
    plane = comp.constructionPlanes.add(inp)
    plane.name, plane.isLightBulbOn = name, False
    return plane



def _build_board(design, fusion, core, p, layout_result):
    comp = design.rootComponent
    width, height = layout_result["overall_width"], layout_result["body_height"]
    outline=comp.sketches.add(comp.xYConstructionPlane)
    outline.name='Analytic scallop board outline'
    _add_analytic_loop(outline, core, fusion, p)
    board_feature=_extrude(comp,fusion,core,outline,fusion.FeatureOperations.NewBodyFeatureOperation,
                           'base_thickness','Main board')
    board=board_feature.bodies.item(0)
    board.name='Timetable board'
    if int(p["show_wall_holes"]):
        margin = p["wall_hole_margin"] + p["wave_amplitude"]
        for index, x_expression in enumerate((
                "wave_amplitude + wall_hole_margin",
                "wave_amplitude + core_width - wall_hole_margin")):
            sketch = _anchored_circle_sketch(
                comp, core, fusion, margin if index == 0 else width - margin,
                height - margin, p["wall_hole_d"], "Wall hole {}".format(index + 1),
                comp.xYConstructionPlane, x_expression,
                "wave_amplitude + body_height - wall_hole_margin", "wall_hole_d")
            cut = _extrude(comp, fusion, core, sketch, fusion.FeatureOperations.CutFeatureOperation,
                     "base_thickness", "Wall hanging hole {}".format(index + 1), board)
            board = cut.bodies.item(0)

    slot_floor = _offset_plane(comp, core, "base_thickness - slot_depth", "Board slot floor")
    magnet_plane = _offset_plane(comp, core,
                                 "base_thickness - slot_depth - magnet_hole_depth",
                                 "Board magnet plane")
    grid_left = layout_result["grid_left"]

    def schedule_pattern(y, rows, y_expression, name):
        nonlocal board
        seed = _rectangle_sketch(
            comp, core, grid_left, y, layout_result["card_length"], p["card_width"],
            name + " seed", slot_floor, fusion=fusion,
            x_expression="grid_left - slot_tolerance / 2",
            y_expression="({}) - slot_tolerance / 2".format(y_expression),
            width_expression="card_length + slot_tolerance",
            height_expression="card_width + slot_tolerance")
        cut = _extrude(comp, fusion, core, seed, fusion.FeatureOperations.CutFeatureOperation,
                       "slot_depth", name + " seed cut", board)
        board = cut.bodies.item(0)
        pattern = _pattern_feature(comp, fusion, core, cut, comp.xConstructionAxis,
                                "day_count", "card_length + column_gap", name + " columns",
                                comp.yConstructionAxis,
                                "effective_{}_rows".format("afternoon" if y_expression == "afternoon_y" else "morning"),
                                "row_pitch")
        board = pattern.bodies.item(0)
        board.name = "Timetable board"
        return pattern

    if layout_result["afternoon_rows"]:
        schedule_pattern(layout_result["afternoon_y"], layout_result["afternoon_rows"],
                         "afternoon_y", "Afternoon schedule pockets")
    if layout_result["morning_rows"]:
        schedule_pattern(layout_result["morning_y"], layout_result["morning_rows"],
                         "morning_y", "Morning schedule pockets")

    for x, y, w, h, x_expression, y_expression, w_expression, h_expression, name in ((
        (width - p["subtitle_block_length"]) / 2, layout_result["subtitle_y"],
        p["subtitle_block_length"], p["subtitle_block_width"],
        "(overall_width - subtitle_block_length) / 2", "subtitle_y",
        "subtitle_block_length", "subtitle_block_width", "Name plaque pocket"),
        ((width - p["slogan_block_length"]) / 2, layout_result["middle_y"],
         p["slogan_block_length"], p["slogan_block_width"],
         "(overall_width - slogan_block_length) / 2", "middle_y",
         "slogan_block_length", "slogan_block_width", "Slogan plaque pocket"),):
        sketch = _rectangle_sketch(comp, core, x, y, w, h, name, slot_floor,
                                   fusion=fusion, x_expression=x_expression,
                                   y_expression=y_expression, width_expression=w_expression,
                                   height_expression=h_expression)
        cut = _extrude(comp, fusion, core, sketch, fusion.FeatureOperations.CutFeatureOperation,
                 "slot_depth", name, board)
        board = cut.bodies.item(0)
        first = "({}) + ({} - floor(({} - 2 * magnet_end_inset) / magnet_center_pitch) * magnet_center_pitch) / 2".format(x_expression,w_expression,w_expression)
        seed = _anchored_circle_sketch(comp, core, fusion, x+w/2, y+h/2,
            p["magnet_hole_d"], name+" magnet seed", magnet_plane, first,
            "({}) + ({}) / 2".format(y_expression,h_expression), "magnet_hole_d")
        # NewBody tool + body pattern + combine-cut: patterning Cut features of
        # these blind magnet holes fails with PATTERN_FEATURES_NO_PASTE_INT_EDGES
        # even when IdenticalPatternCompute is set (R-Pattern on plaque X count).
        tool = _extrude(comp, fusion, core, seed,
                        fusion.FeatureOperations.NewBodyFeatureOperation,
                        "magnet_hole_depth", name+" magnet seed tool")
        pattern = _pattern_bodies(
            comp, fusion, core, _bodies_of(tool), comp.xConstructionAxis,
            "floor(({} - 2 * magnet_end_inset) / magnet_center_pitch) + 1".format(w_expression),
            "magnet_center_pitch", name+" magnet recesses")
        board = _cut_body(comp, fusion, core, board, _bodies_of(pattern),
                          name+" magnet cut")
        board.name = "Timetable board"

    def magnet_pattern(y, rows, y_expression, name):
        # NewBody seed → pattern magnets along X → 2D days×rows of those bodies
        # → one combine-cut. Avoids Cut-feature paste edges on pocket floors.
        nonlocal board
        count = layout_result["magnet_count"]
        first = (layout_result["card_length"] - (count - 1) * p["magnet_center_pitch"]) / 2
        x = grid_left + first
        x_expression = "grid_left + (card_length - (magnet_count - 1) * magnet_center_pitch) / 2"
        seed = _anchored_circle_sketch(comp, core, fusion, x, y + p["card_width"] / 2,
                                       p["magnet_hole_d"], name + " seed", magnet_plane,
                                       x_expression, "{} + card_width / 2".format(y_expression),
                                       "magnet_hole_d")
        tool = _extrude(comp, fusion, core, seed,
                        fusion.FeatureOperations.NewBodyFeatureOperation,
                        "magnet_hole_depth + slot_depth", name + " seed tool")
        magnets = _pattern_bodies(comp, fusion, core, _bodies_of(tool),
                                  comp.xConstructionAxis, "magnet_count",
                                  "magnet_center_pitch", name + " magnets")
        grid = _pattern_bodies(
            comp, fusion, core, _bodies_of(magnets), comp.xConstructionAxis,
            "day_count", "card_length + column_gap", name + " days",
            comp.yConstructionAxis,
            "effective_{}_rows".format(
                "afternoon" if y_expression == "afternoon_y" else "morning"),
            "row_pitch")
        board = _cut_body(comp, fusion, core, board, _bodies_of(grid),
                          name + " cut")
        board.name = "Timetable board"
        return grid

    if layout_result["afternoon_rows"]:
        magnet_pattern(layout_result["afternoon_y"], layout_result["afternoon_rows"],
                       "afternoon_y", "Afternoon magnet recesses")
    if layout_result["morning_rows"]:
        magnet_pattern(layout_result["morning_y"], layout_result["morning_rows"],
                       "morning_y", "Morning magnet recesses")
    return board


def _build_trim(design, fusion, core, p, layout_result, board):
    comp = design.rootComponent
    plane = _offset_plane(comp, core, 'base_thickness', 'Raised trim plane')
    sketch = comp.sketches.add(plane)
    sketch.name = 'Associative scallop trim profile'
    parent_curves = _add_analytic_loop(sketch, core, fusion, p)
    constraints = sketch.geometricConstraints
    outer_input = constraints.createOffsetInput(
        parent_curves, _value(core, '-border_edge_gap'))
    if outer_input is None:
        raise RuntimeError('Không tạo được offset ngoài của viền.')
    outer_input.isTopologyMatched = False
    outer_offset = constraints.addOffset2(outer_input)
    if outer_offset is None or not outer_offset.childCurves:
        raise RuntimeError('Offset ngoài không trả về curve con.')
    outer_offset.dimension.parameter.expression = '-border_edge_gap'
    # Offset childCurves are not guaranteed to retain the parent's flow order.
    # Build the inner edge from the same ordered loop so the two expressions
    # stay independent and the ring remains associative when topology changes.
    inner_input = constraints.createOffsetInput(
        parent_curves, _value(core, '-(border_edge_gap + border_width)'))
    if inner_input is None:
        raise RuntimeError('Không tạo được offset trong của viền.')
    inner_input.isTopologyMatched = False
    inner_offset = constraints.addOffset2(inner_input)
    if inner_offset is None or not inner_offset.childCurves:
        raise RuntimeError('Offset trong không trả về curve con.')
    inner_offset.dimension.parameter.expression = '-(border_edge_gap + border_width)'
    if not sketch.isFullyConstrained:
        raise RuntimeError('Sketch viền offset chưa đủ ràng buộc.')
    rings = [profile for profile in sketch.profiles if profile.profileLoops.count == 2]
    if not rings:
        raise RuntimeError('Expected an associative offset ring profile.')
    # The source loop remains in the sketch to keep both offsets associative.
    # Pick the narrowest annular profile, which is the border_width band.
    ring = min(rings, key=lambda profile: profile.areaProperties().area)
    feature = _extrude_entity(comp, fusion, core, ring,
                              fusion.FeatureOperations.NewBodyFeatureOperation,
                              'border_relief', 'Raised associative scallop ring')
    return _join_body(comp, fusion, core, board, list(feature.bodies),
                      'Join raised associative scallop ring')

def _build_board_labels_native(design, fusion, core, p, layout_result, board):
    """Join each native SketchText extrusion into the board body."""
    comp = design.rootComponent
    width = layout_result["overall_width"]
    text_plane = _offset_plane(comp, core, "base_thickness - 0.01 mm",
                               "Board label text plane")
    support = _rectangle_sketch(
        comp, core, width / 2 - 60, layout_result["body_height"] - 12.6, 120, 23.4,
        "Title backing native", fusion=fusion,
        x_expression="(overall_width - 120 mm) / 2",
        y_expression="body_height - 12.6 mm", width_expression="120 mm",
        height_expression="23.4 mm")
    support_feature = _extrude(comp, fusion, core, support,
                               fusion.FeatureOperations.JoinFeatureOperation,
                               "base_thickness", "Title backing native")
    # At this stage the board is the only existing solid.  A native Join
    # keeps the backing in the same body and removes a separate Combine step.
    board = support_feature.bodies.item(0)

    def text_join(label, height, x, y, text_width, name, x_expr, y_expr,
                  width_expr):
        nonlocal board
        sketch = comp.sketches.add(text_plane)
        sketch.name = name + " sketch"
        text = _add_text(sketch, core, label, height, x, y, text_width,
                         x_expression=x_expr, y_expression=y_expr,
                         width_expression=width_expr, height_expression="title_size" if name=="Native title" else "6 mm")
        # SketchText is not a Profile — explode glyphs, NewBody, Combine Join.
        feature = _extrude_text_glyphs(
            comp, fusion, core, text, sketch,
            fusion.FeatureOperations.NewBodyFeatureOperation,
            "border_relief", name)
        board = _join_body(comp, fusion, core, board, list(feature.bodies),
                           "Join " + name)

    text_join("Thời khóa biểu", p["title_size"], width / 2 - 60,
              layout_result["title_y"] - 9, 120, "Native title",
              "(overall_width - 120 mm) / 2", "title_y - 9 mm", "120 mm")
    names = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")
    for col in range(layout_result["days"]):
        x = (layout_result["grid_left"] + col *
             (layout_result["card_length"] + layout_result["column_gap"]) +
             layout_result["card_length"] / 2 - 8)
        text_join(names[col], 6, x, layout_result["weekday_y"] - 3, 16,
                  "Native weekday {}".format(col + 1),
                  "grid_left + {} * (card_length + column_gap) + card_length / 2 - 8 mm".format(col),
                  "weekday_y - 3 mm", "16 mm")
    if layout_result["morning_rows"]:
        text_join("Sáng", 6, 3,
                  layout_result["morning_y"] + (layout_result["morning_rows"] - 1) * p["row_pitch"] / 2,
                  14, "Native morning label", "wave_amplitude + border_width",
                  "morning_y + (effective_morning_rows - 1) * row_pitch / 2", "14 mm")
    if layout_result["afternoon_rows"]:
        text_join("Chiều", 6, 3,
                  layout_result["afternoon_y"] + (layout_result["afternoon_rows"] - 1) * p["row_pitch"] / 2,
                  14, "Native afternoon label", "wave_amplitude + border_width",
                  "afternoon_y + (effective_afternoon_rows - 1) * row_pitch / 2", "14 mm")
    return board


def _build_plaque_native(design, fusion, core, p, label, width, height, x, y,
                         name, width_expression, y_expression, text_plane=None):
    """Build a plaque base and its raised text as separate native features."""
    comp = design.rootComponent
    height_expression = "subtitle_block_width" if width_expression == "subtitle_block_length" else "slogan_block_width"
    base = _rectangle_sketch(comp, core, x, y, width, height, name + " native outline",
                             fusion=fusion,
                             x_expression="(overall_width - {}) / 2".format(width_expression),
                             y_expression=y_expression, width_expression=width_expression,
                             height_expression=height_expression)
    base_feature = _extrude(comp, fusion, core, base,
                            fusion.FeatureOperations.NewBodyFeatureOperation,
                            "detachable_block_total_height - title_relief", name + " native")
    body = base_feature.bodies.item(0)
    body.name = name
    if text_plane is None:
        text_plane = _offset_plane(comp, core,
                                   "detachable_block_total_height - title_relief",
                                   "Detachable text plane")
    text_sketch = comp.sketches.add(text_plane)
    text = _add_text(text_sketch, core, label, min(height * 0.55, 8), x + 1,
                     y + height * 0.2, width - 2,
                     x_expression="(overall_width - {}) / 2 + 1 mm".format(width_expression),
                     y_expression="{} + ({} - {} mm * 1.5) / 2".format(y_expression,height_expression,min(height*.55,8)),
                     width_expression="{} - 2 mm".format(width_expression))
    raised = _extrude_text_glyphs(
        comp, fusion, core, text, text_sketch,
        fusion.FeatureOperations.NewBodyFeatureOperation,
        "title_relief", name + " native raised text")
    body = _join_body(comp, fusion, core, body, list(raised.bodies), name + " native text join")
    first = "(overall_width - {}) / 2 + ({} - (floor(({} - 2 * magnet_end_inset) / magnet_center_pitch)) * magnet_center_pitch) / 2".format(
        width_expression, width_expression, width_expression)
    seed = _anchored_circle_sketch(
        comp, core, fusion, x + width / 2, y + height / 2,
        p["magnet_hole_d"], name + " native magnet seed", comp.xYConstructionPlane,
        first, "{} + {} / 2".format(y_expression, height_expression), "magnet_hole_d")
    tool = _extrude(comp, fusion, core, seed,
                    fusion.FeatureOperations.NewBodyFeatureOperation,
                    "magnet_hole_depth", name + " native magnet seed tool")
    pattern = _pattern_bodies(
        comp, fusion, core, _bodies_of(tool), comp.xConstructionAxis,
        "floor(({} - 2 * magnet_end_inset) / magnet_center_pitch) + 1".format(width_expression),
        "magnet_center_pitch", name + " native magnet recesses")
    result = _cut_body(comp, fusion, core, body, _bodies_of(pattern),
                       name + " native magnet cut")
    result.name = body.name
    return result


def _build_subject_card_native(design, fusion, core, p, label, index, x, y, length,
                               text_plane=None):
    """Build one detached subject card with separately raised native text."""
    comp = design.rootComponent
    column, row = index % 5, index // 5
    y = layout(p)["body_height"] + 100 + row * (p["card_width"]+p["subject_sheet_gap"])
    x_expression = "{} * (card_length + subject_sheet_gap)".format(column)
    y_expression = "body_height + 100 mm + {} * (card_width + subject_sheet_gap)".format(row)
    base = _rectangle_sketch(comp, core, x, y, length, p["card_width"],
                             "Subject {:02d} native card".format(index + 1), fusion=fusion,
                             x_expression=x_expression, y_expression=y_expression,
                             width_expression="card_length", height_expression="card_width")
    feature = _extrude(comp, fusion, core, base,
                       fusion.FeatureOperations.NewBodyFeatureOperation, "card_height",
                       "Subject {:02d} native {}".format(index + 1, label))
    body = feature.bodies.item(0)
    body.name = "Subject {:02d} - {}".format(index + 1, label)
    if text_plane is None:
        text_plane = _offset_plane(comp, core, "card_height", "Subject text plane")
    text_sketch = comp.sketches.add(text_plane)
    text = _add_text(text_sketch, core, label, min(p["card_width"] * 0.48, 6),
                     x + 1, y + 2, length - 2,
                     x_expression="({}) + 1 mm".format(x_expression),
                     y_expression="({}) + 2 mm".format(y_expression),
                     width_expression="card_length - 2 mm")
    raised = _extrude_text_glyphs(
        comp, fusion, core, text, text_sketch,
        fusion.FeatureOperations.NewBodyFeatureOperation,
        "subject_text_relief",
        "Subject {:02d} native raised text".format(index + 1))
    body = _join_body(comp, fusion, core, body, list(raised.bodies),
               "Join subject {:02d} native text".format(index + 1))
    seed = _anchored_circle_sketch(
        comp, core, fusion, x + length / 2, y + p["card_width"] / 2,
        p["magnet_hole_d"], "Subject {:02d} native magnet seed".format(index + 1),
        comp.xYConstructionPlane,
        "({}) + (card_length - (magnet_count - 1) * magnet_center_pitch) / 2".format(x_expression),
        "({}) + card_width / 2".format(y_expression), "magnet_hole_d")
    tool = _extrude(comp, fusion, core, seed,
                    fusion.FeatureOperations.NewBodyFeatureOperation,
                    "magnet_hole_depth",
                    "Subject {:02d} native magnet seed tool".format(index + 1))
    pattern = _pattern_bodies(
        comp, fusion, core, _bodies_of(tool), comp.xConstructionAxis,
        "magnet_count", "magnet_center_pitch",
        "Subject {:02d} native magnet recesses".format(index + 1))
    result = _cut_body(comp, fusion, core, body, _bodies_of(pattern),
                       "Subject {:02d} native magnet cut".format(index + 1))
    result.name = body.name
    return result


def _build_subject_sheet_native(design, fusion, core, p, layout_result):
    sheet, bodies = subject_sheet_layout(p), []
    text_plane = _offset_plane(design.rootComponent, core, "card_height",
                               "Subject text plane")
    for card in sheet["cards"]:
        bodies.append(_build_subject_card_native(
            design, fusion, core, p, card["label"], card["index"], card["x"], card["y"],
            layout_result["card_length"], text_plane))
    return bodies


def _check_model(design, expected):
    """Raise a feature-aware error with context for Fusion timeline diagnosis."""
    import adsk.fusion as fusion
    if not design.computeAll():
        raise RuntimeError("Fusion computeAll failed; inspect the first feature in the timeline.")
    for index in range(design.timeline.count):
        entity = design.timeline.item(index).entity
        if hasattr(entity, "healthState") and entity.healthState != fusion.FeatureHealthStates.HealthyFeatureHealthState:
            message = getattr(entity, "errorOrWarningMessage", "no diagnostic text")
            raise RuntimeError("Feature {} is unhealthy: {}".format(getattr(entity, "name", index), message))
    bodies = design.rootComponent.bRepBodies
    if bodies.count != 17 or any(not body.isSolid for body in bodies):
        raise RuntimeError("Expected board, trim, plaques, and 14 subject bodies; found {} bodies.".format(bodies.count))
    board = None
    for index in range(bodies.count):
        body = bodies.item(index)
        if body.name == "Timetable board":
            board = body
            break
    if board is None or not board.isSolid:
        raise RuntimeError("Main board body is missing or not solid.")
    bounds = board.preciseBoundingBox
    actual = ((bounds.maxPoint.x - bounds.minPoint.x) * 10,
              (bounds.maxPoint.y - bounds.minPoint.y) * 10)
    if abs(actual[0] - expected["overall_width"]) > 0.5 or abs(actual[1] - expected["approx_overall_height"]) > 0.5:
        raise RuntimeError("Main board bounds {} do not follow parameters {}.".format(actual, expected))
    sketches = list(design.rootComponent.sketches)
    # Text sketches stay unlocked: either live SketchText frames, or exploded
    # glyph curves ("* glyph sketch") that are not fully constrained.
    unconstrained = []
    for sketch in sketches:
        if sketch.isFullyConstrained:
            continue
        try:
            has_text = sketch.sketchTexts.count > 0
        except Exception:
            has_text = False
        is_glyph = sketch.name.endswith(' glyph sketch')
        if not has_text and not is_glyph:
            unconstrained.append(sketch.name)
    if unconstrained:
        raise RuntimeError("Unconstrained native sketches: {}".format(", ".join(unconstrained[:8])))
    if len(sketches) < 17:
        raise RuntimeError("Expected native constrained sketches for board, plaques, and 14 cards.")
    return {"bodies": bodies.count, "expected_width": expected["overall_width"],
            "expected_height": expected["body_height"]}


def verify_variants(design, changes):
    """Recompute selected variants and restore all original expressions."""
    params = design.userParameters
    original = {name: params.itemByName(name).expression for name in DEFAULTS}
    try:
        verified = 0
        for change in changes:
            for name, expression in original.items():
                params.itemByName(name).expression = expression
            for name, value in change.items():
                units = "" if name in ("day_count", "morning_periods", "afternoon_periods",
                                       "show_morning", "show_afternoon", "show_wall_holes",
                                       "auto_card_length") else " mm"
                params.itemByName(name).expression = "{}{}".format(value, units)
            if not design.computeAll():
                raise RuntimeError("Variant compute failed: {}".format(change))
            variant = dict(DEFAULTS)
            variant.update(change)
            _check_model(design, layout(variant))
            verified += 1
    finally:
        for name, expression in original.items():
            params.itemByName(name).expression = expression
        design.computeAll()
        _check_model(design, layout(DEFAULTS))
    return verified


def run(context):
    import adsk.core as core
    import adsk.fusion as fusion
    app = core.Application.get()
    ui = app.userInterface
    progress = ui.createProgressDialog()
    progress.isCancelButtonShown = False
    progress.show("TimetableBoard", "Preparing parameters", 0, 6, 1)
    stage = "Preparing parameters"
    def update(label, value):
        nonlocal stage
        stage = label
        progress.message = label
        progress.progressValue = value
        __import__('adsk').doEvents()
    try:
        p, expected = dict(DEFAULTS), validate(DEFAULTS)
        doc = app.documents.add(core.DocumentTypes.FusionDesignDocumentType)
        doc.name = "Thời khóa biểu - native parametric"
        design = fusion.Design.cast(app.activeProduct)
        design.designType = fusion.DesignTypes.ParametricDesignType
        _add_user_parameters(design, core)
        update("Board and magnet recesses", 1)
        board = _build_board(design, fusion, core, p, expected)
        update("Board labels and wave trim", 2)
        board = _build_board_labels_native(design, fusion, core, p, expected, board)
        board = _build_trim(design, fusion, core, p, expected, board)
        update("Detached plaques", 3)
        detachable_text_plane = _offset_plane(
            design.rootComponent, core,
            "detachable_block_total_height - title_relief",
            "Detachable text plane")
        _build_plaque_native(design, fusion, core, p, "Học sinh mẫu", p["subtitle_block_length"],
                      p["subtitle_block_width"],
                      (expected["overall_width"] - p["subtitle_block_length"]) / 2,
                      expected["body_height"]+30, "Name plaque", "subtitle_block_length",
                      "body_height + 30 mm", detachable_text_plane)
        _build_plaque_native(design, fusion, core, p, "Believe in Yourself", p["slogan_block_length"],
                      p["slogan_block_width"],
                      (expected["overall_width"] - p["slogan_block_length"]) / 2,
                      expected["body_height"]+60, "Slogan plaque", "slogan_block_length",
                      "body_height + 60 mm", detachable_text_plane)
        update("Fourteen detached subject cards", 4)
        _build_subject_sheet_native(design, fusion, core, p, expected)
        update("Recompute and health checks", 5)
        checks = _check_model(design, expected)
        variants = verify_variants(design, ({"day_count": 7}, {"morning_periods": 6,
                                  "afternoon_periods": 4})) if VERIFY_VARIANTS else 0
        update("Completed", 6)
        progress.hide()
        app.activeViewport.fit()
        ui.messageBox("Đã tạo bảng native với {} body. Change Parameters đã sẵn sàng.\n"
                      "Biến thể được kiểm tra: {}.".format(checks["bodies"], variants))
    except Exception:
        ui.messageBox("Không tạo/kiểm tra được mô hình; document vẫn mở để chẩn đoán.\n\n" + stage + "\n" + traceback.format_exc())
    finally:
        progress.hide()
