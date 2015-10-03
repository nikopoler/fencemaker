import bpy
from bpy.props import *

bl_info = {
    "name": "FG Fencemaker",
    "author": "Vadym Kukhtin",
    "version": (1, 0),
    "blender": (2, 7, 2),
    "location": "",
    "description": "Make geolocated and well-heighted fence-like object with UFO's export",
    "warning": "",
    "wiki_url": ""\
        "",
    "tracker_url": ""\
        "",
    "category": "Object"}

# variables
bpy.types.Scene.exportpath = StringProperty(name="UFO's export file",
    attr="exportpath",
    description="file path to UFO's export",
    maxlen= 1024,
    default= "select file -->",
    subtype='FILE_NAME')

bpy.types.Scene.polefence = EnumProperty(name="polefence", items=[('fence',"Fence","fence"),('pole', "Pole", "pole")])
bpy.types.Scene.doShear   = bpy.props.BoolProperty(name="Shear fence", description="Shear the fences")
bpy.types.Scene.doRNDrot  = bpy.props.BoolProperty(name="Random rotate", description="Random rotate the poles")

def BuildFence(pathxml, obj):

    import bpy
    import os
    import mathutils as M
    import mathutils as Vector
    import math
    import random
    import xml.etree.ElementTree as ET
    
    def CopyObject (obj, nam):
        obj = random.choice (obj)
        mesh = bpy.data.meshes.new(nam)
        obj_new = bpy.data.objects.new(nam, mesh)
        obj_new.data = obj.data.copy()
        obj_new.scale = obj.scale
        scene.objects.link(obj_new)
        obj_new.layers = (True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
        return obj_new
    
    def MakeHorizontalFence (pits):
        x, y, z = 0, 0, 0
        for wpt in pits:
            nam = wpt.find("name").text
            lenght = float(wpt.find("lenght").text)
            dx = float(wpt.find("dx").text)
            dy = float(wpt.find("dy").text)
            alt = float(wpt.find("alt").text)
            z = alt - alt0
            course = float(wpt.find("course").text)
            
            obj_new = CopyObject (obj,nam)

            x -= dy
            y += dx

            ScaleMatrix = M.Matrix.Scale(lenght/modelLenght, 4, M.Vector((1, 0, 0)))
            RotationMatrix = M.Matrix.Rotation(-course, 4, "Z")
            TranslationMatrix = M.Matrix.Translation(M.Vector((x, y, z)))
    
            obj_new.data.transform(ScaleMatrix)
            obj_new.data.transform(RotationMatrix)
            obj_new.data.transform(TranslationMatrix)

    def MakeShearedFence (pits):
        x, y, z = 0, 0, 0
        for wpt, wpt_nxt in zip (pits[:-1], pits[1:]):
            nam = wpt.find("name").text
            dx = float(wpt.find("dx").text)
            dy = float(wpt.find("dy").text)
            lenght = math.sqrt(dx*dx + dy*dy)
            alt = float(wpt.find("alt").text)
            alt_nxt = float(wpt_nxt.find("alt").text)
            z = alt_nxt - alt0
            dz = alt_nxt - alt
            course = float(wpt.find("course").text)
            
            obj_new = CopyObject (obj, nam)

            x -= dy
            y += dx

            ScaleMatrix = M.Matrix.Scale(lenght/modelLenght, 4, M.Vector((1, 0, 0)))
            ShearMatrix = M.Matrix.Shear("YZ", 4, (0.0, -dz/lenght))
            RotationMatrix = M.Matrix.Rotation(-course, 4, "Z")
            TranslationMatrix = M.Matrix.Translation(M.Vector((x, y, z)))

            obj_new.data.transform(ScaleMatrix)
            obj_new.data.transform(ShearMatrix)
            obj_new.data.transform(RotationMatrix)
            obj_new.data.transform(TranslationMatrix)

    def MakePoles (pits):
        x, y, z = 0, 0, 0
        for wpt in pits:
            nam = wpt.find("name").text
            dx = float(wpt.find("dx").text)
            dy = float(wpt.find("dy").text)
            alt = float(wpt.find("alt").text)
            z = alt - alt0
            if scene.doRNDrot: course = math.pi * random.random()
            else: course = float(wpt.find("course").text)

            obj_new = CopyObject (obj, nam)

            RotationMatrix = M.Matrix.Rotation(-course, 4, "Z")
            TranslationMatrix = M.Matrix.Translation(M.Vector((x, y, z)))

            obj_new.data.transform(RotationMatrix)
            obj_new.data.transform(TranslationMatrix)

            x -= dy
            y += dx
    
    scene = bpy.context.scene
    obj = bpy.context.selected_objects

    fg_xml = ET.parse(pathxml)
    tree = fg_xml.getroot()
    poles = []
    fences = []
    for wpt in tree.getiterator('pole'):
        poles.append (wpt)
    for wpt in tree.getiterator('fence'):
        fences.append (wpt)

    wpt0 = tree[0][0] # info
    Tile = wpt0.find("Tile").text
    lat0 = wpt0.find("Lat").text
    lon0 = wpt0.find("Lon").text
    alt0 = float(wpt0.find("Alt").text)
    print ("Put in " + Tile + "\nOBJECT_STATIC {modelName.ac|xml} " + str(lon0) + " " + str(lat0) + " " + str(alt0) + "0, 0, 0")

    modelLenght = obj[0].dimensions.x

    if scene.polefence == 'fence' and scene.doShear : MakeShearedFence (poles)
    elif scene.polefence == 'fence' and not scene.doShear : MakeHorizontalFence (fences)
    else: MakePoles (poles)

    return 0


class OBJECT_OT_CustomButton(bpy.types.Operator):
    bl_idname = "object.custombutton"
    bl_label = "Build"
    __doc__ = "Simple Custom Button"

    def invoke(self, context, event):

        obj = bpy.context.scene.objects.active
        BuildFence(bpy.context.scene.exportpath, obj)

        return{'FINISHED'}

class VIEW3D_PT_CustomPathMenuPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "FG fencemaker"

    def draw(self, context):
        layout = self.layout
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(context.scene,"exportpath", text="")
        row.operator("object.export_path", text="Open UFO's file...")
        
        layout.prop(context.scene,"polefence", expand=True)
        
        row = layout.row()
        col = row.column()
        col.active = bpy.context.scene.polefence == 'fence'
        col.prop(context.scene, "doShear") 
        col = row.column()
        col.active = bpy.context.scene.polefence == 'pole'
        col.prop(context.scene, "doRNDrot")
        
        layout.operator(OBJECT_OT_CustomButton.bl_idname)

class OBJECT_OT_ExportPath(bpy.types.Operator):
    bl_idname = "object.export_path"
    bl_label = "Select UFO's export file"
    __doc__ = ""

    filepath = StringProperty(name="File Path", description="Filepath used for exporting the PSA file", maxlen= 1024, default= "")

    def execute(self, context):
        context.scene.exportpath = self.properties.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_module(__name__)
    print("register")

def unregister():
    bpy.utils.unregister_module(__name__)
    print("unregister")

if __name__ == "__main__":
    register()
