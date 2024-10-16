# Tutorial for a simple GPU usage web server

# Get the model name
with open("/proc/device-tree/model", "r") as file:
    MODEL_NAME = file.read().strip()


print(f"Model name: {MODEL_NAME}")

# Get the path where the GPU load data is stored
# On Jetson Nano, there is a symbolic link to the file /sys/device/gpu.0/load
# Starting with Jetson Xaviers, the symbolic link is /sys/devices/platform/gpu.0/load
# However, Xaviers still have the original symlink. In Orin, the original symlink is not present

GPU_LOAD_PATH = "/sys/devices/gpu.0/load" 
if "orin" in MODEL_NAME.lower():
    # The location has been changed on the orins - /sys/devices/platform/bus@0/17000000.gpu/load
    # There's a symbolic link here:
    GPU_LOAD_PATH = "/sys/devices/platform/gpu.0/load"

with open(GPU_LOAD_PATH, 'r') as f:
    value = f.read()
print(f"GPU load: {float(value.strip()) / 10:.1f}")

def get_gpu_load():
    with open(GPU_LOAD_PATH, 'r') as f:
        value = f.read()
    gpu_load = int(float(value.strip()) / 10)
    return gpu_load
