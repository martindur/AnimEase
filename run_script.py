import bpy
import os

filename = os.path.join(os.path.dirname(bpy.data.filepath), "animEase.py")
exec(compile(open(filename).read(), filename, 'exec'))