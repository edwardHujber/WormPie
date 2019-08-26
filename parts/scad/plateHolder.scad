// Z axis is optical axis.

include <global_vars.scad>;


// standard plate
plate_lid_diameter = 55.5;
plate_bottom_diameter = 51.0;

/*
// small plate
plate_lid_diameter = 40.0;
plate_bttomrim_diameter = 38.75;
plate_bottom_diameter = 37.2;
*/

difference(){
    union(){
        cylinder(r=(plate_lid_diameter/2)+plateHolder_R_tol+plateHolder_Rthick, plateHolder_tall, $fn=fn);
        tripleMastGrip();
        }
    translate([0,0,plateHolder_Rthick]){
        cylinder(r=(plate_lid_diameter/2)+plateHolder_R_tol, plateHolder_tall, $fn=fn);
    }
    translate([0,0,plateHolder_Rthick/2]){
        cylinder(r=(plate_bottom_diameter/2)+plateHolder_R_tol, plateHolder_tall, $fn=fn);
    }
    cylinder(r=(plate_bottom_diameter/2)-plateHolder_lip, plateHolder_tall, $fn=fn);

}