include <global_vars.scad>;

difference(){
    union(){
        XYcenteredCube(lightBox_side, lightBox_side, lightBox_height);
        lightBoxPegs();
    }
    //ribs
    translate([-lightBox_side/2, -lightBox_side/2, lightBox_height-ribDeep+0.001]){
        regularRibs(lightBox_side, lightBox_side, ribThick=1, ribSpace=2);
    }
    //main cutout
    XYcenteredCube(lightBox_side-2*lightBox_shellThick, lightBox_side-2*lightBox_shellThick, lightBox_height-lightBox_shellThick-lightFilter_thick);
    //filter recess
    XYcenteredCube(lightFilter_side, lightFilter_side, lightBox_height-lightBox_shellThick);
    //window
    XYcenteredCube(lightBox_cutthrough, lightBox_cutthrough, lightBox_height);
    //cord hole
    translate([lightBox_side/2-lightBox_cordHole_edgeOffset,lightBox_side/2,  0]){
        rotate([90,0,0]){
            cylinder(d=lightBox_cordHoleD, lightBox_shellThick, $fn=fn);
        }
    }
    //mast holes
    tall = lightBox_height-lightFilter_thick;
    translate([0,0,lightBox_height]){
        color("blue")
        tripleMastHoleToCut(gm_tall=lightFilter_thick-lightBox_shellThick+1, r=1, fn=5);}
}

    tall = lightBox_height-lightFilter_thick;

