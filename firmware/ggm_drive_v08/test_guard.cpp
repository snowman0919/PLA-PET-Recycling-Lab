#include "ggm_drive_guard.h"
#include <cstdio>
#include <cstdlib>
static int checks=0;
static void expect(bool value,const char* message){++checks;if(!value){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
static GgmInput good(){return GgmInput{1000,1000,100,0,2,16,0,1,0,true,true,true,true};}
int main(){
  {GgmDriveGuard g;auto i=good();expect(g.update(i).shredder==100,"forward");}
  {GgmDriveGuard g;auto i=good();i.profile_verified=false;expect(g.update(i).shredder==0,"uncertified");}
  {GgmDriveGuard g;auto i=good();i.feedback_ms=0;expect(g.update(i).shredder==0,"stale");}
  {GgmDriveGuard g;auto i=good();i.feedback_valid=false;expect(g.update(i).shredder==0,"invalid");}
  {GgmDriveGuard g;auto i=good();i.motor_current_a=NAN;expect(g.update(i).shredder==0,"nan");}
  {GgmDriveGuard g;auto i=good();i.gearbox_nm_per_amp=0;expect(g.update(i).shredder==0,"no map");}
  {GgmDriveGuard g;auto i=good();i.screw=100;expect(g.update(i).fault,"exclusive");}
  {GgmDriveGuard g;auto i=good();i.shredder=0;i.screw=-1;expect(g.update(i).fault,"no screw reverse");}
  {GgmDriveGuard g;auto i=good();i.motor_current_a=6.1f;expect(g.update(i).fault,"current");}
  {GgmDriveGuard g;auto i=good();i.gearbox_nm_per_amp=5;expect(g.update(i).fault,"torque");i=good();expect(g.update(i).shredder==0,"latched");expect(!g.clear(true,2,0,0),"clear loaded");expect(g.clear(true,0,0,0),"clear stopped");}
  {GgmDriveGuard g;auto i=good();i.shredder_rpm=22;expect(g.update(i).fault,"overspeed");}
  {GgmDriveGuard g;auto i=good();i.shredder=300;expect(g.update(i).shredder==255,"saturate");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;expect(g.update(i).shredder==0,"reverse begins coast");i.now_ms=1499;i.feedback_ms=1499;i.shredder_rpm=0;expect(g.update(i).shredder==0,"reverse dwell");i.now_ms=1500;i.feedback_ms=1500;expect(g.update(i).shredder==-100,"reverse released");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;i.now_ms=0xffffff00UL;i.feedback_ms=i.now_ms;g.update(i);i.now_ms+=600;i.feedback_ms=i.now_ms;i.shredder_rpm=0;expect(g.update(i).shredder==-100,"rollover");}
  {GgmDriveGuard g;auto i=good();i.shredder=-100;i.shredder_rpm=0;i.stopped_observed=false;g.update(i);i.now_ms=1700;i.feedback_ms=1700;expect(g.update(i).shredder==0,"missing stationary evidence");}
  for(unsigned req=0;req<16;++req)for(unsigned start=0;start<4;++start){
    unsigned mask=GgmDriveGuard::heaterMask(req,true,start),sum=0;
    for(unsigned z=0;z<4;++z)if(mask&(1U<<z))sum+=z==3?60:100;
    expect(sum<=300 && !(mask&~req),"bounded heater mask");
  }
  expect(GgmDriveGuard::heaterMask(15,false,0)==15,"full preheat");
  std::printf("PASS %d software checks; physical tests 0\n",checks);
}
