// =============================================================
// THOI KHOA BIEU - PARAMETRIC SCHEDULE BOARD
// Parametric layout with removable labels and subject cards
// Units: millimeters | OpenSCAD snapshot with textmetrics enabled
// =============================================================
// Baseline (6 days, 5 morning + 5 afternoon): approx. 243 x 227 mm.
// The layout is parametric: change days / periods only; rows/columns relocate automatically.
// =============================================================

// Load fonts bundled with this project.
use <assets/fonts/Praise/Praise-Regular.ttf>;
use <assets/fonts/Protest-Riot/ProtestRiot-Regular.ttf>;
use <assets/fonts/Oswald/Oswald[wght].ttf>;
use <assets/fonts/Noto-Emoji/NotoEmoji-Bold.ttf>;

$fn = 48;

// -------------------------------------------------------------
// 1) USER SETTINGS - normally edit only this section
// -------------------------------------------------------------

morning_periods   = 5;
afternoon_periods = 5;

day_count = 5; // [1:7]
show_morning   = true;
show_afternoon = true;
show_wall_holes = true;
output_part = "assembled"; // [assembled, board, name_slogan, subtitle, slogan, subject, subjects]
board_color = "#FFFFFF";
board_accent_color = "#C98AFF";
block_color = "#FFFFFF";
block_text_color = "#FFFFFF";
block_outline_color = "#FF6FAE";
subject_color = "#5AA9FF";
subject_text_color = "#FFFFFF";
auto_card_length = true;
fixed_card_length = 31.0; // original card length; used when auto_card_length is false
subject_index = 0; // [0:13] choose one subject when output_part is "subject"

// Full subject names; edit subject_labels below to change the printed text.
subject_names = [
    "Tiếng Việt", "Toán", "Tiếng Anh", "Hoạt động trải nghiệm",
    "Tiếng Anh bổ trợ", "Tiếng Anh Giao tiếp", "Tự nhiên xã hội",
    "Giáo dục thể chất", "Âm nhạc", "Kỹ năng sống", "STEM",
    "Đạo đức", "Mỹ thuật", "Thể dục"
];
// Printed labels stay at subject_size; long names use short labels instead of smaller text.
subject_labels = [
    "Tiếng Việt", "Toán", "Tiếng Anh", "HĐTN", "TA BT", "TA GT",
    "TN&XH", "GDTC", "Âm nhạc", "KNS", "STEM", "Đạo đức", "Mỹ thuật", "Thể dục"
];

day_names = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
days = [for (i = [0:day_count-1]) day_names[i]];

// Enlarge the board when more columns or a longer name/slogan need room.
// The width limit below prevents exceeding the printer bed.
auto_expand_width = true;
max_board_width = 254.0; // printer limit, including the outer waves

// Main visible texts. These are kept separate so they are easy to customize.
title_text     = "Thời khóa biểu";
morning_text   = "Sáng";
afternoon_text = "Chiều";

// Removable name and slogan blocks are exported separately from the main board.
subtitle_text  = "Học sinh mẫu";            // optional separate block, not rendered by default
slogan_text    = "Believe in Yourself";   // optional separate block, not rendered by default

// -------------------------------------------------------------
// 2) SOURCE-REFERENCED PARAMETERS
// -------------------------------------------------------------

// Frame / body
core_width_ref      = 240;   // source: "max dim"; wavy edge adds 2*wave_amplitude
target_overall_z    = 7.6;   // user-supplied target envelope
base_thickness      = 5.6;   // source: "de day"
corner_radius       = 15.0;  // source: "bo goc bang"

border_width        = 1.6;   // source: "do rong vien"
border_edge_gap     = 2.0;   // source: "vien cach mep"
border_relief       = 1.2;   // source: "do noi vien"

wave_amplitude      = 1.5;   // source: "bien do song"
wave_pitch          = 9.8;   // source: "buoc song"
wave_softness       = 6;     // source: "do mem goc"; rounds crests/troughs and increases curve resolution

// Mounting holes
wall_hole_d         = 4.0;   // source: "d lo treo"
wall_hole_margin    = 12.0;  // source: "le lo treo", measured from nominal/core edge

// Schedule cards / pockets
card_width          = 11.0;  // source: "chieu rong the"
row_pitch           = 15.0;  // source: "khoang cach dong" (centre-to-centre)
slot_corner_radius  = 3.4;   // corner radius for each schedule pocket
slot_depth          = 0.01;  // shallow front recess
slot_tolerance      = 0.00;  // source: "dung sai lo"
magnet_hole_d        = 6.1;   // diameter of the magnet holes in each recess
magnet_hole_depth    = 2.2;   // measured down from the recess floor
magnet_center_pitch  = 12.0;   // centre-to-centre distance along each recess
magnet_end_inset     = 6.5;   // minimum distance from an end to the first hole centre

// Source has a snap groove of 16 mm; retained as a parameter for future true snap-fit cards.
snap_groove_length  = 16.0;  // source: "dai ranh snap"
snap_grip_adjust    = 0.000; // source: "do bam snap"
snap_edge           = "bottom"; // source selection: "Cạnh dưới"

// Typography / relief
font_title          = "Praise";          // source font
font_subtitle       = "Protest Riot";    // source font
font_labels         = "Protest Riot";    // weekday, shift, and slogan text
font_subject        = "Oswald:style=Bold"; // thicker subject labels for printing
font_emoji          = "Noto Emoji:style=Bold"; // source font for emoji

title_size          = 18.0;   // source: "size tieu de"
title_stroke        = 2.0;    // source: "stroke size"
title_relief        = 1.2;    // title stroke height above the base
title_face_above_stroke = 1.2; // title lettering height above its stroke

subtitle_size       = 8.0;    // larger name text; source baseline was 8.0
subtitle_stroke     = 1.2;    // source: "stroke size phu"
slogan_size         = 7.0;    // size of the detachable slogan lettering
slogan_stroke       = 1.2;    // 2D outline width around the slogan lettering
slogan_icon         = "🍀";
slogan_icon_size    = 8.0;
subject_size        = 6.0;    // fixed text size for subject cards; abbreviate long labels
subject_block_total_height = 5.2; // underside to top of the subject lettering
subject_text_relief = 0.8;         // subject lettering above the card body
subject_text_growth = 0.00;        // expand each letter edge for easier printing; 0 disables
subject_sheet_gap   = 4.0;    // space between separate cards for printing
weekday_size        = 6.0;    // source: "size thu"
side_label_size     = 6.0;    // source: "size nhan"
label_relief        = 1.2;    // source: do noi thu / nhan buoi

// Detachable block geometry; textmetrics needs Preferences > Experimental in the GUI
// or --enable=textmetrics at the command line.
subtitle_end_padding     = 13.5; // space beyond the measured text at each end
subtitle_block_width     = 17.0; // room for Vietnamese accents and the raised outline
subtitle_snap_length     = 60.0;

slogan_block_width       = 14.0;
slogan_end_padding       = 32.5; // room for a clover at each end
slogan_snap_length       = 90.0;

block_lug_length         = 5.0;
block_wall               = 1.2;
detachable_block_total_height = 6.5; // underside to top of the raised text
// Body visible above the shallow pocket, derived so the complete block stays 6.5 mm high.
subtitle_block_protrude = detachable_block_total_height - slot_depth
                           - title_relief - title_face_above_stroke;
slogan_block_protrude = detachable_block_total_height - slot_depth
                         - title_relief - title_face_above_stroke;

// Source fine-adjustment values kept as parameters.
title_angle              = 0.0;
title_y_adjust           = 0.0;
title_x_adjust           = 0.0;
side_label_x_adjust      = 2.0;
title_safe_gap           = 5.0; // spacing between title and the top wave/border
other_text_safe_gap      = 2.0;

// -------------------------------------------------------------
// 3) BASELINE LAYOUT CALIBRATION
// -------------------------------------------------------------
// These values define the baseline 6-day / 5+5-period layout.
// They are not individual cell coordinates; all repeated geometry is generated.

baseline_days       = 6;
baseline_periods    = 10;
baseline_total_h    = 227.0;
baseline_body_h     = 216.2;   // visible wavy body, excluding title protrusion
baseline_core_h     = baseline_body_h - 2*wave_amplitude; // 213.2

// Symmetric grid margin inside the nominal 240 mm core while preserving 31 mm cards.
grid_core_margin    = 16.34;
min_column_gap      = 2.0;

// Bottom-origin positions for the baseline layout.
afternoon_grid_y0_ref = 12.50;
middle_block_y0_ref   = 84.64;
morning_grid_y0_ref   = 101.00;
weekday_y_ref          = 179.20;
subtitle_slot_y0_ref   = 185.80;
title_center_y_ref     = 214.60;

// X of the side labels in the 243 mm baseline board.
side_label_x_ref       = 9.5;  // + side_label_x_adjust (2.0) = 11.5 mm

// -------------------------------------------------------------
// 4) DERIVED GEOMETRY - DO NOT EDIT FOR NORMAL CUSTOMIZATION
// -------------------------------------------------------------

subtitle_text_metrics = textmetrics(subtitle_text, size=subtitle_size,
                                    font=font_subtitle, halign="center", valign="center");
subtitle_block_length = assert(!is_undef(subtitle_text_metrics),
                               "Enable textmetrics in Preferences > Experimental or use --enable=textmetrics")
                        ceil(subtitle_text_metrics.size[0] + 2*subtitle_end_padding);
slogan_text_metrics = textmetrics(slogan_text, size=slogan_size,
                                  font=font_labels, halign="center", valign="center");
slogan_block_length = assert(!is_undef(slogan_text_metrics),
                             "Enable textmetrics in Preferences > Experimental or use --enable=textmetrics")
                      ceil(slogan_text_metrics.size[0] + 2*slogan_end_padding);

function n_days() = len(days);
function total_periods() = (show_morning ? morning_periods : 0) + (show_afternoon ? afternoon_periods : 0);
function period_delta() = total_periods() - baseline_periods;
function vertical_delta() = period_delta() * row_pitch;

function grid_margin_for_cols(cols) = cols >= 7 ? 14.0 : grid_core_margin;
function min_gap_for_cols(cols) = cols >= 7 ? 1.0 : min_column_gap;
function auto_card_length_for_cols(cols) =
    ((cols >= 7 && auto_expand_width ? max_board_width - 2*wave_amplitude : core_width_ref)
     - 2*grid_margin_for_cols(cols) - max(cols-1, 0)*min_gap_for_cols(cols)) / cols;
card_length = auto_card_length ? auto_card_length_for_cols(n_days()) : fixed_card_length;

// The same card length drives the grid recesses and all removable subject cards.
function required_core_width(cols) =
    2*grid_margin_for_cols(cols) + cols*card_length + max(cols-1,0)*min_gap_for_cols(cols);

detachable_block_side_margin = border_edge_gap + border_width + wave_amplitude + 1;
required_block_core_width = max(subtitle_block_length, slogan_block_length)
                            + 2*detachable_block_side_margin;
core_width = auto_expand_width
    ? max(core_width_ref, required_core_width(n_days()), required_block_core_width)
    : core_width_ref;
overall_width = core_width + 2*wave_amplitude;

body_core_height = baseline_core_h + vertical_delta();
body_height = body_core_height + 2*wave_amplitude;
approx_overall_height = baseline_total_h + vertical_delta();

core_left   = wave_amplitude;
core_right  = wave_amplitude + core_width;
core_bottom = wave_amplitude;
core_top    = wave_amplitude + body_core_height;

// Grid X extent.
grid_margin = grid_margin_for_cols(n_days());
grid_left  = core_left + grid_margin;
grid_right = core_right - grid_margin;

function column_gap(cols) =
    cols <= 1 ? 0 : (grid_right-grid_left-cols*card_length)/(cols-1);

// Dynamic Y positions. Additional afternoon rows push everything above them up;
// additional morning rows push only elements above the morning grid up.
afternoon_delta = (show_afternoon ? afternoon_periods : 0) - 5;
morning_delta   = (show_morning ? morning_periods : 0) - 5;

afternoon_grid_y0 = afternoon_grid_y0_ref;
middle_block_y0 = middle_block_y0_ref + afternoon_delta*row_pitch;
morning_grid_y0 = morning_grid_y0_ref + afternoon_delta*row_pitch;
weekday_y = weekday_y_ref + (afternoon_delta + morning_delta)*row_pitch;
subtitle_slot_y0 = subtitle_slot_y0_ref + (afternoon_delta + morning_delta)*row_pitch;
title_center_y = title_center_y_ref + (afternoon_delta + morning_delta)*row_pitch + title_y_adjust;

// Block X positions always stay centered on the current board.
subtitle_slot_x0 = overall_width/2 - subtitle_block_length/2;
middle_block_x0  = overall_width/2 - slogan_block_length/2;

// Hole positions are measured from nominal/core edges, reproducing ~13.5 mm
// from the final wavy edge in the baseline configuration.
wall_hole_x_l = core_left  + wall_hole_margin;
wall_hole_x_r = core_right - wall_hole_margin;
wall_hole_y   = core_top   - wall_hole_margin;

// -------------------------------------------------------------
// 5) 2D HELPERS
// -------------------------------------------------------------

module rounded_rect_2d(w, h, r) {
    rr = min(r, min(w,h)/2 - 0.01);
    offset(r=rr)
        offset(delta=-rr)
            square([w,h]);
}

// Smooth sinusoidal wavy outline around a rounded nominal core.
// Both straight sections and rounded corners carry the wave.
function _edge_waves(length, pitch) = max(1, round(length/pitch));
function _edge_steps(length, pitch) = _edge_waves(length,pitch) * max(8, wave_softness*2);

// Higher softness rounds both crests and troughs without changing the +/-1
// extrema or the zero crossings, so amplitude and pitch retain their meaning.
function _wave_profile(v) =
    let(s=max(0,wave_softness), k=0.5*s/(s+0.5))
    v + k*(v - v*v*v);
function _wave_value(deg) = _wave_profile(sin(deg));

function _bottom_pts(inset=0) =
    let(x0=core_left+corner_radius,
        x1=core_right-corner_radius,
        L=x1-x0,
        nw=_edge_waves(L,wave_pitch),
        st=_edge_steps(L,wave_pitch))
    [for(i=[0:st])
        [x0 + L*i/st,
         core_bottom + inset - wave_amplitude*_wave_value(360*nw*i/st)]];

function _right_pts(inset=0) =
    let(y0=core_bottom+corner_radius,
        y1=core_top-corner_radius,
        L=y1-y0,
        nw=_edge_waves(L,wave_pitch),
        st=_edge_steps(L,wave_pitch))
    [for(i=[0:st])
        [core_right - inset + wave_amplitude*_wave_value(360*nw*i/st),
         y0 + L*i/st]];

function _top_pts(inset=0) =
    let(x0=core_right-corner_radius,
        x1=core_left+corner_radius,
        L=x0-x1,
        nw=_edge_waves(L,wave_pitch),
        st=_edge_steps(L,wave_pitch))
    [for(i=[0:st])
        [x0 - L*i/st,
         core_top - inset + wave_amplitude*_wave_value(360*nw*i/st)]];

function _left_pts(inset=0) =
    let(y0=core_top-corner_radius,
        y1=core_bottom+corner_radius,
        L=y0-y1,
        nw=_edge_waves(L,wave_pitch),
        st=_edge_steps(L,wave_pitch))
    [for(i=[0:st])
        [core_left + inset - wave_amplitude*_wave_value(360*nw*i/st),
         y0 - L*i/st]];

// Continue the same radial wave through each rounded corner.  The phase is
// reset to zero at both straight-to-arc joins, so every corner starts and
// ends on the nominal radius instead of leaving a visible step.  Two cycles
// fit the 90-degree arc at the default 15 mm radius (about 11.8 mm pitch).
function _corner_waves() =
    max(1, round((corner_radius*PI/2)/wave_pitch));

function _corner_pts(cx,cy,a0,a1,inset=0) =
    let(nw=_corner_waves(), st=max(16,nw*max(8,wave_softness*3)),
        r=corner_radius-inset)
    [for(i=[1:st])
        let(t=i/st,
            a=a0+(a1-a0)*t,
            rr=r + wave_amplitude*_wave_value(360*nw*t))
        [cx + rr*cos(a), cy + rr*sin(a)]];

module wavy_body_2d(inset=0) {
    pts = concat(
        _bottom_pts(inset),
        _corner_pts(core_right-corner_radius, core_bottom+corner_radius, -90, 0, inset),
        _right_pts(inset),
        _corner_pts(core_right-corner_radius, core_top-corner_radius, 0, 90, inset),
        _top_pts(inset),
        _corner_pts(core_left+corner_radius, core_top-corner_radius, 90, 180, inset),
        _left_pts(inset),
        _corner_pts(core_left+corner_radius, core_bottom+corner_radius, 180, 270, inset)
    );
    polygon(points=pts);
}

module border_ring_2d() {
    // Two nested copies of the same wave avoid the cusps produced by offset(delta).
    difference() {
        wavy_body_2d(border_edge_gap);
        wavy_body_2d(border_edge_gap+border_width);
    }
}

module title_face_2d() {
    rotate(title_angle)
        text(title_text,
             size=title_size,
             font=font_title,
             halign="center",
             valign="center",
             spacing=1.0);
}

module title_outer_2d() {
    offset(delta=title_stroke)
        title_face_2d();
}

module title_outline_2d() {
    difference() {
        title_outer_2d();
        title_face_2d();
    }
}

// One continuous clearance around the complete title, including its accents.
// Derived from the actual glyph shapes so a different title needs no X offsets.
module title_wave_clearance_2d() {
    translate([overall_width/2 + title_x_adjust, title_center_y])
        offset(delta=title_safe_gap)
            hull()
                title_outer_2d();
}

function magnet_hole_count(w) = floor((w - 2*magnet_end_inset)/magnet_center_pitch) + 1;
function magnet_first_hole_x(w) = (w - (magnet_hole_count(w)-1)*magnet_center_pitch)/2;

module rounded_recess(x, y, w, h, r, depth=slot_depth) {
    hole_count = magnet_hole_count(w);
    first_hole_x = x + magnet_first_hole_x(w);
    assert(base_thickness > depth + magnet_hole_depth,
           "Magnet holes would pass through the board");
    assert(h >= magnet_hole_d && magnet_end_inset >= magnet_hole_d/2 && hole_count >= 2,
           "Recess is too small for two magnet holes");
    union() {
        translate([x, y, base_thickness-depth])
            linear_extrude(height=depth+0.05)
                rounded_rect_2d(w, h, r);

        for (i=[0:hole_count-1])
            translate([first_hole_x+i*magnet_center_pitch,
                       y+h/2,
                       base_thickness-depth-magnet_hole_depth])
                cylinder(h=magnet_hole_depth+depth+0.05, d=magnet_hole_d);
    }
}

// -------------------------------------------------------------
// 6) PARAMETRIC SCHEDULE GRID
// -------------------------------------------------------------

module schedule_grid(y0, rows) {
    cols = n_days();
    cg = column_gap(cols);

    assert(rows >= 0, "Period count cannot be negative");
    assert(cols >= 1, "At least one day is required");
    assert(cg >= 0 || auto_expand_width,
           "Columns do not fit. Enable auto_expand_width or reduce card_length.");

    for (r=[0:rows-1])
        for (c=[0:cols-1]) {
            x = grid_left + c*(card_length+cg);
            y = y0 + r*row_pitch;
            rounded_recess(
                x - slot_tolerance/2,
                y - slot_tolerance/2,
                card_length + slot_tolerance,
                card_width + slot_tolerance,
                slot_corner_radius,
                slot_depth
            );
        }
}

module weekday_labels() {
    cols = n_days();
    cg = column_gap(cols);
    for (c=[0:cols-1]) {
        xc = grid_left + c*(card_length+cg) + card_length/2;
        translate([xc, weekday_y, base_thickness])
            linear_extrude(height=label_relief)
                text(days[c], size=weekday_size, font=font_labels,
                     halign="center", valign="center");
    }
}

module side_labels() {
    x = side_label_x_ref + side_label_x_adjust;

    if (show_morning && morning_periods > 0) {
        h = card_width + (morning_periods-1)*row_pitch;
        yc = morning_grid_y0 + h/2;
        translate([x, yc, base_thickness])
            rotate([0,0,90])
                linear_extrude(height=label_relief)
                    text(morning_text, size=side_label_size, font=font_labels,
                         halign="center", valign="center");
    }

    if (show_afternoon && afternoon_periods > 0) {
        h = card_width + (afternoon_periods-1)*row_pitch;
        yc = afternoon_grid_y0 + h/2;
        translate([x, yc, base_thickness])
            rotate([0,0,90])
                linear_extrude(height=label_relief)
                    text(afternoon_text, size=side_label_size, font=font_labels,
                         halign="center", valign="center");
    }
}

// -------------------------------------------------------------
// 7) MAIN BOARD
// -------------------------------------------------------------

module schedule_board() {
    assert(overall_width <= max_board_width,
           "Board exceeds max_board_width; shorten subtitle_text or slogan_text, or reduce its text size");
    assert(max(subtitle_block_length, slogan_block_length)
           <= core_width - 2*detachable_block_side_margin,
           "A detachable block does not fit; enable auto_expand_width or shorten its text");
    // Keep differently colored solids separate in the CSG tree.
    color(board_color)
        difference() {
            linear_extrude(height=base_thickness)
                difference() {
                    wavy_body_2d();
                    // Remove only the top wave; the lower title stays joined to the base.
                    intersection() {
                        title_wave_clearance_2d();
                        translate([0, core_top-wave_amplitude])
                            square([overall_width, overall_width]);
                    }
                }

            // Wall hanging holes
            if (show_wall_holes)
                for (p=[[wall_hole_x_l,wall_hole_y],[wall_hole_x_r,wall_hole_y]])
                    translate([p[0], p[1], -0.1])
                        cylinder(h=base_thickness+border_relief+1, d=wall_hole_d, $fn=40);

            // Empty detachable-block pockets and schedule pockets
            rounded_recess(subtitle_slot_x0, subtitle_slot_y0,
                           subtitle_block_length, subtitle_block_width, 4.0, slot_depth);
            rounded_recess(middle_block_x0, middle_block_y0,
                           slogan_block_length, slogan_block_width, 4.0, slot_depth);
            if (show_afternoon && afternoon_periods > 0)
                schedule_grid(afternoon_grid_y0, afternoon_periods);
            if (show_morning && morning_periods > 0)
                schedule_grid(morning_grid_y0, morning_periods);
        }

    color(board_accent_color) {
        translate([0,0,base_thickness])
            linear_extrude(height=border_relief)
                difference() {
                    border_ring_2d();
                    title_wave_clearance_2d();
                }
        weekday_labels();
        side_labels();
    }

    // The title starts at the underside; its outline takes the accent color
    // only above the base surface.
    translate([overall_width/2 + title_x_adjust, title_center_y, 0]) {
        color(board_color)
            linear_extrude(height=base_thickness)
                title_outline_2d();
        color(board_accent_color)
            translate([0, 0, base_thickness])
                linear_extrude(height=title_relief)
                    title_outline_2d();
        color(board_color)
            linear_extrude(height=base_thickness+title_relief+title_face_above_stroke)
                title_face_2d();
    }
}

// -------------------------------------------------------------
// 8) OPTIONAL SEPARATE BLOCKS (not rendered by default)
// -------------------------------------------------------------

module simple_detachable_block(w, h, protrude, label, label_size, label_font,
                               label_stroke, corner_r=4.0,
                               text_relief=title_relief+title_face_above_stroke,
                               base_color=block_color, text_color=block_text_color,
                               outline_color=block_outline_color, text_growth=0) {
    block_base = slot_depth + protrude;
    hole_count = magnet_hole_count(w);
    first_hole_x = magnet_first_hole_x(w);
    assert(block_base >= magnet_hole_depth + block_wall,
           "Detachable block is too thin above its magnet holes");
    assert(h >= magnet_hole_d && magnet_end_inset >= magnet_hole_d/2 && hole_count >= 2,
           "Detachable block is too small for two magnet holes");
    color(base_color)
        difference() {
            linear_extrude(height=block_base)
                rounded_rect_2d(w, h, corner_r);
            for (i=[0:hole_count-1])
                translate([first_hole_x+i*magnet_center_pitch, h/2, -0.05])
                    cylinder(h=magnet_hole_depth+0.05, d=magnet_hole_d);
        }
    if (label != "")
        translate([w/2, h/2, block_base]) {
            if (label_stroke > 0)
                color(outline_color)
                    linear_extrude(height=title_relief)
                        difference() {
                            offset(delta=label_stroke)
                                text(label, size=label_size, font=label_font,
                                     halign="center", valign="center");
                            text(label, size=label_size, font=label_font,
                                 halign="center", valign="center");
                        }
            color(text_color)
                linear_extrude(height=text_relief)
                    if (text_growth > 0)
                        offset(delta=text_growth)
                            text(label, size=label_size, font=label_font,
                                 halign="center", valign="center");
                    else
                        text(label, size=label_size, font=label_font,
                             halign="center", valign="center");
        }
}

module subtitle_block() {
    simple_detachable_block(subtitle_block_length,
                            subtitle_block_width,
                            subtitle_block_protrude,
                            subtitle_text,
                            subtitle_size,
                            font_subtitle,
                            subtitle_stroke);
}

module slogan_block() {
    end_space = (slogan_block_length - slogan_text_metrics.size[0])/2;
    block_base = slot_depth + slogan_block_protrude;
    union() {
        simple_detachable_block(slogan_block_length,
                                slogan_block_width,
                                slogan_block_protrude,
                                slogan_text,
                                slogan_size,
                                font_labels,
                                slogan_stroke);
        for (x=[end_space/2, slogan_block_length-end_space/2])
            color(block_outline_color)
                translate([x, slogan_block_width/2, block_base])
                    linear_extrude(height=title_relief)
                        text(slogan_icon, size=slogan_icon_size, font=font_emoji,
                             halign="center", valign="center");
    }
}

module name_slogan_sheet() {
    assert(max(subtitle_block_length, slogan_block_length) <= max_board_width,
           "Name or slogan block exceeds max_board_width");
    subtitle_block();
    translate([0, subtitle_block_width+subject_sheet_gap, 0])
        slogan_block();
}

module subject_block(index) {
    assert(index >= 0 && index < len(subject_names), "Invalid subject_index");
    assert(len(subject_labels) == len(subject_names),
           "subject_labels and subject_names must have the same number of entries");
    label = subject_labels[index];
    block_protrude = subject_block_total_height - slot_depth - subject_text_relief;
    simple_detachable_block(card_length, card_width, block_protrude,
                            label, subject_size, font_subject,
                            0, slot_corner_radius, subject_text_relief,
                            subject_color, subject_text_color,
                            text_growth=subject_text_growth);
}

module subject_sheet() {
    cols = max(1, floor((max_board_width+subject_sheet_gap)
                         / (card_length+subject_sheet_gap)));
    assert(card_length <= max_board_width,
           "Subject card exceeds max_board_width");
    for (i=[0:len(subject_names)-1])
        translate([(i%cols)*(card_length+subject_sheet_gap),
                   floor(i/cols)*(card_width+subject_sheet_gap), 0])
            subject_block(i);
}

// Preview the removable parts seated in their matching recesses.
// Subject labels are split evenly between morning and afternoon, then
// placed left-to-right from the top row of each section.
module assembled_board() {
    schedule_board();

    translate([subtitle_slot_x0, subtitle_slot_y0, base_thickness-slot_depth])
        subtitle_block();
    translate([middle_block_x0, middle_block_y0, base_thickness-slot_depth])
        slogan_block();

    morning_subjects = ceil(len(subject_labels)/2);
    afternoon_subjects = len(subject_labels)-morning_subjects;
    morning_slots = show_morning ? n_days()*morning_periods : 0;
    afternoon_slots = show_afternoon ? n_days()*afternoon_periods : 0;
    morning_count = min(morning_subjects, morning_slots);
    afternoon_count = min(afternoon_subjects, afternoon_slots);
    cg = column_gap(n_days());

    if (morning_count < morning_subjects || afternoon_count < afternoon_subjects)
        echo("Some subject cards cannot fit in the visible schedule grid");

    if (morning_count > 0)
        for (i=[0:morning_count-1]) {
            col = i % n_days();
            row = morning_periods-1-floor(i/n_days());
            translate([grid_left+col*(card_length+cg),
                       morning_grid_y0+row*row_pitch,
                       base_thickness-slot_depth])
                subject_block(i);
        }

    if (afternoon_count > 0)
        for (i=[0:afternoon_count-1]) {
            col = i % n_days();
            row = afternoon_periods-1-floor(i/n_days());
            translate([grid_left+col*(card_length+cg),
                       afternoon_grid_y0+row*row_pitch,
                       base_thickness-slot_depth])
                subject_block(morning_subjects+i);
        }
}

// -------------------------------------------------------------
// 9) OUTPUT
// -------------------------------------------------------------
// Default preview: assembled board with removable blocks seated in their pockets.

if (output_part == "assembled")
    assembled_board();
else if (output_part == "board")
    schedule_board();
else if (output_part == "name_slogan")
    name_slogan_sheet();
else if (output_part == "subtitle")
    subtitle_block();
else if (output_part == "slogan")
    slogan_block();
else if (output_part == "subject")
    subject_block(subject_index);
else if (output_part == "subjects")
    subject_sheet();
else
    assert(false, "output_part must be assembled, board, name_slogan, subtitle, slogan, subject, or subjects");

// Baseline diagnostics (visible in OpenSCAD console):
echo("overall_width ~=", overall_width);
echo("approx_overall_height ~=", approx_overall_height);
echo("target_overall_z =", target_overall_z);
echo("base_thickness =", base_thickness);
echo("raised decorative top Z =", base_thickness + max(border_relief, label_relief, title_relief+title_face_above_stroke));
echo("column_gap =", column_gap(n_days()));
echo("card_length =", card_length);
echo("subtitle_block_length =", subtitle_block_length);
echo("slogan_block_length =", slogan_block_length);
