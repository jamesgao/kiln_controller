tube = .775*25.4;
wing = 10;
thick = 5;

delta = .2;

$fn=128;

length = tube+2*wing+2*thick;

module profile() {
	module solids() {
		translate([-length/2,0]) square([length, thick]);
		translate([-tube/2-thick,0]) square([tube+2*thick, tube/2-delta]);
		intersection() {
			translate([0,tube/2-delta]) circle(r=tube/2+thick);
			translate([-tube/2-thick,0]) square([tube+2*thick, tube+thick-delta]);
		}
	}
	difference() {
		solids();
		translate([0,tube/2-delta]) circle(r=tube/2);
		translate([-tube/2,-thick-delta]) square([tube, thick+tube/2]);
	}
}

module screw() {
	rotate([-90,0]) translate([0,0,-1]) {
		cylinder(r=1.8, h=thick+2);
	}
}
module bracket() {
	screw_pos = tube/2+thick+wing/2;
	difference() {
		linear_extrude(height=length) profile();
		translate([-screw_pos,0,wing/2]) screw();
		translate([-screw_pos,0,length-wing/2]) screw();
		translate([screw_pos,0,wing/2]) screw();
		translate([screw_pos,0,length-wing/2]) screw();
	}
}
bracket();
//translate([0,-5]) rotate([90,0]) bracket();