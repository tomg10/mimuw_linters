import subprocess


subprocess.run("docker pull eu.gcr.io/mimuw-linters/linter_image_1.0", shell=True)
subprocess.run("docker run -dp 5000:5000 eu.gcr.io/mimuw-linters/linter_image_1.0", shell=True)

#TODO run docker
