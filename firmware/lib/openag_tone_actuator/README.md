# openag_tone_actuator

OpenAg driver for an actuator that can only be set to binary values and modulates the on signal using the arduino [`tone()`](https://www.arduino.cc/en/Reference/Tone) function.

## Caveats

> Only one tone can be generated at a time. If a tone is already playing on a different pin, the call to tone() will have no effect. If the tone is playing on the same pin, the call will set its frequency.
>
> Use of the tone() function will interfere with PWM output on pins 3 and 11 (on boards other than the Mega). [#](https://www.arduino.cc/en/Reference/Tone)

This means only one instance of tone_actuator can be run at a time. Running more than one will result in undefined behavior.
