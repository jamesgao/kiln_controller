use <involute_gears.scad>;
use <utils.scad>;
use <regulator.scad>;

gsmall = 11;
glarge = 30;
sep = 35+6.1;


pitch = (sep * 2 * 180) / (glarge + gsmall);

module herringbone(teeth, height, pitch=pitch, twist=120, pressure_angle=20) {
    translate([0,0,height/2]) {
	    gear (number_of_teeth=teeth,
		    circular_pitch=pitch,
		    pressure_angle=pressure_angle,
		    clearance = 0.2,
		    gear_thickness = height/2,
		    rim_thickness = height/2,
		    rim_width = 5,
		    hub_thickness=0,
		    bore_diameter=0,
		    twist=twist/teeth);
	    mirror([0,0,1])
	    gear (number_of_teeth=teeth,
		    circular_pitch=pitch,
		    pressure_angle=pressure_angle,
		    clearance = 0.2,
		    gear_thickness = height/2,
		    rim_thickness = height/2,
		    rim_width = 5,
		    hub_thickness = 0,
		    bore_diameter=0,
		    circles=circles,
		    twist=twist/teeth);
	}
}
module bevel_herringbone(teeth, height, pitch=pitch, bevel=0) {
    diam = teeth * pitch / 180;
    intersection() {
        herringbone(teeth, height, pitch=pitch);
        cylinder(r2=diam/2-bevel, r1=diam/2+height-bevel, h=height);
        cylinder(r1=diam/2-bevel, r2=diam/2+height-bevel, h=height);
    }
}

module gear_small() {
    module setscrew() {
        translate([0,0,-1]) polyhole(20, 5);
        translate([0,0,8+4]) rotate([0,90]) polyhole(10, 4);
        translate([2.5,-7.25/2,8]) cube([3.5, 7.25, 10]);
    }
    difference() {
        union() {
            mirror([0,0]) bevel_herringbone(gsmall, 8);
            translate([0,0,8]) cylinder(r=20/2, h=8);
        }
        setscrew();
        rotate([0,0,180]) setscrew();
        //translate([10-1, -5,8]) cube([3, 10, 10]);
    }
}

module gear_large() {
    diam = glarge * pitch / 180;

    difference() {
        bevel_herringbone(glarge, 8);
        translate([0,0,-1]) knob();
    }
}

translate([-gsmall * pitch / 180 / 2,0, 0]) rotate([0,0,360/gsmall*0]) gear_small();
translate([glarge * pitch / 180 / 2+10,0]) gear_large();

