# Phython-Standard- und DesignScript-Bibliotheken laden
import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

# Die Eingaben für diesen Block werden in Form einer Liste in den IN-Variablen gespeichert.
data_list = IN[0]

# Code unterhalb dieser Linie platzieren

# Initalisierung
dynamo = True

con_overhang = data_list[0][0]
ff_overhang = data_list[0][1]
plate_t = data_list[0][2]
gap_hor = data_list[0][3]
gap_ver = data_list[0][4]
e_max = data_list[0][5]

con_gr_pl_l = 200  # Console ground plate length
con_gr_pl_w = 150  # Console ground plate width

orginPoint_list = []
xDirectionPoint_list = []
yDirectionPoint_list = []
property_list = [plate_t]

# Bereinigung #######################################

data_list.pop(0) # Lösche Grunddaten.

for floor in data_list: # None Einträge Löschen. Stockwerke ohne Fußbodeneinträge löschen.
    if None in floor or floor[3] == 0 or floor[4] == 0:
        floor.clear()
while [] in data_list:
    data_list.remove([])

for floor in data_list:
    while floor[-1] == 0:
        floor.pop()

if e_max < 300:     # Programm vor Absturz bewahren. (Zu kleine Zahl erhöht die Konsolenanzahl massiv)
    e_max = 300

# Classes #######################################
class Plate:
    def __init__(self, length, width, thickness):
        self.l = length
        self.w = width
        self.t = thickness
        Plate.set_on_point(self, 0, 0, 0, 'mP')

    def set_on_point(self, x, y, z, pos):
        if pos == 'rP':
            self.orginPoint = [x, y, z]
            self.xDirectionPoint = [x, y, -self.w + z]
            self.yDirectionPoint = [x, -self.l + y, -self.w + z]
        elif pos == 'lP':
            self.orginPoint = [x, y, z]
            self.xDirectionPoint = [x, -self.l + y, z]
            self.yDirectionPoint = [x, -self.l + y, -self.w + z]
        elif pos == 'mP':
            self.orginPoint = [self.l + x, y, z]
            self.xDirectionPoint = [x, y, z]
            self.yDirectionPoint = [x, y, -self.w + z]
        elif pos == 'gP':
            self.orginPoint = [x, self.l + y, z]
            self.xDirectionPoint = [x, y, z]
            self.yDirectionPoint = [self.w + x, y, z]

    def __repr__(self):
        try:
            return f'{self.l}x{self.w}x{self.t} \n' \
                   f'CS: {self.orginPoint}{self.xDirectionPoint}{self.yDirectionPoint}'
        except AttributeError:
            return f'Fehler!: Platte hat noch keine Position'

# Functions #######################################
def write_dynamo_points(plate):
    if dynamo:
        p1 = plate.orginPoint[0]
        p2 = plate.orginPoint[1]
        p3 = plate.orginPoint[2]
        orginPoint_list.append(Point.ByCoordinates(p1, p2, p3))

        p1 = plate.xDirectionPoint[0]
        p2 = plate.xDirectionPoint[1]
        p3 = plate.xDirectionPoint[2]
        xDirectionPoint_list.append(Point.ByCoordinates(p1, p2, p3))

        p1 = plate.yDirectionPoint[0]
        p2 = plate.yDirectionPoint[1]
        p3 = plate.yDirectionPoint[2]
        yDirectionPoint_list.append(Point.ByCoordinates(p1, p2, p3))
    else:
        orginPoint_list.append(plate.orginPoint)
        xDirectionPoint_list.append(plate.xDirectionPoint)
        yDirectionPoint_list.append(plate.yDirectionPoint)

def create_start_points(length, plate):
    div_li = []
    div = []
    starter = 0

    if length > 300:
        if plate == 'b':
            div = (length - 2 * 150) / ((length - 2 * 150) // e_max + 1)
            starter = px_factor + 150
        elif plate == 'c' or plate == 'a':
            div = (length - 150) / ((length - 150) // e_max + 1)
            starter = round(div, 2)
        div_li = [starter]  # Liste mit Startpunkten für die Konsolen.

        while div_li[-1] + div < length:
            div_li.append(round(div_li[-1] + div, 2))
    return div_li


################## Main Function ##################
floor_height = 0
for floor in data_list:

    raw_height = floor[4] - floor[3]
    plate_w = raw_height + ff_overhang + con_overhang
    len_a = floor[0] - gap_hor
    len_b = floor[1] - gap_hor * 2
    len_c = floor[2] - gap_hor
    min_l = 0
    existing = {'Plate_A': 0, 'Plate_B': 0, 'Plate_C': 0}

    if len_a > min_l:
        existing['Plate_A'] = 1
    if len_b > min_l:
        existing['Plate_B'] = 1
    if len_c > min_l:
        existing['Plate_C'] = 1

    if existing['Plate_A']: # Wenn Platte A Existiert
        # Platte A Erstellen.
        plate_a = Plate(len_a, plate_w, plate_t)
        plate_a.set_on_point(0, 0, floor_height + ff_overhang, 'lP')
        write_dynamo_points(plate_a)

        # Konsolen Erstellen.
        for start_p in create_start_points(len_a, 'a'):
            cp_h = Plate(con_gr_pl_w, con_gr_pl_l, plate_t)     # Umkehren der Platten Dimensionen um die Platte zu drehen.
            cp_h.set_on_point(- con_gr_pl_l, -(start_p + con_gr_pl_w / 2), floor_height - raw_height + gap_ver, 'gP')
            write_dynamo_points(cp_h)

            cp_v = Plate(con_gr_pl_l - 20, raw_height - 80 - gap_ver - plate_t, plate_t)
            cp_v.set_on_point(- (con_gr_pl_l - 20), -(start_p - cp_v.t / 2), floor_height - 80, 'mP')
            write_dynamo_points(cp_v)

    if existing['Plate_B']: # Wenn Platte B Existiert
        l_factor = 0
        px_factor = 0
        if existing['Plate_A'] and existing['Plate_C']:
            l_factor = plate_t * 2
            px_factor = plate_t
        elif existing['Plate_A']:
            l_factor = plate_t
            px_factor = plate_t
        elif existing['Plate_C']:
            l_factor = plate_t
        len_b -= l_factor

        # Platte B Erstellen.
        plate_b = Plate(len_b, plate_w, plate_t)
        plate_b.set_on_point(px_factor, 0, floor_height + ff_overhang, 'mP')
        write_dynamo_points(plate_b)

        # Konsolen Erstellen.
        for start_p in create_start_points(len_b, 'b'):
            cp_h = Plate(con_gr_pl_l, con_gr_pl_w, plate_t)
            cp_h.set_on_point(start_p - cp_h.w / 2, 0, floor_height - raw_height + gap_ver, 'gP')
            write_dynamo_points(cp_h)

            cp_v = Plate(cp_h.l - 20, raw_height - 80 - gap_ver - plate_t, plate_t)
            cp_v.set_on_point(start_p - plate_t / 2, cp_v.l, floor_height - 80, 'lP')
            write_dynamo_points(cp_v)

    if existing['Plate_C']: # Wenn Platte C Existiert
        px_factor = 3000 # Fiktiver Wert wenn nur die Platte C existiert.
        if existing['Plate_A'] and existing['Plate_B']:
            px_factor = plate_t * 2 + len_b
        elif existing['Plate_B']:
            px_factor = len_b + plate_t

        # Platte C Erstellen.
        plate_c = Plate(len_c, plate_w, plate_t)
        plate_c.set_on_point(px_factor, 0, floor_height + ff_overhang, 'rP')
        write_dynamo_points(plate_c)

        # Konsolen Erstellen.
        for start_p in create_start_points(len_c, 'c'):
            cp_h = Plate(con_gr_pl_w, con_gr_pl_l, plate_t)     # Umkehren der Platten Dimensionen um die Platte zu drehen.
            cp_h.set_on_point(px_factor, -(start_p + con_gr_pl_w / 2), floor_height - raw_height + gap_ver, 'gP')
            write_dynamo_points(cp_h)

            cp_v = Plate(con_gr_pl_l - 20, raw_height - 80 - gap_ver - plate_t, plate_t)
            cp_v.set_on_point(px_factor, -(start_p - cp_v.t / 2), floor_height - 80, 'mP')
            write_dynamo_points(cp_v)

    floor_height += 3000

# Weisen Sie Ihre Ausgabe der OUT-Variablen zu.

OUT = [orginPoint_list, xDirectionPoint_list, yDirectionPoint_list, property_list]
