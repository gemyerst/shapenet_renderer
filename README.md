This is a compact implementation of a batched OBJ- and PLY-renderer in blender. The inspiration was drawn
from the "Stanford Shapenet Renderer". This code can be used to render datasets such as the ones used in the
"Scene Representation Networks" paper.

This code was adapted to function with Blender 3.3.1 in Windows.

To render a batch of ply files in parallel, just make sure to input a directory to a folder instead of a file for mesh_fpath.

##Instructions:
1. First, navigate to your project directory in the command prompt or terminal. (cd to github folder)

2. Create a new conda environment and activate it by running:
```
conda create -n blender-render
conda activate blender-render
```
3. Clone the repository:
```
git clone https://github.com/gemyerst/shapenet_renderer.git
```
4. Install the required dependencies
```
pip install numpy
pip install bpy
```
Note: bpy might require additional dependencies to work on your system. See https://pypi.org/project/bpy/

5. Run the Repository.
To render a batch of PLY files in parallel, make sure to input a directory path instead of a file path for --mesh_fpath.
To render a single file, make sure the file path ends in .obj.
Ensure the corresponding materials are in the same folder.

For example:
```
python shapenet_spherical_renderer.py --mesh_fpath "path to obj or directory" --output_dir "file save location" --num_observations 100 --sphere_radius 1.2 --mode "train"
```

##License
This code is licensed under the MIT license. Please see the LICENSE file for more information.