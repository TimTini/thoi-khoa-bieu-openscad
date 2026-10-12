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

    def test_native_feature_contract_keeps_text_separate_from_base_profiles(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("_extrude_entity(comp, fusion, core, text", source)
        self.assertIn("_join_body(comp, fusion, core, board", source)
        self.assertIn('"effective_{}_rows".format', source)
        self.assertIn('"magnet_count", "magnet_center_pitch"', source)

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
        parent = rect.index('addTwoPointRectangle')
        fillet = rect.index('addFillet')
        self.assertLess(parent, fillet)
        self.assertIn('parent_lines', rect)
        self.assertIn('model_lines', rect)
        self.assertIn('addCollinear(model_line, parent_line)', rect)
        self.assertIn('_drive_point(sketch, core, axes, parent_lower_left', rect)
        self.assertIn('width_expression)', rect)
        self.assertIn('height_expression)', rect)
        self.assertNotIn(' - 2 * slot_corner_radius', rect)

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
        cuts, circles, rectangles = [], [], []
        def feature():
            body = NS(name='Timetable board')
            current[0] = body
            return NS(bodies=NS(item=lambda index: body))
        def extrude(comp, fusion, core, sketch, operation, distance, name, target=None):
            if operation == 'cut':
                self.assertIs(target, current[0], name)
                cuts.append((name, distance))
            return feature()
        def pattern(*args, **kwargs):
            return feature()
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
                            _pattern_feature=pattern, _anchored_circle_sketch=circle,
                            _rectangle_sketch=rectangle):
            p = dict(timetable.DEFAULTS, slot_tolerance=.6)
            result = timetable._build_board(design, fusion, NS(), p, timetable.layout(p))
        self.assertIs(result, current[0])
        self.assertEqual(len(cuts), 10)
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

if __name__ == '__main__':
    unittest.main()
