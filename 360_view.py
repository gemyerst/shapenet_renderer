# A simple script that uses blender to render views of a single object by rotation the camera around it.
# Also produces depth map at the same time.

import argparse, sys, os
import json
import bpy
import mathutils
from mathutils import Matrix, Vector
import numpy as np

import sys
packages_path = "C:/Users/G/GitHub/shapenet_renderer" + "util.py"
sys.path.insert(0, packages_path )
         
DEBUG = False
            
VIEWS = 100
RESOLUTION = 128
RESULTS_PATH = 'white/mw1_train'
DEPTH_SCALE = 1.4
COLOR_DEPTH = 8
FORMAT = 'PNG'
RANDOM_VIEWS = True
UPPER_VIEWS = True


fp = bpy.path.abspath(f"//{RESULTS_PATH}")


def listify_matrix(matrix):
    matrix_list = []
    for row in matrix:
        matrix_list.append(list(row))
    return matrix_list

if not os.path.exists(fp):
    os.makedirs(fp)

# Data to store in JSON file
out_data = {
    'camera_angle_x': bpy.data.objects['Camera'].data.angle_x,
}

poses_path = os.path.join(fp, "poses")
if not os.path.exists(poses_path):
    os.mkdir(poses_path)

# Render Optimizations
bpy.context.scene.render.use_persistent_data = True


# Set up rendering of depth map.
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links

# Add passes for additionally dumping albedo and normals.
#bpy.context.scene.view_layers["RenderLayer"].use_pass_normal = True
bpy.context.scene.render.image_settings.file_format = str(FORMAT)
bpy.context.scene.render.image_settings.color_depth = str(COLOR_DEPTH)

if not DEBUG:
    # Create input render layer node.
    render_layers = tree.nodes.new('CompositorNodeRLayers')

    depth_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    depth_file_output.label = 'Depth Output'
    if FORMAT == 'OPEN_EXR':
      links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])
    else:
      # Remap as other types can not represent the full range of depth.
      map = tree.nodes.new(type="CompositorNodeMapValue")
      # Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
      map.offset = [-0.7]
      map.size = [DEPTH_SCALE]
      map.use_min = True
      map.min = [0]
      links.new(render_layers.outputs['Depth'], map.inputs[0])

      links.new(map.outputs[0], depth_file_output.inputs[0])

    normal_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    normal_file_output.label = 'Normal Output'
    links.new(render_layers.outputs['Normal'], normal_file_output.inputs[0])

# Background
bpy.context.scene.render.dither_intensity = 0.0
bpy.context.scene.render.film_transparent = True


# Create collection for objects not to render with background
objs = [ob for ob in bpy.context.scene.objects if ob.type in ('EMPTY') and 'Empty' in ob.name]
bpy.ops.object.delete({"selected_objects": objs})

def parent_obj_to_camera(b_camera):
    origin = (0, 0, 0)
    b_empty = bpy.data.objects.new("Empty", None)
    b_empty.location = origin
    b_camera.parent = b_empty  # setup parenting

    scn = bpy.context.scene
    scn.collection.objects.link(b_empty)
    bpy.context.view_layer.objects.active = b_empty
    # scn.objects.active = b_empty
    return b_empty

scene = bpy.context.scene
scene.render.resolution_x = RESOLUTION
scene.render.resolution_y = RESOLUTION
scene.render.resolution_percentage = 100

cam = scene.objects['Camera']
cam.location = (0, 4.0, 0.5)
cam_constraint = cam.constraints.new(type='TRACK_TO')
cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
cam_constraint.up_axis = 'UP_Y'
b_empty = parent_obj_to_camera(cam)
cam_constraint.target = b_empty

scene.render.image_settings.file_format = 'PNG'  # set output format to .png

from math import radians

stepsize = 360.0 / VIEWS
rotation_mode = 'XYZ'

if not DEBUG:
    for output_node in [depth_file_output, normal_file_output]:
        output_node.base_path = ''

out_data['frames'] = []

def set_camera_focal_length_in_world_units(camera_data, focal_length):
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camera_data.sensor_width
    sensor_height_in_mm = camera_data.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camera_data.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal),
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal),
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm

    camera_data.lens = focal_length / s_u

#get openCV coordinates out as well
def get_world2cam_from_blender_cam(camGL):
    # bcam stands for blender camera
    r_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Transpose since the rotation is object rotation,
    # and we want coordinate rotation
    # Use matrix_world instead to account for all constraints
    # decompose: extract components back out of the matrix as two vectors and a quaternion
    location, rotation = camGL.decompose()[0:2] # Matrix_world returns the cam2world matrix.
    r_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:
    t_world2bcam = -1 * r_world2bcam @ location

    # Build the coordinate transform matrix from world to computer vision camera
    r_world2cv = r_bcam2cv @ r_world2bcam
    t_world2cv = r_bcam2cv @ t_world2bcam

    # put into 3x4 matrix
    rt = Matrix((
        r_world2cv[0][:] + (t_world2cv[0],),
        r_world2cv[1][:] + (t_world2cv[1],),
        r_world2cv[2][:] + (t_world2cv[2],),
        (0,0,0,1)
    ))
    cam2world = rt.inverted()
    return cam2world


camera = bpy.context.scene.camera
camera.data.sensor_height = camera.data.sensor_width # Square sensor
util.set_camera_focal_length_in_world_units(self.camera.data, 525./512*resolution)

counter = 0
for i in range(0, VIEWS):
    if RANDOM_VIEWS:
        scene.render.filepath = fp + '/r_' + str(i)
        if UPPER_VIEWS:
            rot = np.random.uniform(0, 1, size=3) * (1,0,2*np.pi)
            rot[0] = np.abs(np.arccos(1 - 2 * rot[0]) - np.pi/2)
            b_empty.rotation_euler = rot
        else:
            b_empty.rotation_euler = np.random.uniform(0, 2*np.pi, size=3)
    else:
        print("Rotation {}, {}".format((stepsize * i), radians(stepsize * i)))
        scene.render.filepath = fp + '/r_{0:03d}'.format(int(i * stepsize))

    # depth_file_output.file_slots[0].path = scene.render.filepath + "_depth_"
    # normal_file_output.file_slots[0].path = scene.render.filepath + "_normal_"

    if DEBUG:
        break
    else:
        bpy.ops.render.render(write_still=True)  # render still

    frame_data = {
        'file_path': scene.render.filepath,
        'rotation': radians(stepsize),
        'transform_matrix': listify_matrix(cam.matrix_world)
    }
    out_data['frames'].append(frame_data)
    
    #save poses
    name = str(counter).zfill(6) + ".txt"
    if not os.path.exists(fp):
        f = open(poses_path + "/" + name, "x")
    else:
        f = open(poses_path + "/" + name, "w")
    
    
    cam2world = get_world2cam_from_blender_cam(cam)
    #f.write(str(listify_matrix(rt)))
    with open(os.path.join(pose_dir, '%06d.txt'%i),'w') as pose_file:
                    matrix_flat = []
                    for j in range(4):
                        for k in range(4):
                            matrix_flat.append(cam2world[j][k])
                    f.write(' '.join(map(str, matrix_flat)) + '\n')

    if RANDOM_VIEWS:
        if UPPER_VIEWS:
            rot = np.random.uniform(0, 1, size=3) * (1,0,2*np.pi)
            rot[0] = np.abs(np.arccos(1 - 2 * rot[0]) - np.pi/2)
            b_empty.rotation_euler = rot
        else:
            b_empty.rotation_euler = np.random.uniform(0, 2*np.pi, size=3)
    else:
        b_empty.rotation_euler[2] += radians(stepsize)
        
    counter += 1


#base_location = "C:/Users/G/GitHub/nvdiffrec/data/blender_data/car_buildings/poses/"

if not DEBUG:
    with open(fp + '/' + 'transforms.json', 'w') as out_file:
        json.dump(out_data, out_file, indent=4)
    