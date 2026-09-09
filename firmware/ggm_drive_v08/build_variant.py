"""Build an isolated GGM sketch from current source, retaining source hashes."""
from pathlib import Path
import json,hashlib,shutil,re,subprocess
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SRC=ROOT/'firmware/arduino_mega'
OUT=ROOT/'exports/final/drive_ggm_v08/firmware/arduino_mega'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Ambiguous patch anchor: '+old[:80])
    return text.replace(old,new)

def main():
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'src').mkdir(exist_ok=True)
    sources=[SRC/'arduino_mega.ino']+sorted((SRC/'src').glob('*.h'))+sorted((SRC/'src').glob('*.cpp'))
    bindings={str(p.relative_to(ROOT)):sha(p) for p in sources}
    for p in sources:shutil.copy2(p,OUT/p.relative_to(SRC))
    shutil.copy2(HERE/'ggm_commissioning.h',OUT/'src/ggm_commissioning.h')
    ino=(OUT/'arduino_mega.ino').read_text()
    ino=replace_once(ino,'#include "src/board_config.h"','#include "src/board_config.h"\n#include "src/ggm_drive_guard.h"\n#include "src/ggm_commissioning.h"')
    ino=replace_once(ino,'class BoardActuators final : public ActuatorBackend {','GgmDriveGuard ggm_guard;\nclass BoardActuators final : public ActuatorBackend {')
    ino=replace_once(ino,'  void begin() {\n    TCCR5A','  void begin() {\n    pinMode(4, OUTPUT); digitalWrite(4, LOW);\n    TCCR5A')
    begin='''  void apply(const ActuatorCommands &c) {
    const bool verified=GgmCommissioning::RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED;
    const bool sh=c.shredder_pwm!=0;
    const float amps=calibration_record.current_amps_per_count>0 ?
        (sh ? abs(analogRead(Board::CURRENT_PIN)-calibration_record.current_zero_adc)*calibration_record.current_amps_per_count : (GgmCommissioning::EX_CURRENT_AMPS_PER_COUNT>0 ? fabsf(analogRead(A9)-GgmCommissioning::EX_CURRENT_ZERO_ADC)*GgmCommissioning::EX_CURRENT_AMPS_PER_COUNT : NAN)) : NAN;
'''
    begin+='''    const GgmInput gi{millis(),last_tach_sample_ms,c.shredder_pwm,c.screw_pwm,
      amps,shredder_rpm,screw_rpm,
      sh?GgmCommissioning::SH_GEARBOX_NM_PER_AMP:GgmCommissioning::EX_GEARBOX_NM_PER_AMP,
      sh?GgmCommissioning::SH_NO_LOAD_CURRENT_A:GgmCommissioning::EX_NO_LOAD_CURRENT_A,
      verified,digitalRead(Board::ESTOP_PIN)==HIGH && digitalRead(Board::SERVICE_GUARD_PIN)==HIGH &&
      digitalRead(Board::LID_PIN)==HIGH && digitalRead(Board::THERMAL_CHAIN_PIN)==HIGH,
      calibrationDomainReady(calibration_record,CAL_CURRENT_SENSOR),
      calibrationDomainReady(calibration_record,CAL_SHREDDER_TACH) && shredder_tach_sample.accepted_pulses>=2 &&
      calibration_record.records[CAL_SHREDDER_TACH].value>0 &&
      float(shredder_tach_sample.pulse_age_us)>=60000000.0f/calibration_record.records[CAL_SHREDDER_TACH].value};
    const GgmOutput safe=ggm_guard.update(gi);
    writeBts(Board::SHREDDER_PWM_PIN,4,Board::SHREDDER_ENABLE_PIN,safe.shredder);
    digitalWrite(Board::SHREDDER_ENABLE_PIN,safe.shredder!=0 ? HIGH:LOW);
'''
    old='''  void apply(const ActuatorCommands &c) override {
    setMotor(Board::SHREDDER_PWM_PIN, Board::SHREDDER_DIR_PIN, Board::SHREDDER_ENABLE_PIN, c.shredder_pwm);
    digitalWrite(Board::SHREDDER_REVERSE_PIN, c.shredder_pwm < 0 ? HIGH : LOW);
'''
    ino=replace_once(ino,old,begin)
    ino=replace_once(ino,'const uint16_t requested_hz = c.feeder_enable ? c.feeder_step_hz : 0;','const uint16_t requested_hz = c.feeder_enable && verified && !safe.fault && safe.screw>0 ? c.feeder_step_hz : 0;')
    ino=replace_once(ino,'setMotor(Board::SCREW_PWM_PIN, Board::SCREW_DIR_PIN, Board::SCREW_ENABLE_PIN, c.screw_pwm);','writeBts(Board::SCREW_PWM_PIN,Board::SCREW_DIR_PIN,Board::SCREW_ENABLE_PIN,safe.screw);\n    digitalWrite(Board::SCREW_ENABLE_PIN,safe.screw!=0 ? HIGH:LOW);')
    old='for (uint8_t zone = 0; zone < 4; ++zone) digitalWrite(Board::HEATER_PINS[zone], c.heater_on[zone] ? HIGH : LOW);'
    new='''uint8_t request=0;
    for(uint8_t z=0;z<4;++z) if(c.heater_on[z]) request|=1U<<z;
    const uint8_t mask=verified && !safe.fault && gi.safety_ok ? GgmDriveGuard::heaterMask(request,c.shredder_pwm || c.screw_pwm,(millis()/250)%4):0;
    for(uint8_t z=0;z<4;++z) digitalWrite(Board::HEATER_PINS[z],(mask&(1U<<z))?HIGH:LOW);'''
    ino=replace_once(ino,old,new)
    helper='''  static void writeBts(uint8_t right_pwm,uint8_t left_pwm,uint8_t enable,int16_t value) {
    digitalWrite(enable,LOW); analogWrite(right_pwm,0); analogWrite(left_pwm,0);
    const int32_t magnitude=value<0?-int32_t(value):int32_t(value);
    if(value) {
      analogWrite(value>0?right_pwm:left_pwm,uint8_t(magnitude>255?255:magnitude));
      digitalWrite(enable,HIGH);
    }
  }
'''
    ino=replace_once(ino,'  static void setMotor(',helper+'  static void setMotor(')
    ino=ino.replace('verified && !safe.fault && gi.safety_ok ?','verified && !safe.fault && gi.safety_ok && !c.shredder_pwm ?')
    ino=replace_once(ino,'bool allDriversHealthy() {','bool allDriversHealthy() {\n  if (!GgmCommissioning::RECEIPT_LIMITER_CURRENT_AND_WIRING_VERIFIED || ggm_guard.faulted()) return false;')
    ino=ino.replace('parallel-actuation-hardening-v0.6.2','ggm-drive-v08-r1')
    (OUT/'arduino_mega.ino').write_text(ino)
    calibration=OUT/'src/calibration_record.h';ct=calibration.read_text()
    ct=replace_once(ct,'CALIBRATION_RECORD_MAGIC = 0x50505236UL','CALIBRATION_RECORD_MAGIC = 0x47474D31UL')
    calibration.write_text(ct)

    board=OUT/'src/board_config.h';bt=board.read_text()
    bt=replace_once(bt,'{SHREDDER_FAULT_PIN, SCREW_FAULT_PIN, PULLER_FAULT_PIN, SPOOLER_FAULT_PIN, FEEDER_FAULT_PIN}','{PULLER_FAULT_PIN, SPOOLER_FAULT_PIN, FEEDER_FAULT_PIN}')
    board.write_text(bt)

    p=OUT/'src/generated_profiles.h';text=p.read_text()
    text=replace_once(text,'MaterialProfile::PLA, 32, 11.0f, 18.0f','MaterialProfile::PLA, 16, 11.0f, 17.0f')
    text=replace_once(text,'MaterialProfile::PET, 24, 13.0f, 18.0f','MaterialProfile::PET, 16, 13.0f, 17.0f')
    text=replace_once(text,'INPUT_MECHANICAL_FUSE_NM = 22.0f','INPUT_MECHANICAL_FUSE_NM = 19.7625f')
    text=replace_once(text,'JAM_STOP_MS = 250','JAM_STOP_MS = 4000')
    text=replace_once(text,'JAM_CURRENT_SENSOR_SATURATION_A = 6.4f','JAM_CURRENT_SENSOR_SATURATION_A = 6.0f')
    text=text.replace('0.75f, 1.316f,','0.0f, 0.0f,').replace('8.2f, 20.0f,','4.6f, 6.0f,').replace('95.0f, 80.0f, false','18.6667f, 80.0f, false')
    text=text.replace('650, 800, 3','650, 1500, 3').replace('850, 1100, 3','850, 1500, 3')
    text='// GGM variant from declared live-source snapshot; not original generated-profile evidence.\n'+text
    p.write_text(text)
    if any(sha(ROOT/p)!=h for p,h in bindings.items()):raise RuntimeError('Source changed during build')
    manifest={'profile':'GGM-DRIVE-v0.8-r1','source_sha256':bindings,'builder_sha256':sha(Path(__file__)),
      'commissioning_header_sha256':sha(HERE/'ggm_commissioning.h'),'physical_validation':'NOT_RUN','hardware_enabled':False,
      'source_payload':{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}}
    (OUT.parent/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('GGM_FIRMWARE_SOURCE_READY',len(manifest['source_payload']))
if __name__=='__main__':main()
