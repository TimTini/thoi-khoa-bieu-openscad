use <../../assets/fonts/Praise/Praise-Regular.ttf>;
use <../../assets/fonts/Protest-Riot/ProtestRiot-Regular.ttf>;
use <../../assets/fonts/Noto-Emoji/NotoEmoji-Bold.ttf>;

/* [Schedule] */
day_count = 6;       // [1:1:7]
morning_rows = 5;
afternoon_rows = 5;

/* [Hidden] */
day_labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
title_text = "Thời khóa biểu";
subtitle_text = "Học sinh mẫu";
slogan_text = "Believe in Yourself";
morning_label = "Sáng";
afternoon_label = "Chiều";

max_dim = 240;
max_print_width = 254;
wave_amplitude = 1.5;
wave_pitch = 9.8;
corner_radius = 15;
wave_softness = 6;
body_thickness = 5.6;
border_width = 1.6;
border_inset = 2.0;
detail_relief = 1.2;

slot_width = 31.0;
slot_height = 11.0;
row_pitch = 15.0;
side_margin = 14.0;
min_column_gap = 1.0;
top_margin = 7.0;
bottom_margin = 9.0;
layout_gap = 5.0;

top_box_width = 80.0;
top_box_height = 14.0;
top_box_radius = 4.0;
separator_width = 140.0;
separator_height = 14.0;
separator_radius = 4.0;

font_title = "Praise";
font_secondary = "Protest Riot";
font_emoji = "Noto Emoji:style=Bold";
title_size = 18.0;
title_outline = 2.0;
subtitle_size = 8.0;
slogan_size = 7.0;
day_label_size = 6.0;
shift_label_size = 6.0;
icon_size = 8.0;

slot_radius = 3.5;
line_width = 0.55;
shift_label_x = 9.0;
$fn = 48;

function session_height(rows) = slot_height + (rows - 1) * row_pitch;
function required_base_width(days) =
    2 * side_margin + days * slot_width + max(0, days - 1) * min_column_gap;
function base_body_width() = max(max_dim, required_base_width(day_count));
function physical_width() = base_body_width() + 2 * wave_amplitude;
function column_gap() =
    day_count <= 1 ? 0 :
    (base_body_width() - 2 * side_margin - day_count * slot_width) / (day_count - 1);
function slot_center_x(column) =
    day_count <= 1 ? physical_width() / 2 :
    wave_amplitude + side_margin + slot_width / 2
        + column * (slot_width + column_gap());

lower_grid_bottom = bottom_margin;
lower_grid_top = lower_grid_bottom + session_height(afternoon_rows);
separator_y = lower_grid_top + layout_gap + separator_height / 2;
morning_grid_bottom = separator_y + separator_height / 2 + layout_gap;
morning_grid_top = morning_grid_bottom + session_height(morning_rows);
weekday_y = morning_grid_top + layout_gap + day_label_size / 2;
top_box_y = weekday_y + day_label_size / 2 + layout_gap + top_box_height / 2;
title_y = top_box_y + top_box_height / 2 + layout_gap + title_size / 2;
physical_height = title_y + title_size / 2 + title_outline + top_margin;
base_body_height = physical_height - 2 * wave_amplitude;

hole_diameter = 4.0;
hole_edge_distance = 12.0;
slot_line_width = line_width;

function softened_wave(angle, softness) =
    let(rounding = min(0.1, max(0, softness / 100)))
    (sin(angle) + rounding * sin(3 * angle)) / (1 - rounding);

function rounded_perimeter(w, h, r) =
    2 * (w - 2 * r) + 2 * (h - 2 * r) + 2 * PI * r;

function rounded_point(s, w, h, r) =
    let(
        sx = w - 2 * r,
        sy = h - 2 * r,
        arc = PI * r / 2,
        c1 = sx,
        c2 = c1 + arc,
        c3 = c2 + sy,
        c4 = c3 + arc,
        c5 = c4 + sx,
        c6 = c5 + arc,
        c7 = c6 + sy
    )
    s < c1 ? [r + s, 0] :
    s < c2 ? let(a = -90 + 90 * (s - c1) / arc) [w-r+r*cos(a), r+r*sin(a)] :
    s < c3 ? [w, r + s - c2] :
    s < c4 ? let(a = 90 * (s - c3) / arc) [w-r+r*cos(a), h-r+r*sin(a)] :
    s < c5 ? [w-r-(s-c4), h] :
    s < c6 ? let(a = 90 + 90 * (s - c5) / arc) [r+r*cos(a), h-r+r*sin(a)] :
    s < c7 ? [0, h-r-(s-c6)] :
    let(a = 180 + 90 * (s - c7) / arc) [r+r*cos(a), r+r*sin(a)];

function rounded_normal(s, w, h, r) =
    let(
        sx = w - 2 * r,
        sy = h - 2 * r,
        arc = PI * r / 2,
        c1 = sx,
        c2 = c1 + arc,
        c3 = c2 + sy,
        c4 = c3 + arc,
        c5 = c4 + sx,
        c6 = c5 + arc,
        c7 = c6 + sy
    )
    s < c1 ? [0, -1] :
    s < c2 ? let(a = -90 + 90 * (s - c1) / arc) [cos(a), sin(a)] :
    s < c3 ? [1, 0] :
    s < c4 ? let(a = 90 * (s - c3) / arc) [cos(a), sin(a)] :
    s < c5 ? [0, 1] :
    s < c6 ? let(a = 90 + 90 * (s - c5) / arc) [cos(a), sin(a)] :
    s < c7 ? [-1, 0] :
    let(a = 180 + 90 * (s - c7) / arc) [cos(a), sin(a)];

function wavy_points(w, h, r, amplitude, pitch, softness) =
    let(
        perimeter = rounded_perimeter(w, h, r),
        cycles = max(1, round(perimeter / pitch)),
        effective_pitch = perimeter / cycles,
        samples_per_wave = max(16, ceil(softness * 4)),
        sample_count = cycles * samples_per_wave
    )
    [
        for (i = [0 : sample_count - 1])
            let(
                s = perimeter * i / sample_count,
                p = rounded_point(s, w, h, r),
                n = rounded_normal(s, w, h, r),
                displacement = amplitude * softened_wave(360 * s / effective_pitch, softness)
            )
            [p[0] + displacement*n[0], p[1] + displacement*n[1]]
    ];

module panel_outline_2d() {
    translate([wave_amplitude, wave_amplitude])
        polygon(points = wavy_points(
            base_body_width(), base_body_height, corner_radius,
            wave_amplitude, wave_pitch, wave_softness
        ));
}

module decorative_border_2d() {
    translate([wave_amplitude, wave_amplitude])
        difference() {
            offset(delta = -border_inset)
                polygon(points = wavy_points(
                    base_body_width(), base_body_height, corner_radius,
                    wave_amplitude, wave_pitch, wave_softness
                ));
            offset(delta = -(border_inset + border_width))
                polygon(points = wavy_points(
                    base_body_width(), base_body_height, corner_radius,
                    wave_amplitude, wave_pitch, wave_softness
                ));
        }
}

module rounded_rect_2d(w, h, r) {
    offset(r = r)
        square([w - 2*r, h - 2*r], center = true);
}

module rounded_rect_outline_2d(w, h, r, stroke) {
    difference() {
        rounded_rect_2d(w, h, r);
        offset(delta = -stroke) rounded_rect_2d(w, h, r);
    }
}

module board_body() {
    difference() {
        linear_extrude(height = body_thickness)
            panel_outline_2d();

        for (x = [hole_edge_distance, physical_width() - hole_edge_distance])
            translate([x, physical_height - hole_edge_distance, -0.01])
                cylinder(h = body_thickness + 0.02, d = hole_diameter);
    }
}

module border_detail() {
    translate([0, 0, body_thickness])
        linear_extrude(height = detail_relief)
            decorative_border_2d();
}

module fixed_box_outlines_2d() {
    union() {
        translate([physical_width() / 2, top_box_y])
            rounded_rect_outline_2d(
                top_box_width, top_box_height, top_box_radius, line_width
            );
        translate([physical_width() / 2, separator_y])
            rounded_rect_outline_2d(
                separator_width, separator_height, separator_radius, line_width
            );
    }
}

module fixed_box_details() {
    translate([0, 0, body_thickness])
        linear_extrude(height = detail_relief)
            fixed_box_outlines_2d();

    translate([physical_width() / 2, top_box_y, body_thickness])
        linear_extrude(height = detail_relief)
            offset(delta = 1.2)
                text(subtitle_text, font = font_secondary, size = subtitle_size,
                     halign = "center", valign = "center");

    translate([physical_width() / 2 - 8, separator_y, body_thickness])
        linear_extrude(height = detail_relief)
            offset(delta = 1.2)
                text(slogan_text, font = font_secondary, size = slogan_size,
                     halign = "center", valign = "center");

    translate([physical_width() / 2 + 43, separator_y, body_thickness])
        linear_extrude(height = detail_relief)
            text("🍀", font = font_emoji, size = icon_size,
                 halign = "center", valign = "center");
}

function morning_center_y(row) =
    morning_grid_bottom + slot_height / 2 + row * row_pitch;
function afternoon_center_y(row) =
    lower_grid_bottom + slot_height / 2 + row * row_pitch;

module schedule_grid_2d() {
    union() {
        for (column = [0 : day_count - 1]) {
            for (row = [0 : morning_rows - 1])
                translate([slot_center_x(column), morning_center_y(row)])
                    rounded_rect_outline_2d(
                        slot_width, slot_height, slot_radius, slot_line_width
                    );

            for (row = [0 : afternoon_rows - 1])
                translate([slot_center_x(column), afternoon_center_y(row)])
                    rounded_rect_outline_2d(
                        slot_width, slot_height, slot_radius, slot_line_width
                    );
        }
    }
}

module schedule_grid_detail() {
    translate([0, 0, body_thickness])
        linear_extrude(height = detail_relief)
            schedule_grid_2d();
}

module schedule_labels_2d() {
    union() {
        for (column = [0 : day_count - 1])
            translate([slot_center_x(column), weekday_y])
                text(day_labels[column], font = font_secondary,
                     size = day_label_size, halign = "center", valign = "center");

        translate([shift_label_x, (morning_grid_bottom + morning_grid_top) / 2])
            rotate(90)
                text(morning_label, font = font_secondary,
                     size = shift_label_size, halign = "center", valign = "center");

        translate([shift_label_x, (lower_grid_bottom + lower_grid_top) / 2])
            rotate(90)
                text(afternoon_label, font = font_secondary,
                     size = shift_label_size, halign = "center", valign = "center");
    }
}

module schedule_labels() {
    translate([0, 0, body_thickness])
        linear_extrude(height = detail_relief)
            schedule_labels_2d();
}

module title_detail() {
    translate([physical_width() / 2, title_y, body_thickness])
        linear_extrude(height = detail_relief)
            offset(delta = title_outline)
                text(title_text, font = font_title, size = title_size,
                     halign = "center", valign = "center");
}

assert(day_count == floor(day_count) && day_count >= 1 && day_count <= len(day_labels),
       "day_count must be an integer from 1 to 7.");
assert(morning_rows == floor(morning_rows) && morning_rows >= 1,
       "morning_rows must be a positive integer.");
assert(afternoon_rows == floor(afternoon_rows) && afternoon_rows >= 1,
       "afternoon_rows must be a positive integer.");
assert(column_gap() >= min_column_gap - 0.0001 || day_count == 1,
       "The day count requires a column gap below the supported minimum.");
assert(physical_width() <= max_print_width + 0.0001,
       "The board exceeds the requested 254 mm printable width.");
assert(base_body_height > 2 * corner_radius,
       "The dynamic panel height is too small for its fixed corner radius.");
assert(row_pitch >= slot_height,
       "row_pitch must leave non-overlapping timetable slots.");
assert(top_box_width < physical_width() - 2 * side_margin,
       "The fixed top box must fit inside the panel.");
assert(separator_width < physical_width() - 2 * side_margin,
       "The fixed separator must fit inside the panel.");

union() {
    board_body();
    border_detail();
    fixed_box_details();
    schedule_grid_detail();
    schedule_labels();
    title_detail();
}
