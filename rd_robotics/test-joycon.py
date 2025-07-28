from pyjoycon import JoyCon, get_R_id, get_L_id
import time

# Récupération de l'ID du Joy-Con (gauche ou droit)
joycon_id = get_R_id()
if joycon_id is None:
    raise RuntimeError("Aucun Joy-Con détecté !")

# Initialisation
joycon = JoyCon(*joycon_id)


while True:
    # Lecture de son état
    status = joycon.get_status()
    """print("Batterie:", status['battery']['level'], "(niveau)",
          "Charging:" , status['battery']['charging'])
    print("Boutons appuyés:",
          {k:v for k,v in status['buttons']['right'].items() if v})
    print("Position stick droit:", status['analog-sticks']['right'])
    print("Accéléromètre:", status['accel'])
    print("Gyroscope brut:", status['gyro'])"""
    print(status)
    break
    #time.sleep(2)
