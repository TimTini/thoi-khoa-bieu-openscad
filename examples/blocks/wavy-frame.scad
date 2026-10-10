// Wavy rounded plate with a raised decorative border.
// Dimensions are millimetres; the total envelope remains 240 x 225 x 6.
length_x = 240;
width_y = 225;
thickness_z = 6;
corner_radius = 15;
border_width = 1.6;
border_inset = 2.0;
wave_amplitude = 1.5;
wave_pitch = 9.8;
corner_softness = 6;
border_relief = 0.4; // Example raised height; adjust to suit the print.

// Positive softness increases the rounding of each wave crest and trough.
function softened_wave(angle, softness) =
    let (rounding = min(0.1, max(0, softness/100)))
    (sin(angle) + rounding*sin(3*angle))/(1-rounding);
function rounded_perimeter(w, h, r) =
    let (straight_x = w - 2*r, straight_y = h - 2*r, quarter = PI*r/2)
    2*straight_x + 2*straight_y + 4*quarter;

function rounded_point(s, w, h, r) =
    let (sx = w - 2*r,
         sy = h - 2*r,
         arc = PI*r/2,
         c1 = sx,
         c2 = c1 + arc,
         c3 = c2 + sy,
         c4 = c3 + arc,
         c5 = c4 + sx,
         c6 = c5 + arc,
         c7 = c6 + sy)
    s < c1 ? [r+s, 0] :
    s < c2 ? let (a = -90 + 90*(s-c1)/arc) [w-r+r*cos(a), r+r*sin(a)] :
    s < c3 ? [w, r+s-c2] :
    s < c4 ? let (a = 90*(s-c3)/arc) [w-r+r*cos(a), h-r+r*sin(a)] :
    s < c5 ? [w-r-(s-c4), h] :
    s < c6 ? let (a = 90 + 90*(s-c5)/arc) [r+r*cos(a), h-r+r*sin(a)] :
    s < c7 ? [0, h-r-(s-c6)] :
    let (a = 180 + 90*(s-c7)/arc) [r+r*cos(a), r+r*sin(a)];

function rounded_normal(s, w, h, r) =
    let (sx = w - 2*r,
         sy = h - 2*r,
         arc = PI*r/2,
         c1 = sx,
         c2 = c1 + arc,
         c3 = c2 + sy,
         c4 = c3 + arc,
         c5 = c4 + sx,
         c6 = c5 + arc,
         c7 = c6 + sy)
    s < c1 ? [0, -1] :
    s < c2 ? let (a = -90 + 90*(s-c1)/arc) [cos(a), sin(a)] :
    s < c3 ? [1, 0] :
    s < c4 ? let (a = 90*(s-c3)/arc) [cos(a), sin(a)] :
    s < c5 ? [0, 1] :
    s < c6 ? let (a = 90 + 90*(s-c5)/arc) [cos(a), sin(a)] :
    s < c7 ? [-1, 0] :
    let (a = 180 + 90*(s-c7)/arc) [cos(a), sin(a)];

function wavy_points(w, h, r, amplitude, pitch, softness) =
    let (base_w = w - 2*amplitude,
         base_h = h - 2*amplitude,
         perimeter = rounded_perimeter(base_w, base_h, r),
         cycles = max(1, round(perimeter/pitch)),
         effective_pitch = perimeter/cycles,
         samples_per_wave = max(16, ceil(softness*4)),
         sample_count = cycles*samples_per_wave,
         raw = [for (i = [0 : sample_count-1])
             let (s = perimeter*i/sample_count,
                  p = rounded_point(s, base_w, base_h, r),
                  n = rounded_normal(s, base_w, base_h, r),
                  displacement = amplitude*softened_wave(360*s/effective_pitch, softness))
             [p[0] + displacement*n[0], p[1] + displacement*n[1]]],
         min_x = min([for (p = raw) p[0]]),
         max_x = max([for (p = raw) p[0]]),
         min_y = min([for (p = raw) p[1]]),
         max_y = max([for (p = raw) p[1]]))
    [for (p = raw)
        [(p[0]-min_x)*w/(max_x-min_x), (p[1]-min_y)*h/(max_y-min_y)]];

module wavy_outline_2d() {
    polygon(points = wavy_points(length_x, width_y, corner_radius,
                                 wave_amplitude, wave_pitch, corner_softness));
}

module decorative_border_2d() {
    difference() {
        offset(delta = -border_inset) wavy_outline_2d();
        offset(delta = -(border_inset + border_width)) wavy_outline_2d();
    }
}

assert(length_x > 0 && width_y > 0, "Plate dimensions must be positive.");
assert(thickness_z > 0, "Thickness must be positive.");
assert(corner_radius > 0 && corner_radius < min(length_x, width_y)/2,
       "Corner radius must fit the plate.");
assert(wave_amplitude > 0 && wave_amplitude < min(length_x, width_y)/4,
       "Wave amplitude is outside the supported range.");
assert(wave_pitch > 0 && corner_softness > 0,
       "Wave pitch and softness must be positive.");
assert(border_width > 0 && border_inset > 0,
       "Border width and inset must be positive.");
assert(border_relief > 0 && border_relief < thickness_z,
       "Raised border must be lower than total plate thickness.");

union() {
    linear_extrude(height = thickness_z - border_relief)
        wavy_outline_2d();

    // Small overlap makes the raised border fuse cleanly with the plate body.
    translate([0, 0, thickness_z - border_relief - 0.01])
        linear_extrude(height = border_relief + 0.01)
            decorative_border_2d();
}
