include <global_vars.scad>;

difference(){
    union(){
        for(x=[0, pi_len], y=[0, pi_wid]){
            translate([x, y, 0]){
                difference(){
                    cylinder(piPeg_len, r=piPeg_OR, $fn=fn);
                    cylinder(piPeg_len, r=piPeg_IR, $fn=fn);
                }
            }
        }
        
        hull(){
            for(x=[0, pi_len], y=[0, pi_wid]){
                translate([x, y, 0]){
                    difference(){
                        cylinder(piholder_thick, r=piPeg_OR, $fn=fn);
                        cylinder(piholder_thick, r=piPeg_IR, $fn=fn);
                    }
                }
            }
        }
        
        translate([(pi_len-piholder_fin_wide)/2, pi_wid-piholder_tall+2*piPeg_OR, 0]){
            cube([piholder_fin_wide, piholder_tall-pi_wid, piholder_thick]);
        }
    }
    intersection(){
        translate([piPeg_OR,piPeg_OR,0]){
            cube([pi_len-2*piPeg_OR,pi_wid-2*piPeg_OR,piholder_thick]);
        }
        translate([pi_len/2, -pi_wid/2, 0]){
            rotate([0,0,45]){
                regularRibs(x=sqrt(pow(pi_wid,2)+pow(pi_len,2)), y=sqrt(pow(pi_wid,2)+pow(pi_len,2)), ribDeep=piholder_thick, ribThick=5.4, ribSpace=5.4);
            }
        }
    }
}