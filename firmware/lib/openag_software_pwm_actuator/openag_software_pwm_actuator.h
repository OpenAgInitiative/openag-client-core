#ifndef OPENAG_SOFTWARE_PWM_ACTUATOR
#define OPENAG_SOFTWARE_PWM_ACTUATOR

#include "Arduino.h"
#include <std_msgs/Float32.h>
#include "openag_module.h"

class SoftwarePwmActuator : public Module {
  public:
    // Constuctor
    SoftwarePwmActuator(int pin, bool is_active_low, int period);

    // Public variables
    bool has_error;
    char* error_msg;

    // Public functions
    void begin();
    void update();
    void set_cmd(std_msgs::Float32 cmd);

  private:
    int _pin;
    int _period;
    bool _is_active_low;
    float _duty_cycle;
    uint32_t _last_cycle_start;
    uint32_t _last_cmd;
    static const int _max_update_interval = 10000;
};

#endif
