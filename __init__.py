from datetime import datetime
import os
import bpy
import re
# from fileinput import filename

bl_info = {
    "name": "",
    "author": "Carlos Leyva",
    "version": (1, 1, 1),
    "blender": (2, 93, 0),
    "location": "File > Import-Export",
    "description": "Exports collections as armor options for MH Rise by using RE Mesh Noesis Wrapper.",
    "warning": "RE Mesh Noesis Wrapper is required",
    "wiki_url": "https://github.com/CarlosLeyvaAyala/MH-Rise-Armor-Option-Exporter",
    "tracker_url": "",
    "category": "Import-Export"}


def forAllObjects(f, objs):
    for o in objs:
        f(o)


def unhideObject(o): o.hide_set(False)
def hideObject(o): o.hide_set(True)


def unhideAll():
    forAllObjects(unhideObject, bpy.context.scene.objects)


def hideAll():
    forAllObjects(hideObject, bpy.context.scene.objects)


def hideArmatures(objs):
    def f(o):
        if o.type == 'ARMATURE':
            hideObject(o)
    forAllObjects(f, objs)


def showOnlyCurrentCollection(willHideArmatures=False):
    selection = bpy.context.collection.objects

    hideAll()
    forAllObjects(unhideObject, selection)

    if willHideArmatures:
        hideArmatures(selection)


def setSelected(collection, isSelected):
    for o in collection.objects:
        o.select_set(isSelected)


def includeCollectionName(baseDir, collectionName):
    return os.path.join(baseDir, collectionName)


def getFilesFromCollectionName(collectionName, requestedFilename):
    """Gets file names from the collection name."""
    names = collectionName.split("|")
    return {
        "dirName": names[0],
        "fileName": meshFileName(names[1]) if len(names) > 1 else requestedFilename,
    }


def getFilesForQuickTest(collectionName, requestedFilename):
    """Converts collection name from "dir|file" to something that can be exported."""
    names = collectionName.split("|")
    if len(names) > 1:
        fName = names[1]
        dirName = "pl" + re.search("\d+$", fName).group()
        return {
            "dirName": dirName,
            "fileName": meshFileName(fName),
        }
    else:
        return {
            "dirName": "",
            "fileName": requestedFilename,
        }


def doExport(filePath):
    bpy.ops.re_mesh_noesis.exportfile(
        filepath=filePath, selection_only=True, check_existing=False)


def testExport(filePath):
    print("Exporting ", filePath)


def processItems(collection, baseDir, fileName, getFullPath=includeCollectionName, getFileName=getFilesFromCollectionName):
    if collection.name[:2] == "__" or collection.name == "Collection":
        print("Skipping \"", collection.name, "\"")
        return

    if len(collection.objects) < 1:
        return

    output = getFileName(collection.name, fileName)
    path = getFullPath(baseDir, output["dirName"])
    os.makedirs(path, exist_ok=True)

    fn = os.path.join(path, output["fileName"])

    setSelected(collection, True)
    doExport(fn)
    # testExport(fn)
    setSelected(collection, False)


def meshFileName(fileName):
    return fileName + ".mesh.2109148288"


def getExportOptions(propertyGroup):
    return {
        "fileName": meshFileName(propertyGroup.filename),
        "outDir": propertyGroup.outDir,
        "quickDir": propertyGroup.quickTest
    }


def reportStartFinish(startMsg, finishMsg):
    def fff(obj, operation):
        obj.report({'INFO'}, startMsg)
        operation()
        obj.report({'INFO'}, finishMsg)

        print("Finished at: ", datetime.now().strftime("%H:%M:%S"))
        print("")

    return fff


reportExportSingle = reportStartFinish(
    "Exporting armor. Please wait...", "Finished exporting armor. Check System Console for results.")


def getPermanentOptions(context):
    """Gets the options used for exporting files that will be packed."""
    o = getExportOptions(context.scene.armor_option_exporter)
    return {
        "fileName": o["fileName"],
        "dir": o["outDir"]
    }


def getTestOptions(context):
    """Gets the options used for exporting files that will be tested while playing."""
    o = getExportOptions(context.scene.armor_option_exporter)
    return {
        "fileName": o["fileName"],
        "dir": o["quickDir"]
    }


def export(context, getOptionsFunc, exportFunc):
    def fff():
        unhideAll()
        o = getOptionsFunc(context)
        exportFunc(o["dir"], o["fileName"])

    return fff


def exportSelected(obj, context, getOptionsFunc, getFullPath=includeCollectionName, getFileName=getFilesFromCollectionName):
    e = export(context, getOptionsFunc,
               lambda outDir, fn: processItems(bpy.context.collection, outDir, fn, getFullPath, getFileName))
    reportExportSingle(obj, e)
    showOnlyCurrentCollection()


class ARMOROPTIONEXPORTER_OT_exportall(bpy.types.Operator):
    """Exports all collections in this file as armor options"""
    bl_label = "All"
    bl_idname = "armoroptionexporter.exportall"

    def execute(self, context):
        report = reportStartFinish("Exporting armors. Please wait...",
                                   "Finished exporting armors. See System Console for results.")

        def exportAll(baseDir, fileName):
            for c in bpy.data.collections:
                processItems(c, baseDir, fileName)

        e = export(context, getPermanentOptions, exportAll)

        report(self, e)

        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_exportselected(bpy.types.Operator):
    """Exports the current selected collection"""
    bl_label = "Selected"
    bl_idname = "armoroptionexporter.exportselected"

    def execute(self, context):
        exportSelected(self, context, getPermanentOptions)

        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_exportquick(bpy.types.Operator):
    """Exports the current selected collection so you can test while playing"""
    bl_label = "Quick test"
    bl_idname = "armoroptionexporter.exportquick"

    def execute(self, context):
        exportSelected(self, context, getTestOptions,

                       getFileName=getFilesForQuickTest)

        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_showonlycurrcollection(bpy.types.Operator):
    """Hides all objects, except the ones inside the current selected collection"""
    bl_label = "Show only current collection"
    bl_idname = "armoroptionexporter.showonlycurrcollection"

    def execute(self, _):
        showOnlyCurrentCollection()
        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_hidecurrcollection(bpy.types.Operator):
    """Hides the current selected collection"""
    bl_label = "Hide current collection"
    bl_idname = "armoroptionexporter.hidecurrcollection"

    def execute(self, _):
        forAllObjects(hideObject, bpy.context.collection.objects)

        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_showcurrcollection(bpy.types.Operator):
    """Shows the current selected collection"""
    bl_label = "Show current collection"
    bl_idname = "armoroptionexporter.showcurrcollection"

    def execute(self, _):
        forAllObjects(unhideObject, bpy.context.collection.objects)

        return {'FINISHED'}


class ARMOROPTIONEXPORTER_OT_unhideallcollections(bpy.types.Operator):
    """Unhides all collections, but not their contents. Collections must be unhidden for this plugin to properly work"""
    bl_label = "Unhide all collections"
    bl_idname = "armoroptionexporter.unhideallcollections"

    def execute(self, _):
        def hhh(c):
            c.hide_viewport = False
        forAllObjects(hhh, bpy.context.view_layer.layer_collection.children)

        return {'FINISHED'}


class ExportProperties(bpy.types.PropertyGroup):
    filename: bpy.props.StringProperty(
        name="File name", default="f_bodyXXX", description="Generated file name. Appending \".mesh.2109148288\" is not needed")
    outDir: bpy.props.StringProperty(
        name="Path", default="", description="Directory where your files will be exported. Collection names will be used to create subdirs in here")
    quickTest: bpy.props.StringProperty(
        name="Test path", default="x:\\SteamLibrary\\steamapps\\common\\MonsterHunterRise\\natives\\STM\\player\\mod\\f\\plXXX", description="Directory where the selected collection will be exported so you can test your armor option while playing")


class ARMOROPTIONEXPORTER_PT_exportPnl(bpy.types.Panel):
    bl_label = "Required info"
    bl_idname = "ARMOROPTIONEXPORTER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Export armor options"

    def draw(self, context):
        lyt = self.layout
        scene = context.scene
        exportOptions = scene.armor_option_exporter

        row = lyt.row()
        row.label(text="Ouput names and paths", icon='FILEBROWSER')

        lyt.prop(exportOptions, "filename")
        lyt.prop(exportOptions, "outDir")
        lyt.prop(exportOptions, "quickTest")

        lyt.separator()
        row = lyt.row()
        row.label(text="Export", icon='EXPORT')

        row = lyt.row()
        row.operator("armoroptionexporter.exportquick")
        row = lyt.row()
        row.operator("armoroptionexporter.exportselected")
        row.operator("armoroptionexporter.exportall")

        lyt.separator()
        row = lyt.row()
        row.label(text="Visibility", icon='HIDE_OFF')
        row = lyt.row()
        row.operator("armoroptionexporter.showonlycurrcollection")
        lyt.separator(factor=0.3)
        row = lyt.row()
        row.operator("armoroptionexporter.hidecurrcollection")
        row = lyt.row()
        row.operator("armoroptionexporter.showcurrcollection")
        lyt.separator(factor=0.3)
        row = lyt.row()
        row.operator("armoroptionexporter.unhideallcollections")


classes = (
    ExportProperties,
    ARMOROPTIONEXPORTER_PT_exportPnl,
    ARMOROPTIONEXPORTER_OT_exportquick,
    ARMOROPTIONEXPORTER_OT_exportselected,
    ARMOROPTIONEXPORTER_OT_exportall,
    ARMOROPTIONEXPORTER_OT_showonlycurrcollection,
    ARMOROPTIONEXPORTER_OT_hidecurrcollection,
    ARMOROPTIONEXPORTER_OT_showcurrcollection,
    ARMOROPTIONEXPORTER_OT_unhideallcollections,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.armor_option_exporter = bpy.props.PointerProperty(
        type=ExportProperties)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.armor_option_exporter


if __name__ == "__main__":
    register()

print("Finished at: ", datetime.now().strftime("%H:%M:%S"))
print("")
