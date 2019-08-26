// Z axis is optical axis.

tol = 0.2;
fn=100;
wall_thickness = 2.5;

camHolder_squareSide = 42.2;
camHolder_tall = 7.5;

plateHolder_tall = 5.0;
plateHolder_R_tol = 1.0;
plateHolder_Rthick = 1.5;
plateHolder_lip = 1.5;

lightBox_side = 111.0;
light_height = 25.0;
lightBox_shellThick = wall_thickness;
lightBox_cutthrough = 70.0;
lightFilter_thick = 10.0;
lightFilter_side = lightBox_cutthrough+5.0;
lightBox_height = light_height+lightFilter_thick+lightBox_shellThick;
lightBox_cordHoleD = 15.0;
lightBox_cordHole_edgeOffset = 20.0;

mast_offset = (lightFilter_side/2)+wall_thickness;
mast_length = 10.0;
mast_width = 5.0;
mast_tall = 150;

mastGrips_thick = 5.0;
mastGrips_tall = 10.0;

piCamB2_side = 32.35;
piCamB2_tall = 2.0;
piCamB2_ledge = 5.0;
piCamB2cable_wide = 17.0;
piCamB2cable_deep = 11.0;



ribDeep = 0.4;
ribThick=1;
ribSpace=2;

piPeg_len = 10.0;
piPeg_OR = 3.0;
piPeg_IR = 1.4;
pi_len = 49.0;
pi_wid = 58.0;
piholder_thick = wall_thickness;
piholder_tall = 85.0;
piholder_fin_wide = 36.0;


module tripleMastGrip(mast_length=mast_length, mast_width=mast_width, mastGrips_thick=mastGrips_thick, arm_tall=plateHolder_tall, mastGrips_tall=mastGrips_tall, mast_offset=mast_offset, tol=tol, arms=true){
    mastGrip(mast_length, mast_width, mastGrips_thick, arm_tall, mastGrips_tall, mast_offset, tol, 0, arms);
    mastGrip(mast_length, mast_width, mastGrips_thick, arm_tall, mastGrips_tall, mast_offset, tol, 90, arms);
    mastGrip(mast_length, mast_width, mastGrips_thick, arm_tall, mastGrips_tall, mast_offset, tol, -90, arms);
}

module regularRibs(x=1, y=1, ribDeep=ribDeep, ribThick=ribThick, ribSpace=ribSpace){
    adjusted_space =(x-ribThick)/floor((x-ribThick)/(ribSpace+ribThick))-ribThick;
    for (p = [ribThick:adjusted_space+ribThick:x]){
        translate([p,0,0]){
            cube([adjusted_space, y, ribDeep]);
        }
    }
}

module XYcenteredCube(x=0,y=0,z=0){
    translate([-x/2,-y/2,0]){
        cube([x,y,z]);
    }  
}

module XYcenteredRoundedCube(x=0,y=0,z=0,r=1,fn=fn){
    translate([-x/2,-y/2,0]){
        roundedCube(x,y,z,r,fn);
    }  
}


module XYcenteredCylinder(d=0,z=0){
    translate([-d/2,-d/2,0]){
        cylinder(d=d,z);
    }  
}

module mastGrip(m_len, m_wid, g_thik, g_tall, gm_tall, off, tol, rot, arm=true){
    grip_len = m_len+(2*(g_thik));
    grip_wid = m_wid+g_thik;
    r=wall_thickness;
    rotate([0,0,rot]){
        difference(){
            union(){
                r = min(wall_thickness, mastGrips_thick);
                //main arm
                if(arm){
                    translate([-grip_len/2, 0, 0]){
                        roundedCube(grip_len, off+grip_wid, g_tall, r, fn);
                    }
                }
                //grip
                translate([-grip_len/2, off-g_thik, 0]){
                    roundedCube(grip_len, m_wid+(g_thik*2), gm_tall, r, fn);
                }
            }
            //cut
            translate([-(m_len+tol)/2, off-(tol/2),0]){
                outflangedCube(m_len+tol, m_wid+tol, gm_tall, r/1.5, fn);
            }
        }
    }
}

module tripleMastHoleToCut(m_len=mast_length, m_wid=mast_width, gm_tall=mastGrips_tall, off=mast_offset, tol=tol, yRot=180, r=wall_thickness){
    for(rot=[-90,0,90]){
        rotate([0,yRot,rot]){
            translate([-(m_len+tol)/2, off+tol, -tol/2]){
                
                outflangedCube(m_len+tol, m_wid+tol, gm_tall+tol, r=r, fn=fn);
            }
        }
    }
}

module lightBoxPegs(s=lightBox_shellThick, p=lightBox_side, up=1){
    for(rot=[0, 90, 180, 270]){
        rotate([0, 0, rot]){
            translate([-p/2, -p/2, -s*up]){
                cube([s, s, s]);
            }
        }
    }
}

module roundedCube(l, w, h, r, fn=fn){
    hull(){
        for(x=[0+r,l-r], y=[0+r,w-r], z=[0+r,h-r]){
            translate([x, y, z]){
                sphere(r=r, $fn=fn);
            }
        }
    }
}

module fourCylinderCube(l, w, h, r, fn=fn){
    hull(){
        for(x=[0+r,l-r], y=[0+r,w-r], z=0){
            translate([x, y, z]){
                cylinder(h=h, r=r, $fn=fn);
            }
        }
    }
}

module outflangedCube(l, w, h, r, fn){
    union(){
                    color("blue")
        cube([l,w,h]);
                    color("red")
        hull(){
            for(x=[0,l], y=[0,w]){
                translate([x,y,0]){
                    cylinder(h=r, r1=r, r2=0, $fn=fn);
                }
            }
        }
    }
}

module square_with_pulled_out_corners(side, h, r, fn=fn){
    _side = sqrt(2)*(side/2+r);
    difference(){
        XYcenteredCube(_side/sqrt(2),_side/sqrt(2),h);
        rotate([0,0,45]){
            for(x=[-_side/2,_side/2], y=[-_side/2,_side/2], z=0){
                translate([x, y, z]){
                    very_fine_cylinder(h=h, r=r,f=1, $fn=fn);
                }
            }
        }        
    }
}            
            

module very_fine_cylinder(h, r, f, fn=100){
    c = PI*2*r;
    n = ceil((c/fn)/f);
    a = (360/fn)/n;
    hull(){
        for(i=[0:a:(360/fn)-a]){
           rotate([0,0,i])
           cylinder(h=h, r=r, $fn=fn);  
        }
    }
}    


            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            