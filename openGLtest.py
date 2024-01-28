import queue
import glfw
import random
from OpenGL.GL import *
import threading
from getProcessedData import read_bdf_file, get_processed_data, moving_average
from queue import Queue

bdf_path = "/Users/ii/generative/eeg-data/sub-001/ses-01/eeg/sub-001_ses-01_task-meditation_eeg.bdf"


def generate_grid_squares(num_squares):
    squares = []
    colors = []
    size = 1.0 / num_squares  # Size of each square

    for i in range(num_squares):
        for j in range(num_squares):
            x, y = i * size, j * size  # Bottom left corner
            # Define vertices for one square
            square_vertices = [
                x,
                y,
                0.0,
                x + size,
                y,
                0.0,
                x + size,
                y + size,
                0.0,
                x,
                y + size,
                0.0,
            ]
            squares.extend(square_vertices)
            # Define color for one square (random colors for simplicity)
            color = [random.random(), random.random(), random.random()]
            colors.extend(color * 4)  # Repeat color for each vertex

    return squares, colors


def create_vbo_old(vertices):
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(
        GL_ARRAY_BUFFER,
        len(vertices) * 4,
        (GLfloat * len(vertices))(*vertices),
        GL_STATIC_DRAW,
    )
    return vbo


def load_shader(shader_file, shader_type):
    with open(shader_file, "r") as f:
        shader_source = f.read()

    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_source)
    glCompileShader(shader)

    # Check for shader compilation errors
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        info_log = glGetShaderInfoLog(shader)
        raise RuntimeError(f"Shader compilation failed with message: {info_log}")

    return shader


def create_vbo(vertices):
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(
        GL_ARRAY_BUFFER,
        len(vertices) * 4,
        (GLfloat * len(vertices))(*vertices),
        GL_STATIC_DRAW,
    )
    return vbo


def create_program(vertex_shader, fragment_shader):
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)

    # Bind attribute location
    glBindAttribLocation(program, 0, "aPos")

    glLinkProgram(program)

    # Check for linking errors
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        info_log = glGetProgramInfoLog(program)
        raise RuntimeError(f"Shader linking failed with message: {info_log}")

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return program


def main():
    if not glfw.init():
        return

    window = glfw.create_window(640, 480, "Dynamic Data Visualization", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    vertex_shader = load_shader("vertex_shader.glsl", GL_VERTEX_SHADER)
    fragment_shader = load_shader("fragment_shader.glsl", GL_FRAGMENT_SHADER)
    shader_program = create_program(vertex_shader, fragment_shader)

    # Square vertices (Two triangles)
    vertices = [
        -0.5,
        -0.5,
        0.0,  # Bottom left
        0.5,
        -0.5,
        0.0,  # Bottom right
        0.5,
        0.5,
        0.0,  # Top right
        -0.5,
        0.5,
        0.0,  # Top left
    ]
    VBO = create_vbo(vertices)

    # Activate shader program
    glUseProgram(shader_program)

    position = glGetAttribLocation(shader_program, "aPos")
    glEnableVertexAttribArray(position)
    glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, None)

    data_queue = Queue()
    data_thread = threading.Thread(target=read_bdf_file, args=(bdf_path, data_queue))
    data_thread.start()

    window_size = 10
    recent_values = []  # List to store recent values for moving average

    num_squares = 9
    vertices, colors = generate_grid_squares(num_squares)

    # Create VBOs for vertices and colors
    vertex_vbo = create_vbo(vertices)
    color_vbo = create_vbo(colors)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        # Bind vertex VBO
        glBindBuffer(GL_ARRAY_BUFFER, vertex_vbo)
        glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(position)

        # Bind color VBO
        glBindBuffer(GL_ARRAY_BUFFER, color_vbo)
        color = glGetAttribLocation(shader_program, "aColor")
        glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(color)

        for data in get_processed_data(data_queue):
            window_average = moving_average(data, recent_values, window_size)
            data_scale = data - window_average

            print(data_scale, data / window_average)

            # Apply scale to vertices
            scaled_vertices = [x * data_scale for x in vertices]
            glBindBuffer(GL_ARRAY_BUFFER, VBO)
            glBufferData(
                GL_ARRAY_BUFFER,
                len(scaled_vertices) * 4,
                (GLfloat * len(scaled_vertices))(*scaled_vertices),
                GL_DYNAMIC_DRAW,
            )

        for i in range(num_squares * num_squares):
            glDrawArrays(GL_QUADS, i * 4, 4)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
