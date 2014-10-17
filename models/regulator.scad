use <../lib/utils.scad>;
use <../lib/28byj.scad>;

thick = 4;
zip_pos = (35 - 12.5)/3 + 12.5;

module knob() {
	cylinder(r=47.6/2, h=13.33);
	for (i=[0:10]) {
		rotate([0,0,36*i]) translate([-3.5/2, 20]) 
			cube([3.5, 1.2+7.6/2, 13.33]);
	}
}

module regulator(knob=false) {
	$fn=128;
	color("gray") {
	translate([0,0,-3.3-1.8]) cylinder(r=67/2, h=2);
	translate([0,0,-3.3]) cylinder(r=36, h=6.6);
	hull() {
		translate([0,0,3.0]) cylinder(r=32.5, h=2.5);
		translate([0,0,3.3+2.4]) cylinder(r1=32, r2=12.5, h=8.4);
	}
	translate([0,0,3.3+2.4+8.4]) cylinder(r=12.5, h=2.4);
	//tube
	translate([-15.4/2,-35,-10]) cube([15.4, 70, 10]);
	}
	color("red") {
			//knob
	if (knob) translate([0,0,3.1+2.4*2+8.4]) knob();

	}
}

module zipties() {
	translate([0,-zip_pos+3]) rotate([90,0]) rotate([0,0,90]) 
		ziptie2(40, 65);
	translate([0,zip_pos+3]) rotate([90,0]) rotate([0,0,90]) 
		ziptie2(40, 65);
}

module holder() {
	difference() {
		intersection()	 {
			translate([0,0,-3.3-thick]) scale([1,1.4]) cylinder(r=36+thick, h=16, $fn=128);
			translate([36+thick-20,-zip_pos-3-thick, -10]) cube([20, 2*zip_pos+6+2*thick,20]);
		}
		regulator();
		zipties();
	}
}
module motor_holder() {
	difference() {
		union() {
			//top motor plate
			intersection() {
				translate([0,0,-3.3-2*thick+16]) scale([1.45,1.2]) 
					cylinder(r=36+thick, h=thick, $fn=128);
				translate([-36-thick-20,-zip_pos-3-thick, -10]) 
					cube([40, 2*zip_pos+6+2*thick,20]);
			}
			
			intersection() {
				translate([0,0,-3.3-thick]) scale([1,1.4]) cylinder(r=36+thick, h=16, $fn=128);
				translate([-36-thick-20,-zip_pos-3-thick, -10]) cube([40, 2*zip_pos+6+2*thick,20]);
			}
		}
		regulator();
		zipties();
		
		//motor cutout
		translate([-35-14.1,0,-10]) {
			cylinder(r=14.5, h=20, $fn=64);
			translate([-50,-14.5]) cube([50,29,20]);
			translate([0,-35/2]) cylinder(r=1.8, h=50);
			translate([0, 35/2]) cylinder(r=1.8, h=50);
		}
	}
}

//horizontal
//translate([0,0,3.1+thick]) rotate([180,0]) 
//vertical
translate([0,0,zip_pos+3+thick]) rotate([90,0]) 
{
//translate([20,0,-20]) rotate([0,-90])
holder();
//translate([-20,0,-20]) rotate([0,90]) 
motor_holder();
}

//regulator(true);
//translate([-35-14,0,-8]) rotate([0,0,-90]) stepper28BYJ();
/*
use <gears.scad>;
%translate([0,0,20]) gear_large();
%translate([-35-6,0,28]) rotate([180,0]) gear_small();
//zipties();*/