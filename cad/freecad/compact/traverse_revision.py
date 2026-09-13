"""Nominal traverse geometry; manufacturing and commissioning remain gated."""
import json
from pathlib import Path
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[3]
SPEC = json.loads((ROOT/'cad/parameters/baseline.json').read_text())['spooler']['traverse_layout']

def end_plate_shape():
    p = SPEC
    t, w, h = p['plate_thickness_mm'], p['plate_width_mm'], p['plate_height_mm']
    stem_w, stem_h = p['plate_stem_width_mm'], p['plate_stem_height_mm']
    shape = Part.makeBox(t, stem_w, stem_h).fuse(Part.makeBox(t, w, h-stem_h, App.Vector(0,0,stem_h)))
    for y in p['rod_local_y_mm']:
        shape = shape.cut(Part.makeCylinder(4.1,t,App.Vector(0,y,p['rod_local_z_mm']),App.Vector(1,0,0)))
    for z in p['mount_local_z_mm']:
        shape = shape.cut(Part.makeCylinder(2.75,t,App.Vector(0,p['mount_local_y_mm'],z),App.Vector(1,0,0)))
    return shape.removeSplitter()

def carriage_shape():
    length = SPEC['carriage_length_mm']
    shape = Part.makeBox(length,55,8).fuse(Part.makeBox(length,6,18,App.Vector(0,0,6)))
    shape = shape.fuse(Part.makeBox(length,6,18,App.Vector(0,49,6)))
    for y in (15,40):
        shape = shape.fuse(Part.makeCylinder(7,length,App.Vector(0,y,12),App.Vector(1,0,0)))
    shape = shape.fuse(Part.makeBox(30,20,8,App.Vector((length-30)/2,17.5,6)))

    for y in (15,40):
        shape = shape.cut(Part.makeCylinder(4.2,length,App.Vector(0,y,12),App.Vector(1,0,0)))
    for x in SPEC['clamp_hole_x_mm']:
        shape = shape.cut(Part.makeCylinder(2.25,14,App.Vector(x,27.5,0)))
    return shape.removeSplitter()

def rotated_at(shape, point):
    result = shape.copy()
    result.rotate(App.Vector(),App.Vector(0,0,1),90)
    result.translate(App.Vector(*point))
    return result
