import pyedflib
import time
import queue
import threading


def process_data_point(data_point):
    # Example processing: Convert to 3D coordinates with Z = 0
    x, y, z = data_point[0], data_point[1], 0
    return [x, y, z]


def get_processed_data(data_queue, stream_index=2):
    while not data_queue.empty():
        data_point = data_queue.get()
        yield data_point[stream_index]


def read_bdf_file(file_path, data_queue):
    try:
        with pyedflib.EdfReader(file_path) as f:
            n = f.signals_in_file
            signal_labels = f.getSignalLabels()
            n_samples = f.getNSamples()[0]

            for i in range(n_samples):
                data_point = []
                for j in range(n):
                    value = f.readSignal(j, start=i, n=1)
                    data_point.append(value[0])
                data_queue.put(data_point)
                time.sleep(1)  # Simulate delay for live data
    except Exception as e:
        print(f"An error occurred: {e}")


def process_and_print_data(data_queue):
    while True:
        processed_data = get_processed_data(data_queue)
        if processed_data:
            print(processed_data)
        time.sleep(1)  # Adjust as needed


def moving_average(new_value, recent_values, window_size):
    if new_value is not None:
        recent_values.append(new_value)
    if len(recent_values) > window_size:
        recent_values.pop(0)
    return sum(recent_values) / len(recent_values) if recent_values else 1


if __name__ == "__main__":
    data_queue = queue.Queue()
    file_path = input("Enter the path of the BDF file: ")

    # Start the file reading in a separate thread
    file_thread = threading.Thread(target=read_bdf_file, args=(file_path, data_queue))
    file_thread.start()

    # Start the data processing and printing in the main thread
    process_and_print_data(data_queue)
