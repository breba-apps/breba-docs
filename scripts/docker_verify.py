import docker

try:
    # Explicitly set the Unix socket base_url
    client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
    print(client.version())  # Fetch and print Docker version
    print("Docker is running")
except docker.errors.DockerException as e:
    print(f"Error connecting to Docker: {e}")