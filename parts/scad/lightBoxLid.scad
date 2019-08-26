include <global_vars.scad>;


difference(){
    XYcenteredCube(lightBox_side, lightBox_side, lightBox_shellThick);
    lightBoxPegs(s=lightBox_shellThick+tol*2, p=lightBox_side+tol/2, up=0);
    //ribs
    translate([-lightBox_side/2, -lightBox_side/2,0]){
        regularRibs(lightBox_side, lightBox_side);
    }
    //window
    XYcenteredCube(lightBox_cutthrough, lightBox_cutthrough, lightBox_height);
}

