import gpiozero as GPIO
from DRV8825 import DRV8825

def main():
    Motor1 = DRV8825(dir_pin=13, step_pin=19, enable_pin=12)
    Motor2 = DRV8825(dir_pin=24, step_pin=18, enable_pin=4)

    weapon = GPIO.LED(3)
    weapon.off()
    laser = GPIO.LED(21)
    laser.off()

    #vegallas1_VCC = PIN17
    vegallas1_GND = GPIO.LED(22)
    vegallas1_GND.off()
    vegallas1_SIG = GPIO.Button(27, pull_up = False)

    vegallas2_VCC = GPIO.LED(11)
    vegallas2_VCC.on()
    #vegallas2_GND = PIN25
    vegallas2_SIG = GPIO.Button(0, pull_up = False)

    while not vegallas1_SIG.is_pressed:
        Motor1.TurnStep(1, 1, 0.0005)

    while not vegallas2_SIG.is_pressed:
        Motor2.TurnStep(1, 1, 0.0005)


if __name__ == "__main__":
    main()
