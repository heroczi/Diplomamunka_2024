import gpiozero as GPIO
import time

MotorDir = [
    1,
    -1,
]


class DRV8825():
    def __init__(self, dir_pin, step_pin, enable_pin):

        self.dir_pin = dir_pin
        self.enable_pin = enable_pin
        self.step_pin = step_pin
        
        self.dir = GPIO.LED(self.dir_pin)
        self.step = GPIO.LED(self.step_pin)        
        self.enable = GPIO.LED(self.enable_pin)

        self.control_pin = {
            dir_pin: self.dir,
            enable_pin: self.enable,
            step_pin: self.step,
        }
        
    def digital_write(self, pin, value):
        if value:
          self.control_pin[pin].on()
        else:
          self.control_pin[pin].off()
          
        #GPIO.output(pin, value)
        
    def Stop(self):
        self.digital_write(self.enable_pin, 0)
        

    def TurnStep(self, Dir, steps, stepdelay=0.005):
        if (Dir == MotorDir[0]):

            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 0)
        elif (Dir == MotorDir[1]):

            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 1)
        else:
            print("the dir must be : '1' or '-1'")
            self.digital_write(self.enable_pin, 0)
            return

        if (steps == 0):
            return
            
        #print("turn step:",steps)
        for i in range(steps):
            self.digital_write(self.step_pin, True)
            time.sleep(stepdelay)
            self.digital_write(self.step_pin, False)
            time.sleep(stepdelay)
