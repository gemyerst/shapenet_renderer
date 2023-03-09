This is a compact implementation of a batched OBJ- and PLY-renderer in blender. The inspiration was drawn
from the "Stanford Shapenet Renderer". This code can be used to render datasets such as the ones used in the
"Scene Representation Networks" paper.

This code was adapted to function with Blender 3.3.1 in Windows.

To render a batch of ply files in parallel, just make sure to input a directory to a folder instead of a file for mesh_fpath.

Instructions:

cd to github
conda create -n blender-render
conda activate blender-render
git clone https://github.com/gemyerst/shapenet_renderer.git
pip install numpy
pip install bpy

python shapenet_spherical_renderer.py --mesh_fpath "path to obj or directory" --output_dir "file save location" --num_observations 100 --sphere_radius 1.2 --mode "train"