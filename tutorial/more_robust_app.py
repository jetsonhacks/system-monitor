# Tutorial - Code with some error checking

def get_model_name():
    try:
        with open("/proc/device-tree/model", "r") as file:
            model_name = file.read().strip()
    except FileNotFoundError:
        print("Error: The file '/proc/device-tree/model' was not found.")
        model_name = None
    except PermissionError:
        print("Error: Permission denied while accessing '/proc/device-tree/model'.")
        model_name = None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        model_name = None

    # Optional: Handle the case where model_name is None if required
    if model_name is None:
        model_name = "Unknown"

    return model_name

# Example usage
MODEL_NAME = get_model_name()
print(f"Model Name: {MODEL_NAME}")

GPU_LOAD_PATH = "/sys/devices/gpu.0/load" 
if "orin" in MODEL_NAME.lower():
    # The location has been changed on the orins - /sys/devices/platform/bus@0/17000000.gpu/load
    # There's a symbolic link here:
    GPU_LOAD_PATH = "/sys/devices/platform/gpu.0/load"


def get_gpu_load():
    try:
        with open(GPU_LOAD_PATH, 'r') as f:
            value = f.read()
        gpu_load = int(float(value.strip()) / 10)
        return gpu_load
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing '{GPU_LOAD_PATH}': {e}")
        return None
    except ValueError:
        print(f"Error: Invalid value read from '{GPU_LOAD_PATH}'.")
        return None

# Example usage
gpu_load = get_gpu_load()
if gpu_load is not None:
    print(f"GPU load: {gpu_load}%")