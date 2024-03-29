import os
import bpy
import util
import json
import math
import mathutils
import numpy as np
from PIL import Image
import random

#PLEASE FIND ORIGINAL HERE: https://github.com/vsitzmann/shapenet_renderer

class BlenderInterface():
    def __init__(self, resolution=128, background_color=(1,1,1)):
        self.resolution = resolution

        # Delete the default cube (default selected)
        bpy.ops.object.delete()

        # Deselect all. All new object added to the scene will automatically selected.
        self.blender_renderer = bpy.                                                                                                                                                                                                                                                                                                                                                                                         context.scene.render
        self.blender_renderer.resolution_x = resolution
        self.blender_renderer.resolution_y = resolution
        self.blender_renderer.resolution_percentage = 100
        self.blender_renderer.image_settings.file_format = 'PNG'  # set output format to .png

        world = bpy.context.scene.world
        world.color = background_color

        # OWN CODE ADJUSTMENTS TO ENABLE FUNCTIONALITY IN NEW BLENDER VERSION
        lamp1 = bpy.data.lights['Light']
        lamp1.type = 'SUN'
        lamp1
        # Enable nodes for the light if necessary
        #if not lamp1.data.use_nodes:
        #     lamp1.data.use_nodes = True
        #lamp1.shadow_method = 'NOSHADOW'
        lamp1.specular_factor = 0.0
        lamp1.energy = 1.

        bpy.ops.object.light_add(type='SUN')
        lamp2 = bpy.data.lights['Sun']
        #lamp2.shadow_method = 'NOSHADOW'
        lamp2.specular_factor = 0.0
        lamp2.energy = 1.
        bpy.data.objects['Sun'].rotation_euler = bpy.data.objects['Light'].rotation_euler
        bpy.data.objects['Sun'].rotation_euler[0] += 180

        bpy.ops.object.light_add(type='SUN')
        lamp2 = bpy.data.lights['Sun.001']
        #lamp2.shadow_method = 'NOSHADOW'
        lamp2.specular_factor = 0.0
        lamp2.energy = 0.3
        bpy.data.objects['Sun.001'].rotation_euler = bpy.data.objects['Light'].rotation_euler
        bpy.data.objects['Sun.001'].rotation_euler[0] += 90

        # Set up the camera
        self.camera = bpy.context.scene.camera
        self.camera.data.sensor_height = self.camera.data.sensor_width # Square sensor
        util.set_camera_focal_length_in_world_units(self.camera.data, 525./512*resolution) # Set focal length to a common value (kinect)

        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def transform_mesh(obj): #DEF IS OWN CODE
        # Get the bounding box dimensions
        bbox = obj.bound_box[:]
        dimensions = [(max([bb[i] for bb in bbox]) - min([bb[i] for bb in bbox])) for i in range(3)]
        max_dim = max(dimensions)

        # Calculate the scale factor needed to make the bounding box 1 unit in size
        scale_factor = 1.0 / max_dim
        obj.scale = (scale_factor, scale_factor, scale_factor)

        # Move the object and its bounding box to the world origin
        new_bbox = [mathutils.Vector(v) for v in bbox]
        for v in new_bbox:
            v[0] = (v[0] - obj.location[0]) * scale_factor
            v[1] = (v[1] - obj.location[1]) * scale_factor
            v[2] = (v[2] - obj.location[2]) * scale_factor

        # Move the object and its bounding box to the world origin
        obj.location = (0.0, 0.0, 0.0)
        for v in new_bbox:
            v[0] += obj.location[0]
            v[1] += obj.location[1]
            v[2] += obj.location[2]

        return obj

    @staticmethod
    def newMaterial(id):
        mat = bpy.data.materials.get(id)

        if mat is None:
            mat = bpy.data.materials.new(name=id)

        mat.use_nodes = True

        if mat.node_tree:
            mat.node_tree.links.clear()
            mat.node_tree.nodes.clear()
        return mat
    
    #OWN CODE
    def import_mesh(self, fpath, scale=1., object_world_matrix=None):
        ext = os.path.splitext(fpath)[-1]
        if ext == '.obj':
            bpy.ops.import_scene.obj(filepath=str(fpath), split_mode='OFF')
        elif ext == '.ply':
            bpy.ops.import_mesh.ply(filepath=str(fpath))
        elif ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=str(fpath))


        bpy.context.selected_objects

        mesh_objects = [m for m in bpy.context.scene.objects if m.type == 'MESH']
        for mesh in mesh_objects:
            #Select all mesh objects
            mesh.select_set(state=True)
            #Makes one active
            bpy.context.view_layer.objects.active = mesh

        bpy.ops.object.join()
        obj_in = bpy.context.selected_objects[0]

        util.dump(bpy.context.selected_objects)

        if object_world_matrix is not None:
            obj_in.matrix_world = object_world_matrix

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        
        obj = BlenderInterface.transform_mesh(obj_in)

        # Disable transparency & specularities
        M = bpy.data.materials


        for i in range(len(M)):
            M[i].show_transparent_back = False
            M[i].specular_intensity = 0.0
            #M[i] = mat

        # Disable texture interpolation
        T = bpy.data.textures
        for i in range(len(T)):
            try:
                T[i].use_interpolation = False
                T[i].use_mipmap = False
                T[i].use_filter_size_min = True
                T[i].filter_type = "BOX"
            except:
                continue

    @staticmethod #OWN CODE
    def listify_matrix(matrix): 
        matrix_list = []
        for row in matrix:
            matrix_list.append(list(row))
        return matrix_list

    def render(self, output_dir, blender_cam2world_matrices, write_cam_params=False):

        if write_cam_params:
            img_dir = os.path.join(output_dir, 'rgb')
            pose_dir = os.path.join(output_dir, 'pose')

            util.cond_mkdir(img_dir)
            util.cond_mkdir(pose_dir)
        else:
            img_dir = output_dir
            util.cond_mkdir(img_dir)

        # Data to store in JSON file
        out_data = {
            'camera_angle_x': bpy.data.objects['Camera'].data.angle_x,
        }
        out_data['frames'] = []

        if write_cam_params:
            K = util.get_calibration_matrix_K_from_blender(self.camera.data)
            with open(os.path.join(output_dir, 'intrinsics.txt'),'w') as intrinsics_file:
                intrinsics_file.write('%f %f %f 0.\n'%(K[0][0], K[0][2], K[1][2]))
                intrinsics_file.write('0. 0. 0.\n')
                intrinsics_file.write('1.\n')
                intrinsics_file.write('%d %d\n'%(self.resolution, self.resolution))

        for i in range(len(blender_cam2world_matrices)):
            self.camera.matrix_world = blender_cam2world_matrices[i]

            # Render the object
            if os.path.exists(os.path.join(img_dir, '%06d.png' % i)):
                continue

            # Render the color image
            image_name = os.path.join(img_dir, '%06d.png'%i)
            self.blender_renderer.filepath = image_name
            bpy.context.scene.render.dither_intensity = 0.0
            bpy.context.scene.render.film_transparent = True
            bpy.ops.render.render(write_still=True)

            # add a whitebackground to the transparent png THIS IS OWN CODE
            # when rendering, the tone of the white background depends on the lighting
            # this ensures a white background every time
            image = Image.open(image_name).convert("RGBA")
            new_image = Image.new("RGBA", image.size, "WHITE")
            new_image.paste(image, mask=image)
            #bw = new_image.convert("L")
            new_image.save(image_name, "PNG")

            if write_cam_params:
                # Write out camera pose
                RT = util.get_world2cam_from_blender_cam(self.camera)
                cam2world = RT.inverted()
                with open(os.path.join(pose_dir, '%06d.txt'%i),'w') as pose_file:
                    matrix_flat = []
                    for j in range(4):
                        for k in range(4):
                            matrix_flat.append(cam2world[j][k])
                    pose_file.write(' '.join(map(str, matrix_flat)) + '\n')
            

                #openGL coordinates to .json file - OWN CODE
                frame_data = {
                    'file_path': "train\\" + '%06d.txt'%i,
                    'rotation': math.radians((2*math.pi)/len(blender_cam2world_matrices)),
                    'transform_matrix': BlenderInterface.listify_matrix(self.camera.matrix_world)
                }
                out_data['frames'].append(frame_data)    

        with open(output_dir + '/' + 'transforms.json', 'w') as out_file:
            json.dump(out_data, out_file, indent=4)

        # Remember which meshes were just imported
        meshes_to_remove = []
        for ob in bpy.context.selected_objects:
            meshes_to_remove.append(ob.data)

        bpy.ops.object.delete()

        # Remove the meshes from memory too
        for mesh in meshes_to_remove:
            bpy.data.meshes.remove(mesh)