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
    def test_wave_outline_coordinates_follow_board_parameters(self):
        for changes in ({},{'day_count':7},{'morning_periods':6,'afternoon_periods':4}):
            p=dict(timetable.DEFAULTS,**changes)
            values=timetable.derived_values(p)
            expressions=timetable.wave_outline_expressions(p,'0 mm')
            def calc(expr):
                return eval(expr.replace(' mm',''),{'__builtins__':{}},values)
            points=[(calc(x),calc(y)) for x,y in expressions]
            self.assertAlmostEqual(min(x for x,y in points),0,places=6)
            self.assertAlmostEqual(max(x for x,y in points),values['overall_width'],places=6)
            self.assertAlmostEqual(min(y for x,y in points),0,places=6)
            self.assertAlmostEqual(max(y for x,y in points),values['body_height'],places=6)
            self.assertTrue(any('core_width' in x for x,y in expressions))
            self.assertTrue(any('body_height' in y for x,y in expressions))

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
        with patch.multiple(timetable, _add_constrained_loop=lambda *a: None,
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

    def test_native_wave_softness_changes_existing_expression_coordinates(self):
        values = timetable.derived_values(timetable.DEFAULTS)
        expressions = timetable.wave_outline_expressions(timetable.DEFAULTS)
        def evaluate(softness):
            local = dict(values,wave_softness=softness)
            return [(eval(x.replace(' mm',''),{'__builtins__':{}},local),
                     eval(y.replace(' mm',''),{'__builtins__':{}},local)) for x,y in expressions]
        before, after = evaluate(0), evaluate(6)
        self.assertTrue(any(math.dist(a,b)>.1 for a,b in zip(before,after)))

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
    def test_loop_coordinates_use_orthogonal_driving_offsets_and_shared_datums(self):
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
            sketchPoints=NS(add=lambda p:NS(geometry=NS(x=p[0],y=p[1]))),
            sketchDimensions=NS(addOffsetDimension=offset))
        core=NS(Point3D=NS(create=lambda *a:a))
        design=NS(unitsManager=NS(evaluateExpression=lambda e,u:float(e.replace(' mm',''))/10))
        axes=timetable._coordinate_axes(sketch,core)
        pairs=[('0.2 mm','0.2 mm'),('180 mm','0.2 mm'),('180 mm','162 mm')]
        timetable._add_constrained_loop(sketch,core,NS(),pairs,design,axes)
        timetable._add_constrained_loop(sketch,core,NS(),pairs,design,axes)
        self.assertEqual(sum(line.isConstruction for line in lines),2)
        self.assertEqual(len(offsets),12)
        for index,(axis,point,dim) in enumerate(offsets):
            self.assertIs(axis,axes[index%2])
            self.assertEqual(dim.parameter.expression,'abs('+pairs[(index//2)%3][index%2]+')')
        self.assertNotEqual(axes[0].a[1],axes[0].b[1])
        self.assertNotEqual(axes[1].a[0],axes[1].b[0])

if __name__ == '__main__':
    unittest.main()
