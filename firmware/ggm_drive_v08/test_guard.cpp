#include "ggm_drive_guard.h"
#include <cstdio>
#include <cstdlib>

static int checks=0;
static void expect(bool value,const char* message){++checks;if(!value){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
static GgmInput good(){return GgmInput{1000,100,0,2,16,0,1,0,2500,6500,true,true,true,true,true,true};}

int main(){
  {GgmDriveGuard g;auto i=good();expect(g.update(i).shredder==100,"forward");}
  {GgmDriveGuard g;auto i=good();i.profile_verified=false;expect(g.update(i).shredder==0,"uncertified");}
  {GgmDriveGuard g;auto i=good();i.current_feedback_valid=false;expect(g.update(i).fault,"invalid current feedback");}
  {GgmDriveGuard g;auto i=good();i.motor_current_a=NAN;expect(g.update(i).fault,"nan current");}
  {GgmDriveGuard g;auto i=good();i.gearbox_nm_per_amp=0;expect(g.update(i).fault,"no torque map");}
  {GgmDriveGuard g;auto i=good();i.screw=100;expect(g.update(i).fault,"exclusive");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=-1;expect(g.update(i).fault,"no screw reverse");}
  {GgmDriveGuard g;auto i=good();i.motor_current_a=6.1f;expect(g.update(i).fault,"current ceiling");}
  {GgmDriveGuard g;auto i=good();i.gearbox_nm_per_amp=5;expect(g.update(i).fault,"torque");i=good();expect(g.update(i).shredder==0,"latched");expect(!g.clear(true,2,0,0),"clear loaded");expect(g.clear(true,0,0,0),"clear stopped");}
  {GgmDriveGuard g;auto i=good();i.shredder_rpm=22;expect(g.update(i).fault,"shredder overspeed");}
  {GgmDriveGuard g;auto i=good();i.screw_rpm=99;expect(g.update(i).shredder==100,"inactive screw rpm ignored");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=100;i.screw_rpm=20.0f;expect(g.update(i).screw==100,"screw hard limit accepted");i.screw_rpm=20.1f;expect(g.update(i).fault,"screw overspeed");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=100;i.shredder_rpm=99;expect(g.update(i).screw==100,"inactive shredder rpm ignored");}
  {GgmDriveGuard g;auto i=good();i.shredder=300;expect(g.update(i).shredder==255,"saturate");}
  {GgmDriveGuard g;auto i=good();i.shredder_tach_valid=false;expect(g.update(i).shredder==100,"shredder tach startup grace");i.now_ms=3499;expect(g.update(i).shredder==100,"shredder grace boundary");i.now_ms=3500;expect(g.update(i).fault,"shredder startup tach timeout");}
  {GgmDriveGuard g;auto i=good();expect(g.update(i).shredder==100,"tach qualified");i.now_ms=1010;i.shredder_tach_valid=false;expect(g.update(i).fault,"running shredder tach loss");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=100;i.screw_tach_valid=false;expect(g.update(i).screw==100,"screw tach startup grace");i.now_ms=7499;expect(g.update(i).screw==100,"screw grace boundary");i.now_ms=7500;expect(g.update(i).fault,"screw startup tach timeout");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=100;expect(g.update(i).screw==100,"screw tach qualified");i.now_ms=1010;i.screw_tach_valid=false;expect(g.update(i).fault,"running screw tach loss");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.current_feedback_valid=false;i.shredder_tach_valid=false;i.screw_tach_valid=false;expect(!g.update(i).fault,"idle invalid feedback does not latch");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;expect(g.update(i).shredder==0,"reverse begins coast");i.now_ms=1499;i.shredder_rpm=0;i.shredder_tach_valid=false;expect(g.update(i).shredder==0,"reverse dwell");i.now_ms=1500;expect(g.update(i).shredder==-100,"reverse released into tach grace");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;i.shredder_rpm=0;i.shredder_stopped_observed=false;g.update(i);i.now_ms=12000;i.shredder_tach_valid=false;expect(g.update(i).shredder==0,"reverse requires stationary evidence");expect(!g.faulted(),"coast silence is not tach fault");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;i.now_ms=0xffffff00UL;g.update(i);i.now_ms+=600;i.shredder_rpm=0;i.shredder_tach_valid=false;expect(g.update(i).shredder==-100,"reverse rollover");}
  for(unsigned req=0;req<16;++req)for(unsigned start=0;start<4;++start){
    unsigned mask=GgmDriveGuard::heaterMask(req,true,start),sum=0;
    for(unsigned z=0;z<4;++z)if(mask&(1U<<z))sum+=z==3?60:100;
    expect(sum<=300 && !(mask&~req),"bounded heater mask");
  }
  expect(GgmDriveGuard::heaterMask(15,false,0)==15,"full preheat");
  std::printf("PASS %d software checks; physical tests 0\n",checks);
}
