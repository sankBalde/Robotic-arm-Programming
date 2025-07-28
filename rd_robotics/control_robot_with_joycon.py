# -*- coding: utf-8 -*-
"""
Braccio control with Joy-Con and integrated analytical IK solver
Enhanced with Home functionality and on-app Joy-Con movement documentation.
Integrated compensation for radial extension and backlash.
"""
import os
import serial
import time
import pygame
import numpy as np
from math import sqrt, atan2, degrees, acos, asin, sin
from pyjoycon import JoyCon, get_R_id
from tkinter import *

# --- Geometry and IK solver parameters ---
l0 = 71.5   # base height offset
l1 = 125.0  # shoulder link length
l2 = 125.0  # elbow link length
l3 = 60.0 + 132.0  # forearm + wrist link length
COMP_FACTOR = 1.02   # radial compensation factor (2%)
Z_OFFSET = 15        # backlash compensation in Z (mm)
PREV_ANGLE_FILE = "prev_teta.txt"

# --- Helper to clamp values to range ---
def clamp(val, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, val))

# --- Read previous angles with fallback ---
def get_previous_teta2():
    default = [0, 90, 90, 90, 90, 72]
    if not os.path.isfile(PREV_ANGLE_FILE):
        try:
            with open(PREV_ANGLE_FILE, "w") as f:
                f.write(";".join(str(a) for a in default) + ";")
        except OSError:
            pass
        return default

    try:
        with open(PREV_ANGLE_FILE, "r") as f:
            data = f.read().strip().split(";")
        angles = [int(v) for v in data if v]
        if len(angles) >= 6:
            return angles[:6]
    except (ValueError, OSError):
        pass
    return default

# --- Backlash compensation for base rotation ---
def backlash_compensation_base(theta_base):
    theta = round(theta_base)
    prev_theta = get_previous_teta2()[0]
    delta = theta - prev_theta

    if delta > 1 and theta > 45:
        idx = min(max(theta - 46, 0), 134)
        comp_values = np.linspace(0, 14, 135)
        theta += round(comp_values[idx])
    elif delta < -1:
        theta -= 8

    return theta

# --- IK solver functions ---
def move_to_position_cart(x, y, z):
    # apply backlash in Z and radial compensation
    z_eff = z + Z_OFFSET
    r_hor = sqrt(x**2 + y**2)
    r = sqrt(r_hor**2 + (z_eff - l0)**2) * COMP_FACTOR

    # base angle
    if y == 0:
        theta_base = 180 if x <= 0 else 0
    else:
        theta_base = degrees(atan2(x, y))
    theta_base = backlash_compensation_base(theta_base)

    # shoulder & elbow
    alpha1 = acos(clamp((r - l2) / (l1 + l3)))
    theta_shoulder = degrees(alpha1)
    alpha3 = asin(clamp((sin(alpha1)*l3 - sin(alpha1)*l1) / l2))
    theta_elbow = (90 - degrees(alpha1)) + degrees(alpha3)
    theta_wrist = (90 - degrees(alpha1)) - degrees(alpha3)

    # wrist non-negative fallback
    if theta_wrist <= 0:
        # safe clamp for asin argument
        arg = clamp((l3 - l1) / r)
        theta_shoulder = degrees(alpha1 + asin(arg))
        theta_elbow = 90 - degrees(alpha1)
        theta_wrist = 90 - degrees(alpha1)

    # height adjustment
    if z_eff != l0 + Z_OFFSET:
        theta_shoulder += degrees(atan2((z_eff - l0), r))

    # servo alignment compensation
    theta_elbow += 5
    theta_wrist += 5

    return [round(theta_base), round(theta_shoulder), round(theta_elbow), round(theta_wrist)]

# --- Braccio serial interface ---
class Position:
    def __init__(self, base, shoulder, elbow, wrist, wrist_rotation, gripper):
        self.angles = [base, shoulder, elbow, wrist, wrist_rotation, gripper]
    def to_string(self):
        return ",".join(str(a) for a in self.angles)

class Braccio:
    def __init__(self, serial_port):
        self.port = serial.Serial(serial_port, 115200, timeout=5)
        time.sleep(3)
    def write(self, cmd):
        self.port.write(cmd.encode())
        self.port.readline()
    def move_to_position(self, pos, speed):
        cmd = f"P{pos.to_string()},{speed}\n"
        self.write(cmd)

# --- Application Tkinter + Joy-Con + IK ---
class App:
    POLL_INTERVAL = 50
    STICK_SCALE = 100.0
    BUTTON_SPEED = 10

    def __init__(self, master, robot):
        self.master = master
        self.robot = robot
        master.title("Braccio IK Control with Joy-Con")
        pygame.init()
        joy_id = get_R_id()
        if joy_id is None:
            raise RuntimeError("No right Joy-Con detected")
        self.joy = JoyCon(*joy_id)

        self.x, self.y, self.z = 0.0, 0.0, l0
        labels = ['Base','Épaule','Coude','Poignet','Rot.Poignet','Pince']
        defaults = get_previous_teta2()
        limits = [(0,180),(15,165),(0,180),(0,180),(0,180),(0,73)]
        self.scales = []
        for lbl, dft, (mn,mx) in zip(labels, defaults, limits):
            frm = Frame(master); frm.pack(padx=5,pady=2,fill='x')
            Label(frm, text=lbl).pack(side='left')
            sc = Scale(frm, from_=mn, to=mx, orient='horizontal')
            sc.set(dft); sc.pack(side='right', expand=True, fill='x')
            self.scales.append(sc)

        frm_sp = Frame(master); frm_sp.pack(padx=5,pady=5,fill='x')
        Label(frm_sp, text='Vitesse').pack(side='left')
        self.speed_sc = Scale(frm_sp, from_=1, to=255, orient='horizontal')
        self.speed_sc.set(100); self.speed_sc.pack(side='right', expand=True, fill='x')

        btnf = Frame(master); btnf.pack(pady=8)
        Button(btnf, text='Home',    command=self.go_home).pack(side='left', padx=5)
        Button(btnf, text='Help',    command=self.show_help).pack(side='left', padx=5)
        Button(btnf, text='Exit',    command=master.quit).pack(side='left', padx=5)

        self.last_time = time.time()
        self.poll_joycon()

    def poll_joycon(self):
        now = time.time(); dt = now - self.last_time; self.last_time = now
        st = self.joy.get_status()
        raw = st['analog-sticks']['right']
        ax = (raw['horizontal'] - 2048) / 2048.0; ay = -(raw['vertical'] - 2048) / 2048.0
        self.x += ay * self.STICK_SCALE * dt
        self.y += ax * self.STICK_SCALE * dt
        btns = st['buttons']['right']
        if btns.get('stick_button', 0): self.z = max(0.0, self.z - self.BUTTON_SPEED)
        if btns.get('zr', 0):           self.z += self.BUTTON_SPEED
        b, s, e, w = move_to_position_cart(self.x, self.y, self.z)
        for sc, val in zip(self.scales, [b, s, e, w, 90, self.scales[5].get()]): sc.set(val)
        pos = Position(b, s, e, w, 90, self.scales[5].get())
        self.robot.move_to_position(pos, self.speed_sc.get())
        self.master.after(self.POLL_INTERVAL, self.poll_joycon)

    def go_home(self):
        self.x, self.y, self.z = 0.0, 0.0, l0
        b, s, e, w = move_to_position_cart(0, 0, l0)
        home = Position(b, s, e, w, 90, 72)
        for sc, val in zip(self.scales, home.angles): sc.set(val)
        self.robot.move_to_position(home, 100)

    def show_help(self):
        win = Toplevel(self.master); win.title("Aide Joy-Con")
        t = Text(win, wrap='word', width=50, height=10)
        doc = (
            "Joystick ↑ : Avancer (X+)\n"
            "Joystick ↓ : Reculer (X−)\n"
            "Joystick ← : Strafing gauche (Y−)\n"
            "Joystick → : Strafing droite (Y+)\n"
            "Joystick ● (press): Descendre (Z−)\n"
            "Bouton ZR : Monter (Z+)\n"
            "Home : Retour à la position de départ\n"
        )
        t.insert('1.0', doc); t.config(state='disabled'); t.pack(padx=10, pady=10)

# --- Main ---
if __name__ == '__main__':
    PORT = "/dev/tty.usbserial-A600euch"
    robot = Braccio(PORT)
    b, s, e, w = move_to_position_cart(0, 0, l0)
    robot.move_to_position(Position(b, s, e, w, 90, 72), 100)
    root = Tk()
    App(root, robot)
    root.mainloop()
