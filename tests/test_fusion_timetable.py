"""Offline contracts for the native timetable Fusion script.

These tests deliberately do not import Autodesk Fusion.  The Fusion-side
builder is exercised separately in a real Fusion installation.
"""
import importlib.util
import math
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "fusion" / "TimetableBoard" / "TimetableBoard.py"
spec = importlib.util.spec_from_file_location("timetable_fusion", SCRIPT)
timetable = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timetable)


class TimetableMathTest(unittest.TestCase):
    def test_source_defaults_and_subject_labels_are_preserved(self):
        source = (ROOT / "thoi-khoa-bieu.scad").read_text(encoding="utf-8")
        self.assertIn("base_thickness      = 5.6", source)
        self.assertAlmostEqual(timetable.DEFAULTS["base_thickness"], 5.6)
        self.assertEqual(len(timetable.SUBJECT_NAMES), 14)
        self.assertEqual(timetable.SUBJECT_NAMES[-1], "Thể dục")
        self.assertEqual(timetable.SUBJECT_LABELS[3], "HĐTN")

    def test_default_layout_matches_canonical_board(self):
        result = timetable.layout(timetable.DEFAULTS)
        self.assertEqual(result["days"], 5)
        self.assertEqual(result["morning_rows"], 5)
        self.assertEqual(result["afternoon_rows"], 5)
        self.assertAlmostEqual(result["overall_width"], 243.0)
        self.assertAlmostEqual(result["body_height"], 216.2)
        self.assertAlmostEqual(result["approx_overall_height"], 227.0)
        self.assertAlmostEqual(result["card_length"], 39.864)
        self.assertEqual(result["magnet_count"], 3)

    def test_layout_recomputes_grid_and_vertical_anchors(self):
        changed = dict(timetable.DEFAULTS, day_count=7, morning_periods=6,
                       afternoon_periods=4)
        result = timetable.layout(changed)
        self.assertEqual(result["days"], 7)
        self.assertAlmostEqual(result["card_length"], 31.0)
        self.assertGreaterEqual(result["column_gap"], 0)
        self.assertAlmostEqual(result["morning_y"],
                               timetable.DEFAULTS["morning_y_ref"] - timetable.DEFAULTS["row_pitch"])
        self.assertAlmostEqual(result["weekday_y"], timetable.DEFAULTS["weekday_y_ref"])

    def test_validate_rejects_unsafe_parameter_variants(self):
        invalid = [
            {"day_count": 0}, {"day_count": 8}, {"base_thickness": 0},
            {"magnet_hole_depth": 6}, {"magnet_hole_d": 12},
            {"fixed_card_length": 50, "auto_card_length": False},
            {"morning_periods": -1}, {"max_board_width": 200},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    timetable.validate(dict(timetable.DEFAULTS, **changes))

    def test_subject_sheet_covers_all_subjects_and_magnet_centres(self):
        result = timetable.subject_sheet_layout(timetable.DEFAULTS)
        self.assertEqual(len(result["cards"]), 14)
        self.assertEqual(result["columns"], 5)
        for card in result["cards"]:
            self.assertEqual(card["label"], timetable.SUBJECT_LABELS[card["index"]])
            self.assertEqual(len(card["magnet_x"]), 3)
            self.assertGreater(card["magnet_x"][0], 0)
            self.assertLess(card["magnet_x"][-1], timetable.layout(timetable.DEFAULTS)["card_length"])

    def test_derived_parameter_expressions_match_layout(self):
        for changes in ({}, {"day_count": 7},
                        {"morning_periods": 6, "afternoon_periods": 4},
                        {"day_count": 7, "morning_periods": 6,
                         "afternoon_periods": 4}):
            with self.subTest(changes=changes):
                values = timetable.derived_values(dict(timetable.DEFAULTS, **changes))
                result = timetable.layout(dict(timetable.DEFAULTS, **changes))
                self.assertEqual(set(timetable.DERIVED),
                                 set(values) & set(timetable.DERIVED))
                for name in timetable.DERIVED:
                    self.assertTrue(math.isfinite(float(values[name])), name)
                self.assertAlmostEqual(values["overall_width"], result["overall_width"])
                self.assertAlmostEqual(values["body_height"], result["body_height"])
                self.assertAlmostEqual(values["column_gap"], result["column_gap"])
                self.assertEqual(values["effective_morning_rows"], result["morning_rows"])
                self.assertEqual(values["effective_afternoon_rows"], result["afternoon_rows"])
                self.assertEqual(values["magnet_count"], result["magnet_count"])


class FusionScriptContractTest(unittest.TestCase):
    def test_script_uses_native_parametric_features_and_is_importable_without_adsk(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for token in ("userParameters.add", "sketches.add", "extrudeFeatures",
                      "SketchTexts", "VERIFY_VARIANTS", "computeAll",
                      "rectangularPatternFeatures", "combineFeatures",
                      "heightParameter", "isFullyConstrained",
                      "FeatureOperations.NewBodyFeatureOperation"):
            self.assertIn(token, source)
        for token in ("createOffsetInput", "addOffset2", "sketchArcs",
                      "addByCenterStartSweep", "addRadialDimension"):
            self.assertIn(token, source)
        self.assertNotIn("wave_outline_expressions", source)
        self.assertNotIn("sketchPoints.add(core.Point3D.create", source)
        self.assertNotRegex(source, r"(mesh|stl|obj|importManager|TriangleMesh)",
                            msg="native script must not import mesh geometry")

    def test_fusion_text_uses_windows_system_fonts_not_scad_oswald(self):
        """Oswald is an OpenSCAD asset font; Fusion needs a Windows family name."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(timetable.FUSION_TEXT_FONTS[0], "Arial")
        self.assertIn("Segoe UI", timetable.FUSION_TEXT_FONTS)
        self.assertIn("Times New Roman", timetable.FUSION_TEXT_FONTS)
        self.assertIn("for font_name in FUSION_TEXT_FONTS", source)
        self.assertIn("inp.fontName = font_name", source)
        self.assertNotIn('inp.fontName = "Oswald"', source)
        self.assertIn("Arial", (ROOT / "fusion" / "README.md").read_text(
            encoding="utf-8"))

    def test_native_feature_contract_keeps_text_separate_from_base_profiles(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("_extrude_text_glyphs(", source)
        self.assertIn("_join_body(comp, fusion, core, board", source)
        self.assertIn('"effective_{}_rows".format', source)
        self.assertIn('"magnet_count", "magnet_center_pitch"', source)
        # Pocket Cut patterns still use Identical. Magnet holes must NOT pattern
        # Cut features: Identical still raises PATTERN_FEATURES_NO_PASTE_INT_EDGES
        # for blind magnet tools on pocket floors. Use NewBody tools → pattern
        # bodies → combine-cut instead (body patterns skip feature paste edges).
        self.assertIn("IdenticalPatternCompute", source)
        pattern_helper = source[source.index("def _pattern_feature"):
                                source.index("def _offset_plane")]
        self.assertIn("patternComputeOption", pattern_helper)
        self.assertIn("IdenticalPatternCompute", pattern_helper)
        self.assertIn("def _pattern_bodies", source)
        self.assertIn("def _cut_body", source)
        board_build = source[source.index("def _build_board"):
                             source.index("def _build_trim")]
        plaque_magnets = board_build[board_build.index("magnet seed"):
                                     board_build.index("def magnet_pattern")]
        self.assertIn("NewBodyFeatureOperation", plaque_magnets)
        self.assertIn("_pattern_bodies", plaque_magnets)
        self.assertIn("_cut_body", plaque_magnets)
        self.assertNotIn("_pattern_feature", plaque_magnets)
        magnet = source[source.index("def magnet_pattern"):
                        source.index("if layout_result[\"afternoon_rows\"]:",
                                     source.index("def magnet_pattern"))]
        self.assertIn("_pattern_bodies", magnet)
        self.assertIn("_cut_body", magnet)
        self.assertIn('name + " days"', magnet)
        self.assertNotIn('name + " rows"', magnet)
        self.assertIn("comp.yConstructionAxis", magnet)
        self.assertNotIn("_pattern_feature", magnet)

    def test_manifest_and_documentation_are_present(self):
        manifest = ROOT / "fusion" / "TimetableBoard" / "TimetableBoard.manifest"
        docs = ROOT / "fusion" / "README.md"
        self.assertTrue(manifest.is_file())
        self.assertTrue(docs.is_file())
        self.assertIn("VERIFY_VARIANTS", docs.read_text(encoding="utf-8"))
        self.assertIn("timeline", docs.read_text(encoding="utf-8").lower())



class NativeGeometryRegressionTest(unittest.TestCase):
    def test_native_arc_parameters_reject_degenerate_geometry(self):
        self.assertNotIn('wave_softness', timetable.DEFAULTS)
        for changes in ({'wave_amplitude': 0}, {'slot_corner_radius': 6},
                        {'corner_radius': 110}, {'border_width': 0}):
            with self.assertRaises(ValueError):
                timetable.validate(dict(timetable.DEFAULTS, **changes))

    def test_analytic_outline_plan_has_native_arcs_and_safe_offset_radius(self):
        for changes in ({},{'day_count':7},{'morning_periods':6,'afternoon_periods':4}):
            p=dict(timetable.DEFAULTS,**changes)
            plan=timetable.analytic_outline_plan(p)
            self.assertEqual(plan['kind'], 'analytic-arcs')
            self.assertGreater(plan['horizontal_count'], 1)
            self.assertGreater(plan['vertical_count'], 1)
            self.assertGreater(plan['scallop_radius'],
                               p['border_edge_gap'] + p['border_width'])
            self.assertEqual(plan['bounds'], (0.0, p['core_width'] if 'core_width' in p else timetable.layout(p)['overall_width'],
                                              0.0, timetable.layout(p)['body_height']))

    def test_outline_uses_one_associative_offset_for_inner_ring(self):
        source = SCRIPT.read_text(encoding='utf-8')
        trim = source[source.index('def _build_trim'):source.index('def _build_board_labels_native')]
        self.assertIn('createOffsetInput', trim)
        self.assertIn('addOffset2', trim)
        self.assertNotIn('wave_outline_expressions', trim)

    def test_rounded_rect_anchors_and_sizes_native_parent_before_fillet(self):
        source = SCRIPT.read_text(encoding='utf-8')
        rect = source[source.index('def _anchored_rectangle_sketch'):
                     source.index('def _anchored_circle_sketch')]
        # Ignore the docstring (it may name the rejected pattern); assert on body.
        body = rect[rect.index('"""', rect.index('"""') + 3) + 3:]
        # Four-corner drive before fillet; do not rely on addTwoPointRectangle
        # H/V edges (API shear DOF) or one-anchor + diagonal width/height.
        self.assertNotIn('addTwoPointRectangle', body)
        self.assertNotIn('addDistanceDimension', body)
        self.assertLess(body.index('parent_corners'), body.index('addFillet'))
        self.assertIn('parent_lines', body)
        self.assertIn('model_lines', body)
        self.assertIn('addCollinear(model_line, parent_line)', body)
        self.assertIn('_drive_point(sketch, core, axes, corner', body)
        self.assertIn('width_expression', body)
        self.assertIn('height_expression', body)
        self.assertNotIn(' - 2 * slot_corner_radius', body)

    def test_anchored_rectangle_drives_all_four_corners(self):
        """Structural DOF contract: 4 corners away from origin → 8 offsets.

        Offline mocks that hardcode isFullyConstrained=True are false positives;
        count driven corners and connecting parent edges instead.
        """
        from types import SimpleNamespace as NS
        points, offsets, lines, collinear, fillets, radials = (
            [], [], [], [], [], [])

        def add_point(geometry):
            result = NS(geometry=geometry)
            points.append(result)
            return result

        def add_line(a, b):
            start = a if hasattr(a, 'geometry') else NS(geometry=a)
            end = b if hasattr(b, 'geometry') else NS(geometry=b)
            result = NS(startSketchPoint=start, endSketchPoint=end,
                        isConstruction=False)
            lines.append(result)
            return result

        def add_offset(axis, point, text, isDriving=True):
            self.assertTrue(isDriving)
            result = NS(parameter=NS(expression=''))
            offsets.append((axis, point, result))
            return result

        def add_fillet(line_a, point_a, line_b, point_b, radius):
            arc = NS(centerSketchPoint=NS(geometry=NS(x=0.1, y=0.1)))
            fillets.append(arc)
            return arc

        def add_radial(arc, text):
            result = NS(parameter=NS(expression=''))
            radials.append(result)
            return result

        sketch = NS(
            name='',
            isFullyConstrained=True,
            originPoint=NS(),
            sketchPoints=NS(add=add_point),
            sketchCurves=NS(
                sketchLines=NS(addByTwoPoints=add_line),
                sketchArcs=NS(addFillet=add_fillet)),
            sketchDimensions=NS(
                addOffsetDimension=add_offset,
                addRadialDimension=add_radial),
            geometricConstraints=NS(
                addCollinear=lambda a, b: collinear.append((a, b)),
                addCoincident=lambda a, b: None,
                addVerticalPoints=lambda a, b: None,
                addHorizontalPoints=lambda a, b: None))
        comp = NS(xYConstructionPlane='xy',
                  sketches=NS(add=lambda plane: sketch))
        core = NS(Point3D=NS(create=lambda *a: NS(x=a[0], y=a[1], z=a[2]
                                                  if len(a) > 2 else 0)))
        fusion = NS()

        timetable._anchored_rectangle_sketch(
            comp, core, fusion, 12.0, 24.0, 40.0, 18.0, 'Afternoon seed',
            x_expression='grid_left - slot_tolerance / 2',
            y_expression='(afternoon_y) - slot_tolerance / 2',
            width_expression='card_length + slot_tolerance',
            height_expression='card_width + slot_tolerance')

        self.assertEqual(len(points), 4)
        self.assertEqual(len(offsets), 8)
        self.assertEqual({id(point) for _, point, _ in offsets},
                         {id(point) for point in points})
        # 2 fixed construction axes + 4 parent edges + 4 model edges
        self.assertEqual(len(lines), 10)
        self.assertEqual(sum(1 for line in lines if line.isConstruction), 6)
        self.assertEqual(len(collinear), 4)
        self.assertEqual(len(fillets), 4)
        self.assertEqual(len(radials), 4)
        self.assertTrue(all(
            dim.parameter.expression == 'slot_corner_radius' for dim in radials))
        expr_pairs = [
            (offsets[i][2].parameter.expression,
             offsets[i + 1][2].parameter.expression)
            for i in range(0, 8, 2)]
        self.assertEqual(expr_pairs[0], (
            'abs(grid_left - slot_tolerance / 2)',
            'abs((afternoon_y) - slot_tolerance / 2)'))
        self.assertEqual(expr_pairs[1], (
            'abs((grid_left - slot_tolerance / 2) + (card_length + slot_tolerance))',
            'abs((afternoon_y) - slot_tolerance / 2)'))
        self.assertEqual(expr_pairs[2], (
            'abs((grid_left - slot_tolerance / 2) + (card_length + slot_tolerance))',
            'abs(((afternoon_y) - slot_tolerance / 2) + (card_width + slot_tolerance))'))
        self.assertEqual(expr_pairs[3], (
            'abs(grid_left - slot_tolerance / 2)',
            'abs(((afternoon_y) - slot_tolerance / 2) + (card_width + slot_tolerance))'))

    def test_trim_offsets_are_independent_and_allow_topology_changes(self):
        source = SCRIPT.read_text(encoding='utf-8')
        trim = source[source.index('def _build_trim'):source.index('def _build_board_labels_native')]
        self.assertGreaterEqual(trim.count('createOffsetInput(\n        parent_curves'), 2)
        self.assertGreaterEqual(trim.count('isTopologyMatched = False'), 2)
        self.assertIn('profile.areaProperties().area', trim)
        self.assertNotIn('list(outer_offset.childCurves)', trim)

class NativeBuilderRegressionTest(unittest.TestCase):
    def test_board_cuts_use_current_body_and_plaque_magnets_match(self):
        from types import SimpleNamespace as NS
        from unittest.mock import patch
        current = [None]
        cuts, new_bodies, body_patterns, combine_cuts = [], [], [], []
        circles, rectangles = [], []
        def feature(body_name='Timetable board', update_current=True):
            body = NS(name=body_name)
            if update_current:
                current[0] = body
            return NS(bodies=NS(item=lambda index: body, count=1))
        def extrude(comp, fusion, core, sketch, operation, distance, name, target=None):
            if operation == 'cut':
                self.assertIs(target, current[0], name)
                cuts.append((name, distance))
                return feature()
            if operation == 'new':
                # Magnet tools are separate solids; Main board owns current.
                if 'magnet' in name.lower():
                    new_bodies.append((name, distance))
                    return feature(body_name=name, update_current=False)
                return feature()
            return feature()
        def pattern_feature(*args, **kwargs):
            return feature()
        def pattern_bodies(comp, fusion, core, bodies, axis, quantity, distance, name,
                           second_axis=None, second_quantity=None, second_distance=None):
            body_patterns.append((name, quantity, distance, second_quantity, len(bodies)))
            return feature(body_name=name, update_current=False)
        def cut_body(comp, fusion, core, target, tools, name):
            self.assertIs(target, current[0], name)
            combine_cuts.append((name, len(tools)))
            return feature().bodies.item(0)
        def circle(*args):
            circles.append(args)
            return NS()
        def rectangle(*args, **kwargs):
            rectangles.append(kwargs)
            return NS()
        comp = NS(xYConstructionPlane='xy', xConstructionAxis='x',
                  yConstructionAxis='y', sketches=NS(add=lambda plane: NS()))
        design = NS(rootComponent=comp)
        fusion = NS(FeatureOperations=NS(NewBodyFeatureOperation='new', CutFeatureOperation='cut'))
        with patch.multiple(timetable, _add_analytic_loop=lambda *a: [],
                            _offset_plane=lambda *a: 'plane', _extrude=extrude,
                            _pattern_feature=pattern_feature, _pattern_bodies=pattern_bodies,
                            _cut_body=cut_body, _anchored_circle_sketch=circle,
                            _rectangle_sketch=rectangle):
            p = dict(timetable.DEFAULTS, slot_tolerance=.6)
            result = timetable._build_board(design, fusion, NS(), p, timetable.layout(p))
        self.assertIs(result, current[0])
        # Wall + schedule pockets + plaque pockets only; magnets are NewBody tools.
        self.assertEqual(len(cuts), 6)
        self.assertEqual(len(new_bodies), 4)  # two plaque + two schedule magnet seeds
        self.assertEqual(len(body_patterns), 6)  # plaque x2 + schedule magnets+days x2
        self.assertEqual(len(combine_cuts), 4)
        self.assertTrue(all('magnet' in name.lower() for name, _ in new_bodies))
        self.assertEqual(len(circles), 6)  # two wall, two plaque, two schedule seeds
        values = timetable.derived_values(p)
        calc = lambda expr: eval(expr.replace(' mm',''), {'__builtins__':{}, 'floor':math.floor}, values)
        for rect in rectangles[:2]:
            self.assertAlmostEqual(calc(rect['x_expression']),values['grid_left']-.3)
        for seed, width_name, height_name, anchor in (
                (circles[2], 'subtitle_block_length', 'subtitle_block_width', 'subtitle_y'),
                (circles[3], 'slogan_block_length', 'slogan_block_width', 'middle_y')):
            count = math.floor((p[width_name]-2*p['magnet_end_inset'])/p['magnet_center_pitch'])+1
            first = (values['overall_width']-p[width_name])/2+(p[width_name]-(count-1)*p['magnet_center_pitch'])/2
            self.assertAlmostEqual(calc(seed[8]),first)
            self.assertAlmostEqual(calc(seed[9]),values[anchor]+p[height_name]/2)

    def test_native_arc_radius_tracks_pitch_and_amplitude(self):
        base = timetable.analytic_outline_plan(timetable.DEFAULTS)
        changed = timetable.analytic_outline_plan(dict(timetable.DEFAULTS,
                                                       wave_pitch=12.0,
                                                       wave_amplitude=1.2))
        self.assertNotEqual(base['horizontal_radius'], changed['horizontal_radius'])
        self.assertGreater(base['scallop_radius'],
                           timetable.DEFAULTS['border_edge_gap'] + timetable.DEFAULTS['border_width'])

    def test_single_day_and_manual_card_length_derived_chain(self):
        for changes in ({'day_count':1}, {'auto_card_length':0}):
            p=dict(timetable.DEFAULTS,**changes)
            values=timetable.derived_values(p)
            expected=timetable.layout(p)
            for key in ('card_length','column_gap','overall_width','body_height'):
                self.assertAlmostEqual(values[key],expected[key])

    def test_validation_rejects_fractional_counts_and_thin_cards(self):
        for changes in ({'day_count':5.5},{'subject_block_total_height':2},
                        {'detachable_block_total_height':2}, {'slot_tolerance':-.1}):
            with self.assertRaises(ValueError):
                timetable.validate(dict(timetable.DEFAULTS,**changes))


class FusionExpressionGrammarRegressionTest(unittest.TestCase):
    def test_derived_functions_use_fusion_arity_and_logical_conditions(self):
        import ast
        for name,(expression,units) in timetable.DERIVED.items():
            tree=ast.parse(expression.replace(' mm','').replace('if(', '_if(').replace(';',','), mode='eval')
            for node in ast.walk(tree):
                if not isinstance(node,ast.Call):
                    continue
                if node.func.id in ('max','min'):
                    self.assertEqual(len(node.args),2,(name,expression))
                elif node.func.id=='_if':
                    self.assertEqual(len(node.args),3,(name,expression))
                    self.assertIsInstance(node.args[0],(ast.Compare,ast.BoolOp),(name,expression))

    def test_parameter_failure_names_the_rejected_expression(self):
        from types import SimpleNamespace as NS
        def reject(name, expression, units, comment):
            if name == 'core_width':
                raise RuntimeError('3 : Invalid expression')
        design=NS(userParameters=NS(add=reject))
        core=NS(ValueInput=NS(createByString=str))
        with self.assertRaisesRegex(RuntimeError,'core_width.*max\\('):
            timetable._add_user_parameters(design,core)


class CoordinateOffsetRegressionTest(unittest.TestCase):
    def test_driven_points_use_orthogonal_offsets_and_shared_datums(self):
        from types import SimpleNamespace as NS
        lines, offsets = [], []
        def line(a,b):
            result=NS(a=a,b=b,isConstruction=False,isFixed=False,
                      startSketchPoint=NS(isFixed=False),endSketchPoint=NS(isFixed=False))
            lines.append(result)
            return result
        def offset(axis,point,text,isDriving=True):
            self.assertTrue(axis.isConstruction and axis.isFixed and isDriving)
            self.assertTrue(axis.startSketchPoint.isFixed and axis.endSketchPoint.isFixed)
            dim=NS(parameter=NS(expression=''))
            offsets.append((axis,point,dim))
            return dim
        sketch=NS(sketchCurves=NS(sketchLines=NS(addByTwoPoints=line)),
            sketchDimensions=NS(addOffsetDimension=offset))
        core=NS(Point3D=NS(create=lambda *a:a))
        axes=timetable._coordinate_axes(sketch,core)
        point = NS(geometry=NS(x=18.0, y=16.2))
        timetable._drive_point(sketch,core,axes,point,'width_expr','height_expr')
        self.assertEqual(sum(line.isConstruction for line in lines),2)
        self.assertEqual(len(offsets),2)
        self.assertIs(offsets[0][0],axes[0])
        self.assertIs(offsets[1][0],axes[1])
        self.assertEqual(offsets[0][2].parameter.expression,'abs(width_expr)')
        self.assertEqual(offsets[1][2].parameter.expression,'abs(height_expr)')
        self.assertNotEqual(axes[0].a[1],axes[0].b[1])
        self.assertNotEqual(axes[1].a[0],axes[1].b[0])


class TextSketchConstraintRegressionTest(unittest.TestCase):
    """SketchText != free rectangle. Offline isFullyConstrained mocks lie."""

    def _run_add_text(self, *, vertical_raises=False, sketch_fully=False):
        import sys
        import types
        from types import SimpleNamespace as NS
        from unittest.mock import patch

        # cm: title box at (6.15, 19.46) size 12 x 2.1  (120x21 mm at 1.5*height)
        bl = NS(geometry=NS(x=6.15, y=19.46), geometricConstraints=[])
        br = NS(geometry=NS(x=18.15, y=19.46), geometricConstraints=[])
        tl = NS(geometry=NS(x=6.15, y=21.56), geometricConstraints=[])
        tr = NS(geometry=NS(x=18.15, y=21.56), geometricConstraints=[])

        def edge(a, b):
            return NS(startSketchPoint=a, endSketchPoint=b, geometricConstraints=[])

        bottom, right, top, left = (
            edge(bl, br), edge(br, tr), edge(tr, tl), edge(tl, bl))
        rect_lines = [bottom, right, top, left]
        offsets, horizontals, verticals, distance_dims = [], [], [], []

        def add_offset(axis, point, text, isDriving=True):
            self.assertTrue(isDriving)
            dim = NS(parameter=NS(expression=''))
            offsets.append((axis, point, dim))
            return dim

        def add_distance(a, b, orientation, text):
            dim = NS(parameter=NS(expression=''))
            distance_dims.append((a, b, orientation, dim))
            return dim

        def add_vertical(line):
            # Real Fusion: after H(bottom), V(left) raises OVER_CONSTRAINTS.
            if vertical_raises:
                raise RuntimeError('3 : VCS_SKETCH_OVER_CONSTRAINTS')
            verticals.append(line)

        def axis_line(a, b):
            return NS(a=a, b=b, isConstruction=False, isFixed=False,
                      startSketchPoint=NS(isFixed=False),
                      endSketchPoint=NS(isFixed=False))

        sketch = NS(
            name='Native title sketch',
            isFullyConstrained=sketch_fully,
            originPoint=NS(),
            sketchCurves=NS(sketchLines=NS(addByTwoPoints=axis_line)),
            sketchDimensions=NS(
                addOffsetDimension=add_offset,
                addDistanceDimension=add_distance),
            geometricConstraints=NS(
                addHorizontal=lambda line: horizontals.append(line),
                addVertical=add_vertical,
                addVerticalPoints=lambda a, b: None,
                addHorizontalPoints=lambda a, b: None),
            sketchTexts=NS(
                createInput3=lambda text, height: NS(
                    setAsMultiLine=lambda *a: None, fontName=None),
                add=lambda inp: NS(
                    heightParameter=NS(expression=''),
                    definition=NS(rectangleLines=rect_lines)),
                count=1))

        core = NS(
            Point3D=NS(create=lambda *a: NS(
                x=a[0], y=a[1], z=a[2] if len(a) > 2 else 0)),
            ValueInput=NS(createByString=lambda s: s),
            HorizontalAlignments=NS(CenterHorizontalAlignment=0),
            VerticalAlignments=NS(MiddleVerticalAlignment=0))

        fusion_mod = types.ModuleType('adsk.fusion')
        fusion_mod.HorizontalConstraint = type('HorizontalConstraint', (), {})
        fusion_mod.VerticalConstraint = type('VerticalConstraint', (), {})
        fusion_mod.DimensionOrientations = NS(
            HorizontalDimensionOrientation=0,
            VerticalDimensionOrientation=1)
        adsk_mod = types.ModuleType('adsk')

        with patch.dict(sys.modules, {'adsk': adsk_mod, 'adsk.fusion': fusion_mod}):
            with patch.object(timetable, 'FUSION_TEXT_FONTS', ('Arial',)):
                result = timetable._add_text(
                    sketch, core, 'Thời khóa biểu', 14, 61.5, 194.6, 120,
                    height_expression='title_size',
                    x_expression='(overall_width - 120 mm) / 2',
                    y_expression='title_y - 9 mm',
                    width_expression='120 mm')

        return {
            'result': result,
            'offsets': offsets,
            'horizontals': horizontals,
            'verticals': verticals,
            'distance_dims': distance_dims,
            'points': {'bl': bl, 'br': br, 'tl': tl, 'tr': tr},
            'edges': {'bottom': bottom, 'left': left},
            'sketch': sketch,
        }

    def test_add_text_uses_height_bl_and_selective_size_drives(self):
        """Fusion-safe recipe: heightParameter + BL + BR.x + TL.y.

        H/V are best-effort only. Never drive TR. Never require
        sketch.isFullyConstrained (SketchText often stays editable).
        """
        run = self._run_add_text(vertical_raises=True, sketch_fully=False)
        result = run['result']
        offsets = run['offsets']
        bl, br, tl, tr = (run['points'][k] for k in ('bl', 'br', 'tl', 'tr'))

        self.assertEqual(result.heightParameter.expression, 'title_size')
        # BL (x,y) + BR.x + TL.y = 4 offsets; TR must stay undriven.
        self.assertEqual(len(offsets), 4)
        driven = {id(point) for _, point, _ in offsets}
        self.assertEqual(driven, {id(bl), id(br), id(tl)})
        self.assertNotIn(id(tr), driven)
        by_point = {}
        for _, point, dim in offsets:
            by_point.setdefault(id(point), []).append(dim.parameter.expression)
        self.assertEqual(sorted(by_point[id(bl)]), sorted([
            'abs((overall_width - 120 mm) / 2)',
            'abs(title_y - 9 mm)',
        ]))
        self.assertEqual(by_point[id(br)], [
            'abs(((overall_width - 120 mm) / 2) + (120 mm))',
        ])
        self.assertEqual(by_point[id(tl)], [
            'abs((title_y - 9 mm) + ((title_size) * 1.5))',
        ])
        self.assertEqual(len(run['distance_dims']), 0)
        # H(bottom) succeeds; V(left) OVER is swallowed — title still returns.
        self.assertIn(run['edges']['bottom'], run['horizontals'])
        self.assertEqual(run['verticals'], [])
        self.assertFalse(run['sketch'].isFullyConstrained)

    def test_add_text_source_matches_fusion_safe_strategy(self):
        source = SCRIPT.read_text(encoding='utf-8')
        # Include helpers that own H/V try/except and frame parsing.
        helper = source[source.index('def _text_frame_corners'):
                        source.index('def _extrude')]
        self.assertIn('_drive_point', helper)
        self.assertIn('_drive_coordinate', helper)
        self.assertIn('_try_orientation', helper)
        self.assertIn('addVertical', helper)
        self.assertIn('addHorizontal', helper)
        # Do not revive failed recipes.
        self.assertNotIn('_drive_point(sketch, core, axes, tr', helper)
        self.assertNotIn('_drive_point(sketch, core, axes, br', helper)
        self.assertNotIn('_drive_point(sketch, core, axes, tl', helper)
        self.assertNotIn('addDistanceDimension', helper)
        self.assertNotIn('required=True', helper)
        add_text = source[source.index('def _add_text'):
                          source.index('def _extrude')]
        # Runtime must not gate on sketch lock (docstring wording may vary).
        body = add_text[add_text.index('"""', add_text.index('"""') + 3) + 3:]
        self.assertNotIn('isFullyConstrained', body)
        # _check_model must exempt SketchText sketches.
        check = source[source.index('def _check_model'):
                       source.index('def verify_variants')]
        self.assertIn('sketchTexts.count', check)

    def test_text_extrude_explodes_sketch_text_to_glyph_profiles(self):
        """SketchText is not a Profile; addSimple(SketchText) returns error 3.

        Working path: explode → sketch.profiles → addSimple(Profiles).
        """
        source = SCRIPT.read_text(encoding='utf-8')
        helper = source[source.index('def _extrude_text_glyphs'):
                        source.index('def _join_body')]
        self.assertIn('explode', helper)
        self.assertIn('sketch.profiles', helper)
        self.assertIn('_extrude_entity', helper)
        self.assertIn('glyph sketch', helper)
        # Do not pass SketchText to addSimple / setOneSideExtent.
        self.assertNotIn('addSimple(\n                text', helper)
        self.assertNotIn('addSimple(text', helper)
        entity = source[source.index('def _extrude_entity'):
                        source.index('def _extrude_text_glyphs')]
        self.assertIn('addSimple', entity)
        self.assertIn('not SketchText', entity)

    def test_board_label_text_new_body_then_combine_join(self):
        """Native title: explode glyphs → NewBody Profile extrude → Combine Join."""
        source = SCRIPT.read_text(encoding='utf-8')
        labels = source[source.index('def _build_board_labels_native'):
                        source.index('def _build_plaque_native')]
        self.assertIn('NewBodyFeatureOperation', labels)
        self.assertIn('_join_body', labels)
        self.assertIn('_extrude_text_glyphs', labels)
        # Title backing may still Join-extrude as a Profile; lettering must not
        # pass SketchText to _extrude_entity.
        text_join = labels[labels.index('def text_join'):
                           labels.index('text_join("Thời khóa biểu"')]
        self.assertIn('NewBodyFeatureOperation', text_join)
        self.assertNotIn('JoinFeatureOperation', text_join)
        self.assertIn('_join_body', text_join)
        self.assertIn('_extrude_text_glyphs', text_join)
        self.assertNotIn('_extrude_entity(comp, fusion, core, text', text_join)

    def test_check_model_exempts_exploded_glyph_sketches(self):
        source = SCRIPT.read_text(encoding='utf-8')
        check = source[source.index('def _check_model'):
                       source.index('def verify_variants')]
        self.assertIn("endswith(' glyph sketch')", check)
        self.assertIn('sketchTexts.count', check)


if __name__ == '__main__':
    unittest.main()
