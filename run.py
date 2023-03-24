

#ALL OWN CODE, FBX FILES RUN FASTER USING THIS SYSTEM THHAN BY RUNNING THE RENDERER
import subprocess
from pathlib import Path
import sys

if __name__ == "__main__":
    mesh_folder = Path("C:/Users/G/Downloads/towerdataset/fbx_81/train/")
    output_folder = Path("C:/Users/G/Downloads/towerdataset/fbx_81/train/outputs")

    for filePath in mesh_folder.glob("*.fbx"):
        process = subprocess.Popen(args=[
            "python", "shapenet_spherical_renderer.py",
            "--mesh_fpath", filePath.resolve(),
            "--output_dir", output_folder.resolve(),
            "--num_observations", "150",
            "--sphere_radius", "1.5",
            "--mode", "test"
            ])
        
        (out, err) = process.communicate()
        if err:
            print(err.decode())
        if out:
            print(out.decode())
        

        exit_code = process.wait()
        if exit_code != 0:
            print(f"Failed for filePath {filePath}")
            sys.exit(exit_code)