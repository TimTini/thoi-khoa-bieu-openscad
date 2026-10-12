"""Create a native, editable timetable board in Autodesk Fusion.

Run from Utilities > Scripts and Add-Ins. Dimensions are millimetres in the
public parameter table; Fusion stores them internally in centimetres. The
script creates a new parametric document on every run. Board, trim, plaques,
and cards use sketches and native extrude/cut features.

The source SCAD uses text metrics to size plaques and a sinusoidal outline.
Fusion's text metrics are not consistently exposed to scripts, so plaque
widths are explicit parameters and the scalloped outline is sampled at run
time. Board dimensions, grid positions, recess sizes, and feature heights
remain linked to Change Parameters expressions. Rerun after changing wave
pitch/amplitude when a different scallop count is wanted.
"""
import math
import ast
import traceback


VERIFY_VARIANTS = False

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
    "wave_softness": 6.0, "corner_radius": 15.0,
    "wall_hole_d": 4.0, "wall_hole_margin": 12.0,
    "card_width": 11.0, "row_pitch": 15.0,
    "slot_depth": 0.01, "slot_tolerance": 0.0,
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
    "wave_pitch": "Bước sóng mép", "wave_softness": "Độ mịn mẫu sóng",
    "corner_radius": "Bán kính góc ngoài", "wall_hole_d": "Đường kính lỗ treo",
    "wall_hole_margin": "Khoảng cách tâm lỗ tới mép lõi", "card_width": "Chiều rộng thẻ",
    "row_pitch": "Bước tâm giữa các hàng",
    "slot_depth": "Độ sâu rãnh thẻ", "slot_tolerance": "Dung sai rãnh",
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
    "effective_morning_rows": ("if(show_morning; morning_periods; 0)", ""),
    "effective_afternoon_rows": ("if(show_afternoon; afternoon_periods; 0)", ""),
    "period_delta": ("(effective_morning_rows + effective_afternoon_rows) - baseline_periods", ""),
    "vertical_delta": ("period_delta * row_pitch", "mm"),
    "grid_margin": ("if(day_count >= 7; 14 mm; grid_core_margin)", "mm"),
    "min_gap": ("if(day_count >= 7; 1 mm; min_column_gap)", "mm"),
    "card_length": ("if(auto_card_length; (if(day_count >= 7; max_board_width - 2 * wave_amplitude; core_width_ref) - 2 * grid_margin - (day_count - 1) * min_gap) / day_count; fixed_card_length)", "mm"),
    "core_width": ("max(core_width_ref; 2 * grid_margin + day_count * card_length + (day_count - 1) * min_gap; max(subtitle_block_length; slogan_block_length) + 2 * (border_edge_gap + border_width + wave_amplitude + 1 mm))", "mm"),
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
                "title_size", "title_relief", "corner_radius", "slot_depth",
                "subtitle_block_width", "slogan_block_width", "subject_text_relief")
    if any(not math.isfinite(float(p[name])) or float(p[name]) <= 0 for name in positive):
        raise ValueError("Kích thước phải là số dương hữu hạn.")
    for name in ("day_count", "morning_periods", "afternoon_periods"):
        if not math.isfinite(float(p[name])) or float(p[name]) != int(p[name]):
            raise ValueError(name + " phải là số nguyên hữu hạn.")
    if p["wave_softness"] < 0 or p["slot_tolerance"] < 0:
        raise ValueError("wave_softness và slot_tolerance không được âm.")
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

def wave_outline_expressions(p, inset='0 mm'):
    """Rounded wave outline. Wave count is chosen at Run; all vertices resize.

    Each straight edge has 8 segments per wave. Corner waves use 12 segments
    per quadrant. Offsetting a parallel inner outline retains a single ring.
    """
    points=[]
    r='corner_radius'
    amp='wave_amplitude'
    left='wave_amplitude'
    right='wave_amplitude + core_width'
    bottom='wave_amplitude'
    top='body_height-wave_amplitude'
    w='core_width-2*corner_radius'
    h='body_height-2*wave_amplitude-2*corner_radius'
    layout_result=layout(p)
    lengths=[layout_result['core_width']-2*p['corner_radius'],
             layout_result['body_height']-2*p['wave_amplitude']-2*p['corner_radius']]
    counts=[max(1,round(length/p['wave_pitch'])) for length in lengths]
    def wave(t,n):
        v=math.sin(2*math.pi*n*t)
        return f'({v:.15g} + (0.5*wave_softness/(wave_softness+0.5))*{v-v*v*v:.15g})'
    for edge in range(4):
        n=counts[edge%2]
        for i in range(n*8):
            t=i/(n*8)
            q=format(t,'.15g')
            v=wave(t,n)
            if edge==0:
                x=f'{left}+{r}+({w})*{q}'
                y=f'{bottom}+({inset})-{amp}*{v}'
            elif edge==1:
                x=f'{right}-({inset})+{amp}*{v}'
                y=f'{bottom}+{r}+({h})*{q}'
            elif edge==2:
                x=f'{right}-{r}-({w})*{q}'
                y=f'{top}-({inset})+{amp}*{v}'
            else:
                x=f'{left}+({inset})-{amp}*{v}'
                y=f'{top}-{r}-({h})*{q}'
            points.append((x,y))
        centers=[(f'{right}-{r}',f'{bottom}+{r}'),(f'{right}-{r}',f'{top}-{r}'),
                 (f'{left}+{r}',f'{top}-{r}'),(f'{left}+{r}',f'{bottom}+{r}')]
        cx,cy=centers[edge]
        for i in range(12):
            angle=math.radians(-90+90*edge+90*i/12)
            radius=f'({r}-({inset})+{amp}*{wave(i/12,1)})'
            points.append((f'{cx}+{radius}*{math.cos(angle):.15g}',
                           f'{cy}+{radius}*{math.sin(angle):.15g}'))
    return points

def _value(core, expression):
    return core.ValueInput.createByString(expression)


def _collection(core, items):
    result = core.ObjectCollection.create()
    for item in items:
        result.add(item)
    return result


def _anchored_rectangle_sketch(comp, core, fusion, x, y, width, height, name,
                               plane=None, x_expression=None, y_expression=None,
                               width_expression=None, height_expression=None):
    """Create a rectangle whose four corner coordinates are driving dimensions."""
    sketch = comp.sketches.add(plane or comp.xYConstructionPlane)
    sketch.name = name
    point = core.Point3D.create
    x_expression = x_expression or "{} mm".format(x)
    y_expression = y_expression or "{} mm".format(y)
    width_expression = width_expression or "{} mm".format(width)
    height_expression = height_expression or "{} mm".format(height)
    points = [
        sketch.sketchPoints.add(point(x / 10, y / 10, 0)),
        sketch.sketchPoints.add(point((x + width) / 10, y / 10, 0)),
        sketch.sketchPoints.add(point((x + width) / 10, (y + height) / 10, 0)),
        sketch.sketchPoints.add(point(x / 10, (y + height) / 10, 0)),
    ]
    lines = sketch.sketchCurves.sketchLines
    for index in range(4):
        lines.addByTwoPoints(points[index], points[(index + 1) % 4])
    x_values = (x_expression, "({}) + ({})".format(x_expression, width_expression),
                "({}) + ({})".format(x_expression, width_expression), x_expression)
    y_values = (y_expression, y_expression,
                "({}) + ({})".format(y_expression, height_expression),
                "({}) + ({})".format(y_expression, height_expression))
    orientations = (fusion.DimensionOrientations.HorizontalDimensionOrientation,
                    fusion.DimensionOrientations.VerticalDimensionOrientation)
    for item, x_value, y_value in zip(points, x_values, y_values):
        for axis, expression in enumerate((x_value, y_value)):
            coordinate=item.geometry.x if axis==0 else item.geometry.y
            if abs(coordinate)<1e-8:
                if axis==0:
                    sketch.geometricConstraints.addVerticalPoints(sketch.originPoint,item)
                else:
                    sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint,item)
            else:
                dim=sketch.sketchDimensions.addDistanceDimension(sketch.originPoint,item,orientations[axis],
                    point(item.geometry.x+.3,item.geometry.y+.3,0))
                dim.parameter.expression='abs('+expression+')'
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
    orientations = (fusion.DimensionOrientations.HorizontalDimensionOrientation,
                    fusion.DimensionOrientations.VerticalDimensionOrientation)
    for axis, expression in enumerate((x_expression, y_expression)):
        dim = sketch.sketchDimensions.addDistanceDimension(
            sketch.originPoint, circle.centerSketchPoint, orientations[axis],
            point(x / 10 + 0.3, y / 10 + 0.3, 0))
        dim.parameter.expression = expression
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
                                "auto_card_length", "baseline_periods", "wave_softness") else "mm"
        design.userParameters.add(name, value(str(number) + (" mm" if units else "")), units,
                                  COMMENTS.get(name, "Tham số nguồn SCAD."))
    for name, (expression, units) in DERIVED.items():
        design.userParameters.add(name, value(expression), units, "Giá trị tự tính theo tham số nguồn.")


def _rectangle_sketch(comp, core, x, y, width, height, name, plane=None,
                      fusion=None, width_expression=None, height_expression=None,
                      x_expression=None, y_expression=None):
    if fusion is None:
        raise RuntimeError("Rectangle sketches require Fusion dimension orientations.")
    return _anchored_rectangle_sketch(
        comp, core, fusion, x, y, width, height, name, plane,
        x_expression, y_expression, width_expression, height_expression)


def _add_constrained_loop(sketch, core, fusion, expressions, design):
    points=[]
    orientations=(fusion.DimensionOrientations.HorizontalDimensionOrientation,
                  fusion.DimensionOrientations.VerticalDimensionOrientation)
    for pair in expressions:
        coords=[design.unitsManager.evaluateExpression(expr,'mm') for expr in pair]
        point=sketch.sketchPoints.add(core.Point3D.create(*coords,0))
        for axis,expr in enumerate(pair):
            if abs(coords[axis])<1e-8:
                if axis==0:
                    sketch.geometricConstraints.addVerticalPoints(sketch.originPoint,point)
                else:
                    sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint,point)
            else:
                dim=sketch.sketchDimensions.addDistanceDimension(sketch.originPoint,point,
                    orientations[axis],core.Point3D.create(coords[0]+.05,coords[1]+.05,0))
                dim.parameter.expression='abs('+expr+')'
        points.append(point)
    for i,point in enumerate(points):
        sketch.sketchCurves.sketchLines.addByTwoPoints(point,points[(i+1)%len(points)])
    return points

def _add_text(sketch, core, text, height_mm, x_mm, y_mm, width_mm,
              height_expression=None, x_expression=None, y_expression=None,
              width_expression=None):
    """Add a native SketchTexts text block (Fusion 2026 createInput3 API)."""
    import adsk.fusion as fusion
    texts = sketch.sketchTexts  # SketchTexts API collection
    inp = texts.createInput3("'{}'".format(text.replace("'", "''")),
                             _value(core, "{} mm".format(height_mm)))
    inp.setAsMultiLine(core.Point3D.create(x_mm / 10, y_mm / 10, 0),
                       core.Point3D.create((x_mm + width_mm) / 10,
                                           (y_mm + height_mm * 1.5) / 10, 0),
                       core.HorizontalAlignments.CenterHorizontalAlignment,
                       core.VerticalAlignments.MiddleVerticalAlignment, 0)
    inp.fontName = "Oswald"
    result = texts.add(inp)
    result.heightParameter.expression = height_expression or "{} mm".format(height_mm)
    lines=result.definition.rectangleLines
    if not lines or len(lines)!=4:
        raise RuntimeError('Text has no native rectangular boundary: '+text)
    unique={}
    for line in lines:
        for pt in (line.startSketchPoint,line.endSketchPoint):
            unique[(round(pt.geometry.x,8),round(pt.geometry.y,8))]=pt
    if len(unique)!=4:
        raise RuntimeError('Text boundary is not a four-corner rectangle: '+text)
    xmin=min(x for x,y in unique); xmax=max(x for x,y in unique)
    ymin=min(y for x,y in unique); ymax=max(y for x,y in unique)
    bl,br,tl=(unique[(xmin,ymin)],unique[(xmax,ymin)],unique[(xmin,ymax)])
    bottom=next(line for line in lines if abs(line.startSketchPoint.geometry.y-ymin)<1e-6
                and abs(line.endSketchPoint.geometry.y-ymin)<1e-6)
    if not any(isinstance(c,fusion.HorizontalConstraint) for c in bottom.geometricConstraints):
        sketch.geometricConstraints.addHorizontal(bottom)
    orientations=(fusion.DimensionOrientations.HorizontalDimensionOrientation,
                  fusion.DimensionOrientations.VerticalDimensionOrientation)
    def drive(a,b,axis,expr):
        dim=sketch.sketchDimensions.addDistanceDimension(a,b,orientations[axis],
            core.Point3D.create(b.geometry.x+.03,b.geometry.y+.03,0))
        dim.parameter.expression='abs('+expr+')'
    drive(bl,br,0,width_expression or str(width_mm)+' mm')
    drive(bl,tl,1,'('+ (height_expression or str(height_mm)+' mm') +') * 1.5')
    for axis,expr in enumerate((x_expression or str(x_mm)+' mm',y_expression or str(y_mm)+' mm')):
        coord=bl.geometry.x if axis==0 else bl.geometry.y
        if abs(coord)<1e-8:
            if axis==0: sketch.geometricConstraints.addVerticalPoints(sketch.originPoint,bl)
            else: sketch.geometricConstraints.addHorizontalPoints(sketch.originPoint,bl)
        else:
            drive(sketch.originPoint,bl,axis,expr)
    if not sketch.isFullyConstrained:
        raise RuntimeError('Text sketch chưa đủ ràng buộc: '+text)
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
    """Extrude one profile or SketchText without flattening text into a base profile."""
    inp = comp.features.extrudeFeatures.createInput(entity, operation)
    inp.setOneSideExtent(fusion.DistanceExtentDefinition.create(_value(core, distance)),
                         fusion.ExtentDirections.PositiveExtentDirection)
    if target is not None:
        inp.participantBodies = [target]
    try:
        feature = comp.features.extrudeFeatures.add(inp)
    except Exception as error:
        raise RuntimeError('Extrude failed: '+name) from error
    feature.name = name
    return feature


def _join_body(comp, fusion, core, target, tools, name):
    inp = comp.features.combineFeatures.createInput(target, _collection(core, tools))
    inp.operation = fusion.FeatureOperations.JoinFeatureOperation
    inp.isKeepToolBodies = False
    result = comp.features.combineFeatures.add(inp)
    result.name = name
    return result.bodies.item(0)


def _pattern_feature(comp, fusion, core, feature, axis, quantity, distance, name,
                     second_axis=None, second_quantity=None, second_distance=None):
    patterns = comp.features.rectangularPatternFeatures
    inp = patterns.createInput(_collection(core, [feature]), axis,
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
    outline.name='Rounded wave board outline'
    _add_constrained_loop(outline,core,fusion,wave_outline_expressions(p),design)
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
        plane = _offset_plane(comp, core, "base_thickness - slot_depth - magnet_hole_depth", name + " magnet plane")
        seed = _anchored_circle_sketch(comp, core, fusion, x+w/2, y+h/2,
            p["magnet_hole_d"], name+" magnet seed", plane, first,
            "({}) + ({}) / 2".format(y_expression,h_expression), "magnet_hole_d")
        cut = _extrude(comp, fusion, core, seed, fusion.FeatureOperations.CutFeatureOperation,
            "magnet_hole_depth", name+" magnet seed cut", board)
        board = cut.bodies.item(0)
        pattern = _pattern_feature(comp, fusion, core, cut, comp.xConstructionAxis,
            "floor(({} - 2 * magnet_end_inset) / magnet_center_pitch) + 1".format(w_expression),
            "magnet_center_pitch", name+" magnet recesses")
        board = pattern.bodies.item(0)
        board.name = "Timetable board"

    def magnet_pattern(y, rows, y_expression, name):
        nonlocal board
        count = layout_result["magnet_count"]
        first = (layout_result["card_length"] - (count - 1) * p["magnet_center_pitch"]) / 2
        x = grid_left + first
        x_expression = "grid_left + (card_length - (magnet_count - 1) * magnet_center_pitch) / 2"
        plane = _offset_plane(comp, core, "base_thickness - slot_depth - magnet_hole_depth", name + " plane")
        seed = _anchored_circle_sketch(comp, core, fusion, x, y + p["card_width"] / 2,
                                       p["magnet_hole_d"], name + " seed", plane,
                                       x_expression, "{} + card_width / 2".format(y_expression),
                                       "magnet_hole_d")
        cut = _extrude(comp, fusion, core, seed, fusion.FeatureOperations.CutFeatureOperation,
                       "magnet_hole_depth + slot_depth", name + " seed cut", board)
        board = cut.bodies.item(0)
        magnet = _pattern_feature(comp, fusion, core, cut, comp.xConstructionAxis,
                                  "magnet_count", "magnet_center_pitch", name + " magnets")
        rows_feature = _pattern_feature(comp, fusion, core, magnet, comp.yConstructionAxis,
                                        "effective_{}_rows".format("afternoon" if y_expression == "afternoon_y" else "morning"),
                                        "row_pitch", name + " rows")
        pattern = _pattern_feature(comp, fusion, core, rows_feature, comp.xConstructionAxis,
                                "day_count", "card_length + column_gap", name + " days")
        board = pattern.bodies.item(0)
        board.name = "Timetable board"
        return pattern

    if layout_result["afternoon_rows"]:
        magnet_pattern(layout_result["afternoon_y"], layout_result["afternoon_rows"],
                       "afternoon_y", "Afternoon magnet recesses")
    if layout_result["morning_rows"]:
        magnet_pattern(layout_result["morning_y"], layout_result["morning_rows"],
                       "morning_y", "Morning magnet recesses")
    return board


def _build_trim(design, fusion, core, p, layout_result, board):
    comp=design.rootComponent
    plane=_offset_plane(comp,core,'base_thickness','Raised trim plane')
    sketch=comp.sketches.add(plane)
    sketch.name='Wave ring profile'
    _add_constrained_loop(sketch,core,fusion,wave_outline_expressions(p,'border_edge_gap'),design)
    _add_constrained_loop(sketch,core,fusion,wave_outline_expressions(p,'border_edge_gap+border_width'),design)
    if not sketch.isFullyConstrained:
        raise RuntimeError('Wave ring sketch is not fully constrained.')
    rings=[profile for profile in sketch.profiles if profile.profileLoops.count==2]
    if len(rings)!=1:
        raise RuntimeError('Expected one ring profile with a single inner hole.')
    feature=_extrude_entity(comp,fusion,core,rings[0],fusion.FeatureOperations.NewBodyFeatureOperation,
                            'border_relief','Raised wave ring')
    return _join_body(comp,fusion,core,board,list(feature.bodies),'Join raised wave ring')

def _build_board_labels_native(design, fusion, core, p, layout_result, board):
    """Join each native SketchText extrusion into the board body."""
    comp = design.rootComponent
    width = layout_result["overall_width"]
    support = _rectangle_sketch(
        comp, core, width / 2 - 60, layout_result["body_height"] - 12.6, 120, 23.4,
        "Title backing native", fusion=fusion,
        x_expression="(overall_width - 120 mm) / 2",
        y_expression="body_height - 12.6 mm", width_expression="120 mm",
        height_expression="23.4 mm")
    support_feature = _extrude(comp, fusion, core, support,
                               fusion.FeatureOperations.NewBodyFeatureOperation,
                               "base_thickness", "Title backing native")
    board = _join_body(comp, fusion, core, board, list(support_feature.bodies),
               "Join title backing native")

    def text_join(label, height, x, y, text_width, name, x_expr, y_expr,
                  width_expr):
        nonlocal board
        plane = _offset_plane(comp, core, "base_thickness - 0.01 mm", name + " plane")
        sketch = comp.sketches.add(plane)
        sketch.name = name + " sketch"
        text = _add_text(sketch, core, label, height, x, y, text_width,
                         x_expression=x_expr, y_expression=y_expr,
                         width_expression=width_expr, height_expression="title_size" if name=="Native title" else "6 mm")
        feature = _extrude_entity(comp, fusion, core, text,
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
                         name, width_expression, y_expression):
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
    text_plane = _offset_plane(comp, core,
                               "detachable_block_total_height - title_relief",
                               name + " native text plane")
    text_sketch = comp.sketches.add(text_plane)
    text = _add_text(text_sketch, core, label, min(height * 0.55, 8), x + 1,
                     y + height * 0.2, width - 2,
                     x_expression="(overall_width - {}) / 2 + 1 mm".format(width_expression),
                     y_expression="{} + ({} - {} mm * 1.5) / 2".format(y_expression,height_expression,min(height*.55,8)),
                     width_expression="{} - 2 mm".format(width_expression))
    raised = _extrude_entity(comp, fusion, core, text,
                             fusion.FeatureOperations.NewBodyFeatureOperation,
                             "title_relief", name + " native raised text")
    body = _join_body(comp, fusion, core, body, list(raised.bodies), name + " native text join")
    first = "(overall_width - {}) / 2 + ({} - (floor(({} - 2 * magnet_end_inset) / magnet_center_pitch)) * magnet_center_pitch) / 2".format(
        width_expression, width_expression, width_expression)
    seed = _anchored_circle_sketch(
        comp, core, fusion, x + width / 2, y + height / 2,
        p["magnet_hole_d"], name + " native magnet seed", comp.xYConstructionPlane,
        first, "{} + {} / 2".format(y_expression, height_expression), "magnet_hole_d")
    cut = _extrude(comp, fusion, core, seed, fusion.FeatureOperations.CutFeatureOperation,
                   "magnet_hole_depth", name + " native magnet seed cut", body)
    pattern = _pattern_feature(comp, fusion, core, cut, comp.xConstructionAxis,
                     "floor(({} - 2 * magnet_end_inset) / magnet_center_pitch) + 1".format(width_expression),
                     "magnet_center_pitch", name + " native magnet recesses")
    result = pattern.bodies.item(0)
    result.name = body.name
    return result


def _build_subject_card_native(design, fusion, core, p, label, index, x, y, length):
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
    text_plane = _offset_plane(comp, core, "card_height",
                               "Subject {:02d} native text plane".format(index + 1))
    text_sketch = comp.sketches.add(text_plane)
    text = _add_text(text_sketch, core, label, min(p["card_width"] * 0.48, 6),
                     x + 1, y + 2, length - 2,
                     x_expression="({}) + 1 mm".format(x_expression),
                     y_expression="({}) + 2 mm".format(y_expression),
                     width_expression="card_length - 2 mm")
    raised = _extrude_entity(comp, fusion, core, text,
                             fusion.FeatureOperations.NewBodyFeatureOperation,
                             "subject_text_relief", "Subject {:02d} native raised text".format(index + 1))
    body = _join_body(comp, fusion, core, body, list(raised.bodies),
               "Join subject {:02d} native text".format(index + 1))
    seed = _anchored_circle_sketch(
        comp, core, fusion, x + length / 2, y + p["card_width"] / 2,
        p["magnet_hole_d"], "Subject {:02d} native magnet seed".format(index + 1),
        comp.xYConstructionPlane,
        "({}) + (card_length - (magnet_count - 1) * magnet_center_pitch) / 2".format(x_expression),
        "({}) + card_width / 2".format(y_expression), "magnet_hole_d")
    cut = _extrude(comp, fusion, core, seed, fusion.FeatureOperations.CutFeatureOperation,
                   "magnet_hole_depth", "Subject {:02d} native magnet seed cut".format(index + 1), body)
    pattern = _pattern_feature(comp, fusion, core, cut, comp.xConstructionAxis,
                     "magnet_count", "magnet_center_pitch",
                     "Subject {:02d} native magnet recesses".format(index + 1))
    result = pattern.bodies.item(0)
    result.name = body.name
    return result


def _build_subject_sheet_native(design, fusion, core, p, layout_result):
    sheet, bodies = subject_sheet_layout(p), []
    for card in sheet["cards"]:
        bodies.append(_build_subject_card_native(
            design, fusion, core, p, card["label"], card["index"], card["x"], card["y"],
            layout_result["card_length"]))
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
    unconstrained = [sketch.name for sketch in sketches if not sketch.isFullyConstrained]
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
        _build_plaque_native(design, fusion, core, p, "Học sinh mẫu", p["subtitle_block_length"],
                      p["subtitle_block_width"],
                      (expected["overall_width"] - p["subtitle_block_length"]) / 2,
                      expected["body_height"]+30, "Name plaque", "subtitle_block_length",
                      "body_height + 30 mm")
        _build_plaque_native(design, fusion, core, p, "Believe in Yourself", p["slogan_block_length"],
                      p["slogan_block_width"],
                      (expected["overall_width"] - p["slogan_block_length"]) / 2,
                      expected["body_height"]+60, "Slogan plaque", "slogan_block_length",
                      "body_height + 60 mm")
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
