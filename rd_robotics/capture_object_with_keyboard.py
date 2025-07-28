import serial
import time
from tkinter import *

# --- Classes fournies ---
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
        self.port.write(cmd.encode())
        self.port.readline()
    def move_to_position(self, pos, speed):
        self.write('P' + pos.to_string() + ',' + str(speed) + '\n')

# --- Configuration du port et position Home ---
PORT = "/dev/tty.usbserial-A600euch"
robot = Braccio(PORT)
home_position = Position(0, 90, 90, 90, 90, 72)
robot.move_to_position(home_position, 100)

# --- Application Tkinter ---
class App:
    def __init__(self, master, robot):
        self.master = master
        self.robot = robot
        master.title("Contrôle Braccio")

        # Définition des limites pour chaque axe
        labels = ['Base (←/→)', 'Épaule (↑/↓)', 'Coude (E/D)', 'Poignet (R/F)', 'Rotation Poignet (T/G)', 'Pince (Y/H)']
        defaults = [0, 90, 90, 90, 90, 72]
        limits = [
            (0, 180),   # Base
            (15, 165),  # Épaule
            (0, 180),   # Coude
            (0, 180),   # Poignet
            (0, 180),   # Rotation Poignet
            (0, 73)     # Pince
        ]

        # Création des curseurs
        self.scales = []
        for i, (lbl, dft, (mn, mx)) in enumerate(zip(labels, defaults, limits)):
            frame = Frame(master)
            frame.pack(padx=5, pady=3, fill='x')
            Label(frame, text=lbl).pack(side='left')
            scale = Scale(frame, from_=mn, to=mx, orient='horizontal')
            scale.set(dft)
            scale.pack(side='right', expand=True, fill='x')
            self.scales.append(scale)

        # Curseur de vitesse
        frame_speed = Frame(master)
        frame_speed.pack(padx=5, pady=5, fill='x')
        Label(frame_speed, text='Vitesse').pack(side='left')
        self.speed_scale = Scale(frame_speed, from_=1, to=255, orient='horizontal')
        self.speed_scale.set(100)
        self.speed_scale.pack(side='right', expand=True, fill='x')

        # Boutons
        btn_frame = Frame(master)
        btn_frame.pack(pady=10)
        Button(btn_frame, text='Move', command=self.move).pack(side='left', padx=5)
        Button(btn_frame, text='Home', command=self.go_home).pack(side='left', padx=5)
        Button(btn_frame, text='Exit', command=master.quit).pack(side='left', padx=5)

        # Raccourcis clavier
        binds = [
            ('<Left>', 0, -5), ('<Right>', 0, 5),
            ('<Down>', 1, -5), ('<Up>', 1, 5),
            ('e',     2, 5), ('d',     2, -5),
            ('r',     3, 5), ('f',     3, -5),
            ('t',     4, 5), ('g',     4, -5),
            ('y',     5, 5), ('h',     5, -5)
        ]
        for key, idx, delta in binds:
            master.bind(key, lambda e, i=idx, d=delta: self.adjust_scale(i, d))

    def get_position(self):
        vals = [s.get() for s in self.scales]
        return Position(*vals)

    def move(self):
        pos = self.get_position()
        speed = self.speed_scale.get()
        self.robot.move_to_position(pos, speed)

    def go_home(self):
        for s, val in zip(self.scales, home_position.angels):
            s.set(val)
        self.speed_scale.set(100)
        self.move()

    def adjust_scale(self, idx, delta):
        s = self.scales[idx]
        new_val = max(s['from'], min(s['to'], s.get() + delta))
        s.set(new_val)
        self.move()

# --- Démarrage de l'application ---
if __name__ == '__main__':
    root = Tk()
    app = App(root, robot)
    root.mainloop()