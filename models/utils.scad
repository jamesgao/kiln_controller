use <MCAD/nuts_and_bolts.scad>;

module nut(flats, h=1) {
    cylinder(r=flats/sqrt(3), h=h, $fn=6);
}

module polyhole(h, d) {
    n = max(round(2 * d),3);
    rotate([0,0,180])
        cylinder(h = h, r = (d / 2) / cos (180 / n), $fn = n);
}

module ccube(size=[1,1,1]) {
    translate([-size[0]/2,-size[1]/2,0]) cube(size);
}

module rrect(size=[10,10,1], rad=1, center=false, $fn=36) {
    hull() {
        translate([rad, rad]) cylinder(r=rad, h=size[2], $fn=$fn);
        translate([size[0]-rad,rad]) cylinder(r=rad, h=size[2], $fn=$fn);
        translate([rad, size[1]-rad]) cylinder(r=rad, h=size[2], $fn=$fn);
        translate([size[0]-rad, size[1]-rad]) cylinder(r=rad, h=size[2], $fn=$fn);
    }
}

module tube(r=10, h=10, thick=2) {
    difference() {
        cylinder(r=r+thick, h);    
        translate([0,0,-1]) cylinder(r=r, h=h+2);
    }
}

module ziptie(tube=25.4, zthick=2, zwidth=6) {
    difference() {
        cylinder(r=tube/2+thick+zthick, h=zwidth);
        translate([0,0,-1]) cylinder(r=tube/2+thick, h=zwidth+2);
    }
}
module ziptie2(diam, outer, width=6, thick=2) {
    scale([1,outer/diam]) difference() {
        cylinder(r=diam/2+thick, h=width);
        translate([0,0,-1]) cylinder(r=diam/2, h=width+2);
    }
}

module spiral(r1=20, r2=25, thick=2, $fn=36, wedge=[0, 360]) {
    inc = 360 / $fn;
    for (t=[wedge[0]:inc:wedge[1]-inc]) {
        assign( ra = (1 - t/wedge[1]) * r1 + t/wedge[1] * r2, 
                rb=(1-(t+inc)/wedge[1])*r1 + (t+inc)/wedge[1] * r2) {
            polygon([
                [ra*cos(t), ra*sin(t)], 
                [(ra+thick)*cos(t),(ra+thick)*sin(t)], 
                [(rb+thick)*cos(t+inc), (rb+thick)*sin(t+inc)], 
                [rb*cos(t+inc), rb*sin(t+inc)]
            ]);
        }
    }
}

module frustum(a=[1,1,1,1], h=10) {
	polyhedron(
		points=[
			[0,0,0],[a[0],0,0],[a[0],a[1],0],[0,a[1],0],
			[a[0]/2-a[2]/2,a[1]/2-a[3]/2,h],
			[a[0]/2+a[2]/2,a[1]/2-a[3]/2,h],
			[a[0]/2+a[2]/2,a[1]/2+a[3]/2,h],
			[a[0]/2-a[2]/2,a[1]/2+a[3]/2,h]],
		triangles = [
			[0,2,3],[0,1,2],[0,4,5],[0,5,1],
			[1,5,6],[1,6,2],[2,6,7],[2,7,3],
			[3,7,4],[3,4,0],[4,6,5],[4,7,6]
		]
	);
}

module eyelet(d=10, h=10, hole=3, thick=2, nut=0, bolt=false) {
    difference() {
        union() {
            translate([-d/2,0]) cube([d, h, thick]);
            translate([0, h, 0]) cylinder(r=d/2, h=thick, $fn=72);
        }
        if (nut > 0) translate([0,h,-.01]) nutHole(nut);
        if (bolt) translate([0,h,thick-2]) mirror([0,0,1]) boltHole(hole, length=thick);
        else translate([0, h, -1]) polyhole(thick+2, hole);
    }
}

module double_eyelet(d=20, h=20, hole=3, thick=2, rad=5, nut=0, bolt=false) {
    translate([0, h-rad,0]) difference() {
        hull() {
            translate([rad-d/2, 0,0]) cylinder(r=rad, h=thick);
            translate([d/2-rad, 0,0]) cylinder(r=rad, h=thick);
            translate([-d/2,rad-h,0]) cube([d,1, thick]);
        }
        if (nut > 0) {
            translate([rad-d/2, 0, 0]) nutHole(nut);
            translate([d/2-rad, 0, 0]) nutHole(nut);
        }
        if (bolt) {
            translate([rad-d/2, 0, thick-2]) mirror([0,0,1]) boltHole(hole, length=thick);
            translate([d/2-rad, 0, thick-2]) mirror([0,0,1]) boltHole(hole, length=thick);
        } else {
            translate([rad-d/2, 0, -1]) polyhole(thick+2, hole);
            translate([d/2-rad, 0, -1]) polyhole(thick+2, hole);
        }
    }
}

module tri_equi(leg=10) {
    translate([0,offset]) difference() {
        translate([-leg/2,0]) square([leg, leg]);
        translate([leg/2,0]) rotate([0, 0, 30]) square([2*leg, 2*leg]);
        translate([-leg/2,0]) rotate([0, 0, -30]) mirror([1,0]) square([2*leg, 2*leg]);
    }
}

/*
module screw(rad, length, tpmm=2, $fn=16) {
    i = 0;
    //translate([0,0,i/$fn*tpmm]) rotate([0,0,i*360/$fn]) 
    linear_extrude(height)
        translate([rad,0,0]) child();
}

*/
