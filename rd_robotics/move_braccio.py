import serial, time, copy
from tkinter import *

class Position:
    def __init__(self, base, shoulder, elbow, wrist, wrist_rotation, gripper):
        self.angels = [base, shoulder, elbow, wrist, wrist_rotation, gripper]
    def to_string(self):
        return ",".join(str(a) for a in self.angels)

class Braccio:
    def __init__(self, serial_port):
        self.port = serial.Serial(serial_port, 115200, timeout=5)
        time.sleep(3)
    def write(self, cmd):
        self.port.write(cmd.encode()); self.port.readline()
    def move_to_position(self, pos, speed):
        self.write('P' + pos.to_string() + ',' + str(speed) + '\n')

# … définitions de l’interface tkinter et de la gestion clavier …

port = "/dev/tty.usbserial-A600euch"
robot = Braccio(port)
home = Position(0,90,90,90,90,72)
robot.move_to_position(home, 100)
# lancez ensuite l’interface graphique pour piloter en direct
