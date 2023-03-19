


import subprocess
from pathlib import Path
import sys


if __name__ == "__main__":
    mesh_folder = Path("C:/Users/G/GitHub/datasets/fbx_dataset/fbxtest/")
    output_folder = Path("C:/Users/G/GitHub/datasets/fbx_dataset/fbxtest/outputs")

    for filePath in mesh_folder.glob("*.fbx"):
        process = subprocess.Popen(args=[
            "python", "shapenet_spherical_renderer.py",
            "--mesh_fpath", filePath.resolve(),
            "--output_dir", output_folder.resolve(),
            "--num_observations", "50",
            "--sphere_radius", "1.5",
            "--mode", "train"
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
