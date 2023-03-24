import argparse
import numpy as np
import os
import glob
import sys
sys.path.append(os.path.dirname(__file__))

import sys
import util
import blender_interface
packages_path = "C:/Users/G/GitHub/shapenet_renderer"
sys.path.insert(0, packages_path + "util.py")
sys.path.insert(0, packages_path + "blender_interface")

if(__name__== "__main__"):
    p = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')
    p.add_argument('--mesh_fpath', type=str, required=True, help='The path to the obj file to render.')
    p.add_argument('--output_dir', type=str, required=True, help='The path the output will be dumped to.')
    p.add_argument('--num_observations', type=int, required=True, help='The number of images to render.')
    p.add_argument('--sphere_radius', type=float, required=True, help='The camera distance to use.')
    p.add_argument('--mode', type=str, required=True, help='Options: train and test')
    
    argv = p.parse_args()
    #argv = sys.argv[sys.argv.index("--") + 1:]

instance_name = (argv.mesh_fpath.split('/')[-1]).split(".")[0] #OWN CODE
instance_dir = os.path.join(argv.output_dir, instance_name)

renderer = blender_interface.BlenderInterface(resolution=128) #CHANGE RESOLUTION HERE

if argv.mode == 'train':
    cam_locations = util.sample_spherical(argv.num_observations, argv.sphere_radius)
elif argv.mode == 'test':
    cam_locations = util.get_archimedean_spiral(argv.sphere_radius, argv.num_observations)

obj_location = np.zeros((1,3))

cv_poses = util.look_at(cam_locations, obj_location)
blender_poses = [util.cv_cam2world_to_bcam2world(m) for m in cv_poses]

shapenet_rotation_mat = np.array([[1.0000000e+00,  0.0000000e+00,  0.0000000e+00],
                                  [0.0000000e+00, -1.0000000e+00, -1.2246468e-16],
                                  [0.0000000e+00,  1.2246468e-16, -1.0000000e+00]])
rot_mat = np.eye(3)
hom_coords = np.array([[0., 0., 0., 1.]]).reshape(1, 4)
obj_pose = np.concatenate((rot_mat, obj_location.reshape(3,1)), axis=-1)
obj_pose = np.concatenate((obj_pose, hom_coords), axis=0)


#OWN CODE TO AUTOMATE ALL OBJECTS IN A FOLDER
if(argv.mesh_fpath.endswith(".obj") or argv.mesh_fpath.endswith(".fbx")or argv.mesh_fpath.endswith(".ply") ):
    renderer.import_mesh(argv.mesh_fpath, scale=1., object_world_matrix=obj_pose)
    renderer.render(instance_dir, blender_poses, write_cam_params=True)

else:
    for file in os.listdir(argv.mesh_fpath):
        if file.endswith(".obj") or file.endswith(".fbx") or file.endswith(".fbx"):
            renderer.import_mesh(argv.mesh_fpath + file, scale=1., object_world_matrix=obj_pose)
            folder_name = file[:-4]
            renderer.render(instance_dir + folder_name, blender_poses, write_cam_params=True)

