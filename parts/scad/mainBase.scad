// Z axis is optical axis.

include <global_vars.scad>;

base_thick = 2.5;
base_len = max(lightBox_side,(mast_offset+mastGrips_thick+mast_width)*2+20);
base_heel = 75;
base_toe = 75;

piSlot_len = 10.0;
piSlot_tall = 10.0;
piSlot_setback = 7.5;

dist_to_grip = mast_offset-mastGrips_thick;

difference(){
    union(){
        color([0,0,1])
        hull(){
            for(x=[(base_len-dist_to_grip)/2,-(base_len-dist_to_grip)/2],
                y=[base_heel-dist_to_grip/2,-(base_toe-dist_to_grip*1.0)]){
                translate([x,y,0]){
                    cylinder(h=base_thick, d=dist_to_grip, $fn=fn);
                }
            }
        }
        
        hull(){
            for(x=[mast_offset-dist_to_grip/2,-(mast_offset-dist_to_grip/2)],
                y=[-(base_toe-dist_to_grip),-(base_toe-dist_to_grip*0.5)]){
                translate([x,y,0]){
                    cylinder(h=base_thick, d=dist_to_grip, $fn=fn);
                }
            }
        }
        tripleMastGrip(arms=false);
        translate([-piholder_fin_wide/2, mast_offset+mast_width+mastGrips_thick+wall_thickness, base_thick]){
            difference(){
                union(){
                    roundedCube(piholder_fin_wide, piSlot_len, piSlot_tall, piSlot_len/2.5);
                    fourCylinderCube(piholder_fin_wide, piSlot_len, piSlot_tall/2,piSlot_len/2.5);
                }
                translate([0,(piSlot_len-(piholder_thick+tol))/2 ,0]){
                    cube([piholder_fin_wide, piholder_thick+tol, piSlot_tall]);
                }
            }    
        }
    }
    hull(){
            for(x=[dist_to_grip/2,-dist_to_grip/2],y=[dist_to_grip/2,-dist_to_grip/2]){
                translate([x,y,0]){
                    cylinder(h=plateHolder_tall, d=dist_to_grip, $fn=fn);
                }
            }
        }
    translate([-base_len/2, -base_heel,0]){
        regularRibs(base_len, base_heel+base_toe, ribDeep, 0.75, 2.5);
    } 
}

