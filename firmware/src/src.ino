#include <openag_am2315.h>
#include <openag_mhz16.h>
#include <openag_ds18b20.h>
#include <openag_atlas_ph.h>
#include <openag_atlas_ec.h>
#include <openag_binary_sensor.h>

#include <openag_pwm_actuator.h>
#include <openag_binary_actuator.h>
#include <openag_pulse_actuator.h>
#include <openag_doser_pump.h>
#include <openag_tone_actuator.h>

// Sensor Instances
Am2315 am2315_1;
MHZ16 mhz16_1(77);
Ds18b20 ds18b20_1(5);
BinarySensor water_level_sensor_low_1(3, true);
BinarySensor water_level_sensor_high_1(4, true);
AtlasPh atlas_ph_1(99);
AtlasEc atlas_ec_1(100);

// Actuator Instances. Sorted by pin number.
DoserPump pump_1_nutrient_a_1(28, true);
DoserPump pump_2_nutrient_b_1(29, true);
PulseActuator pump_3_ph_up_1(30, true, 50, 4000);
PulseActuator pump_4_ph_down_1(31, true, 50, 4000);
BinaryActuator pump_5_water_1(32, true, 10000);
BinaryActuator chiller_fan_1(33, true, 10000);
BinaryActuator chiller_pump_1(34, true, 10000);
BinaryActuator heater_core_2_1(35, true, 10000);
BinaryActuator air_flush_1(36, true, 10000);
BinaryActuator water_aeration_pump_1(37, true, 10000);
BinaryActuator water_circulation_pump_1(38, true, 10000);
BinaryActuator chamber_fan_1(39, true, 10000);
PwmActuator led_blue_1(40, true, 0);
PwmActuator led_white_1(41, true, 0);
PwmActuator led_red_1(42, true, 0);
BinaryActuator heater_core_1_1(43, true, 10000);
ToneActuator chiller_compressor_1(9, false, 140, -1);

// Message string
String message = "";
bool stringComplete = false;
const int COMMAND_LENGTH = 18; // status + num_actuators

// Timing constants
uint32_t delayMs = 50; //ms
uint32_t prev_time = millis();

void split(String messages, String* splitMessages,  char delimiter=',');
void actuatorLoop();
void sensorLoop();

// #region Arduino Events
void setup() {
  Serial.begin(115200);
  while(!Serial){
    // wait for serial port to connect, needed for USB
  }
  message.reserve(200);

  // Begin sensors
  beginModule(am2315_1, "AM2315 #1");
  beginModule(mhz16_1, "MHZ16 #1");
  beginModule(ds18b20_1, "DS18B20 #1");
  beginModule(atlas_ec_1, "Atlas EC #1");
  beginModule(atlas_ph_1, "Atlas pH #1");
  beginModule(water_level_sensor_low_1, "Water Level Low sensor");
  beginModule(water_level_sensor_high_1, "Water Level High sensor");

  // Begin Actuators
  beginModule(pump_1_nutrient_a_1, "Pump 1, Nutrient A");
  beginModule(pump_2_nutrient_b_1, "Pump 2, Nutrient B");
  beginModule(pump_3_ph_up_1, "Pump 3, pH Up");
  beginModule(pump_4_ph_down_1, "Pump 4, pH Down");
  beginModule(pump_5_water_1, "Pump 5, Water");
  beginModule(chiller_fan_1, "Chiller Fan");
  beginModule(chiller_pump_1, "Chiller Pump");
  beginModule(heater_core_2_1, "Heater core #2");
  beginModule(air_flush_1, "Air Flush");
  beginModule(water_aeration_pump_1, "Water Aeration Pump");
  beginModule(water_circulation_pump_1, "Water Circulation Pump");
  beginModule(chamber_fan_1, "Chamber Circulation Fan");
  beginModule(led_blue_1, "LED Blue");
  beginModule(led_white_1, "LED White");
  beginModule(led_red_1, "LED Red");
  beginModule(heater_core_1_1, "Heater Core #1");
  beginModule(chiller_compressor_1, "Chiller Compressor #1");
}

void loop() {

  // Throttle the Arduino since the python node can't keep up
  // and the serial buffer overflows. We do this without blocking.
  if(millis() - prev_time < delayMs){
    return;
  }
  prev_time = millis();

  actuatorLoop();
  sensorLoop();
}

// Runs inbetween loop()s, just takes any input serial to a string buffer.
// Runs as realtime as possible since loop has no delay() calls. (It shouldn't!)
void serialEvent() {
  if(stringComplete){
    message = "";
    stringComplete = false;
  }
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    message += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      return;
    }
  }
}
// #endregion

void actuatorLoop(){
  // If serial message, actuate based on it.
  if(stringComplete){
    String splitMessages[COMMAND_LENGTH];
    for(int i = 0; i < COMMAND_LENGTH; i++){
      splitMessages[0] = "";
    }
    split(message, splitMessages);

    // We've already used this message
    message = "";
    stringComplete = false;
    // status, blue, white, red
    if(splitMessages[0] != "0"){
      return;
    }
    pump_1_nutrient_a_1.set_cmd(splitMessages[1].toFloat());        // DoserPump float flow_rate
    pump_2_nutrient_b_1.set_cmd(splitMessages[2].toFloat());        // DoserPump float flow_rate
    pump_3_ph_up_1.set_cmd(str2bool(splitMessages[3]));             // PulseActuator bool
    pump_4_ph_down_1.set_cmd(str2bool(splitMessages[4]));           // PulseActuator bool
    pump_5_water_1.set_cmd(str2bool(splitMessages[5]));             // BinaryActuator bool
    chiller_fan_1.set_cmd(str2bool(splitMessages[6]));              // BinaryActuator bool
    chiller_pump_1.set_cmd(str2bool(splitMessages[7]));             // BinaryActuator bool
    heater_core_2_1.set_cmd(str2bool(splitMessages[8]));            // BinaryActuator bool
    air_flush_1.set_cmd(str2bool(splitMessages[9]));                // BinaryActuator bool
    water_aeration_pump_1.set_cmd(str2bool(splitMessages[10]));     // BinaryActuator bool
    water_circulation_pump_1.set_cmd(str2bool(splitMessages[11]));  // BinaryActuator bool
    chamber_fan_1.set_cmd(str2bool(splitMessages[12]));             // BinaryActuator bool
    led_blue_1.set_cmd(splitMessages[13].toFloat());                // PwmActuator float 0-1
    led_white_1.set_cmd(splitMessages[14].toFloat());               // PwmActuator float 0-1
    led_red_1.set_cmd(splitMessages[15].toFloat());                 // PwmActuator float 0-1
    heater_core_1_1.set_cmd(str2bool(splitMessages[16]));           // BinaryActuator bool
    chiller_compressor_1.set_cmd(str2bool(splitMessages[17]));      // ToneActuator bool on/off
  }

  // Run the update loop
  bool allActuatorSuccess = true;

  allActuatorSuccess = updateModule(pump_1_nutrient_a_1, "Pump 1 Nutrient A") && allActuatorSuccess;
  allActuatorSuccess = updateModule(pump_2_nutrient_b_1, "Pump 2 Nutrient B") && allActuatorSuccess;
  allActuatorSuccess = updateModule(pump_3_ph_up_1, "Pump 3 pH Up") && allActuatorSuccess;
  allActuatorSuccess = updateModule(pump_4_ph_down_1, "Pump 4 pH Down") && allActuatorSuccess;
  allActuatorSuccess = updateModule(pump_5_water_1, "Pump 5 Water") && allActuatorSuccess;
  allActuatorSuccess = updateModule(chiller_fan_1, "Chiller Fan") && allActuatorSuccess;
  allActuatorSuccess = updateModule(chiller_pump_1, "Chiller Pump") && allActuatorSuccess;
  allActuatorSuccess = updateModule(heater_core_2_1, "Heater core #2") && allActuatorSuccess;
  allActuatorSuccess = updateModule(air_flush_1, "Air Flush") && allActuatorSuccess;
  allActuatorSuccess = updateModule(water_aeration_pump_1, "Water Aeration Pump") && allActuatorSuccess;
  allActuatorSuccess = updateModule(water_circulation_pump_1, "Water Circulation Pump") && allActuatorSuccess;
  allActuatorSuccess = updateModule(chamber_fan_1, "Chamber Circulation Fan") && allActuatorSuccess;
  allActuatorSuccess = updateModule(led_blue_1, "LED Blue") && allActuatorSuccess;
  allActuatorSuccess = updateModule(led_white_1, "LED White") && allActuatorSuccess;
  allActuatorSuccess = updateModule(led_red_1, "LED Red") && allActuatorSuccess;
  allActuatorSuccess = updateModule(heater_core_1_1, "Heater Core #1") && allActuatorSuccess;
  allActuatorSuccess = updateModule(chiller_compressor_1, "Chiller Compressor #1") && allActuatorSuccess;

  if(!allActuatorSuccess){
    return;
  }
}

void sensorLoop(){
  bool allSensorSuccess = true;

  // Run Update on all sensors
  allSensorSuccess = updateModule(am2315_1, "AM2315 #1") && allSensorSuccess;
  allSensorSuccess = updateModule(mhz16_1, "MHZ16 #1") && allSensorSuccess;
  allSensorSuccess = updateModule(ds18b20_1, "DS18B20 #1") && allSensorSuccess;
  allSensorSuccess = updateModule(atlas_ec_1, "Atlas EC #1") && allSensorSuccess;
  allSensorSuccess = updateModule(atlas_ph_1, "Atlas pH #1") && allSensorSuccess;
  allSensorSuccess = updateModule(water_level_sensor_low_1, "Water Level Low sensor") && allSensorSuccess;
  allSensorSuccess = updateModule(water_level_sensor_high_1, "Water Level High sensor") && allSensorSuccess;

  if(!allSensorSuccess){
    return;
  }

  // Prints the data in CSV format via serial.
  // Columns: status,hum,temp,co2
  Serial.print(OK);                                             Serial.print(',');
  Serial.print(am2315_1.get_air_humidity());                    Serial.print(',');
  Serial.print(am2315_1.get_air_temperature());                 Serial.print(',');
  Serial.print(mhz16_1.get_air_carbon_dioxide());               Serial.print(',');
  Serial.print(ds18b20_1.get_temperature());                    Serial.print(',');
  Serial.print(water_level_sensor_low_1.get_is_on());           Serial.print(',');
  Serial.print(water_level_sensor_high_1.get_is_on());          Serial.print(',');
  Serial.print(atlas_ph_1.get_water_potential_hydrogen());      Serial.print(',');
  Serial.print(atlas_ec_1.get_water_electrical_conductivity()); Serial.print('\n');
  // https://www.arduino.cc/en/serial/flush
  // Wait until done writing.
  Serial.flush();
}

// #region helpers
// C is disgusting and I hate it deeply...
void split(String messages, String* splitMessages,  char delimiter){
  int indexOfComma = 0;
  for(int i = 0; messages.indexOf(delimiter, indexOfComma) > 0; i++){
    int nextIndex = messages.indexOf(delimiter, indexOfComma+1);
    String nextMessage;

    // The first message doesn't have an initial comma, so account for that.
    if(indexOfComma == 0){
      indexOfComma = -1;
    }
    if(nextIndex == -1){
      nextMessage = messages.substring(indexOfComma+1);
    }else{
      nextMessage = messages.substring(indexOfComma+1, nextIndex);
    }
    splitMessages[i] = nextMessage;
    indexOfComma = nextIndex;
  }
}

bool beginModule(Module &module, String name){
  bool status = module.begin() == OK;
  if(!status){
    Serial.print(module.status_level); Serial.print(',');
    Serial.print(name);  Serial.print(',');
    Serial.print(module.status_code);  Serial.print(',');
    Serial.print(module.status_msg);   Serial.print('\n');
    Serial.flush();
  }
  return status;
}

bool updateModule(Module &module, String name){
  bool status = module.update() == OK;
  if(!status){
    Serial.print(module.status_level); Serial.print(',');
    Serial.print(name);  Serial.print(',');
    Serial.print(module.status_code);
    // Serial.print(',');
    // Serial.print(module.status_msg);
    Serial.print('\n');
    Serial.flush();
  }
  return status;
}

bool any(bool *all){
  int length = sizeof(all)/sizeof(all[0]);
  for(int i=0; i < length; i++){
    if(all[i]){
      return true;
    }
  }
  return false;
}

bool str2bool(String str){
  return (str == "True");
}
// #endregion
