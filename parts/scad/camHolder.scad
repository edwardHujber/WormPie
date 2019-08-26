// Z axis is optical axis.

include <global_vars.scad>;

difference(){
    union(){
        XYcenteredRoundedCube(camHolder_squareSide, camHolder_squareSide, camHolder_tall, camHolder_tall/2);
        tripleMastGrip(mast_length, mast_width, mastGrips_thick, camHolder_tall, mastGrips_tall, mast_offset, tol);
    }
    
    // picam
    translate([0,0,camHolder_tall-piCamB2_tall]){
        square_with_pulled_out_corners(side=piCamB2_side,h=piCamB2_tall+tol, r=200);
    }
    //cutthrough
    translate([0,0,-tol/2]){
        XYcenteredCube(piCamB2_side-piCamB2_ledge,piCamB2_side-piCamB2_ledge,camHolder_tall+tol);
    }
    //cable
    //translate([-(piCamB2cable_wide+tol)/2, (piCamB2cable_wide+tol)/2, camHolder_tall-piCamB2_tall]){
    //    cube([piCamB2cable_wide+tol, piCamB2cable_deep+tol, piCamB2_tall+tol]);
    //    }
}
