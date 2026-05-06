"""
build_blender_template.py
Run this ONCE on the render PC to auto-generate kinetic_quote.blend.
No manual Blender work needed -- this script builds the template programmatically.

Run with:
  blender --background --python build_blender_template.py

It creates: C:\DopamineStudios\BlenderTemplates\kinetic_quote.blend
"""

import bpy
import os
import sys

OUTPUT_DIR = r"C:\DopamineStudios\BlenderTemplates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Clean the default scene ─────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 72       # 3 seconds at 24fps
scene.render.fps = 24
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'

# ── Black background ────────────────────────────────────────────────
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.039, 0.039, 0.039, 1)  # #0a0a0a

# ── Main text object ────────────────────────────────────────────────
bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.name = "main_text"
text_obj.data.name = "main_text_data"
text_obj.data.body = "PLACEHOLDER"
text_obj.data.align_x = 'CENTER'
text_obj.data.align_y = 'CENTER'
text_obj.data.size = 0.4
text_obj.data.space_character = 0.95
text_obj.data.extrude = 0.002

# White material
mat = bpy.data.materials.new("text_material")
mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)
text_obj.data.materials.append(mat)

# ── Animation: scale 0 → 1 (slam entrance) ─────────────────────────
# Frame 1: scale 0
text_obj.scale = (0.0, 0.0, 0.0)
text_obj.keyframe_insert(data_path="scale", frame=1)

# Frame 5: scale 1.1 (slight overshoot)
text_obj.scale = (1.1, 1.1, 1.1)
text_obj.keyframe_insert(data_path="scale", frame=5)

# Frame 9: scale 1.0 (settle)
text_obj.scale = (1.0, 1.0, 1.0)
text_obj.keyframe_insert(data_path="scale", frame=9)

# Frame 60: scale 1.0 (hold)
text_obj.keyframe_insert(data_path="scale", frame=60)

# Frame 72: scale 0 (exit fade -- done via opacity below)
text_obj.keyframe_insert(data_path="scale", frame=72)

# ── Opacity animation: fade out last 12 frames ──────────────────────
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for n in nodes:
    nodes.remove(n)

# Build: emission → transparent → mix → output
emission = nodes.new("ShaderNodeEmission")
emission.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
emission.inputs[1].default_value = 2.0

transparent = nodes.new("ShaderNodeBsdfTransparent")
mix = nodes.new("ShaderNodeMixShader")
output = nodes.new("ShaderNodeOutputMaterial")

links.new(transparent.outputs[0], mix.inputs[1])
links.new(emission.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], output.inputs[0])

# Opacity keyframes
mix.inputs[0].default_value = 1.0   # fully opaque by default
mix.inputs[0].keyframe_insert(data_path="default_value", frame=1)
mix.inputs[0].keyframe_insert(data_path="default_value", frame=60)

mix.inputs[0].default_value = 0.0
mix.inputs[0].keyframe_insert(data_path="default_value", frame=72)

mat.blend_method = 'BLEND'

# ── Camera ──────────────────────────────────────────────────────────
bpy.ops.object.camera_add(location=(0, -5, 0))
cam = bpy.context.active_object
cam.rotation_euler = (1.5708, 0, 0)  # 90 degrees to face the text
scene.camera = cam

# ── Output path placeholder (overridden per render by watcher.py) ───
scene.render.filepath = r"C:\DopamineStudios\Temp\kinetic_quote_"

# ── Save the .blend file ────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, "kinetic_quote.blend")
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"\n[DONE] Template saved: {output_path}")
print("You can now run watcher.py -- Blender is fully linked.")
