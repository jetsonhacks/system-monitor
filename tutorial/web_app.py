from fasthtml.common import *
from data_app import MODEL_NAME, get_gpu_load

app, rt = fast_app()

@rt('/')
def get():
    gpu_load = get_gpu_load()
    page = Title('Jetson Web Sample'), Body(
        Div( H3(MODEL_NAME), 
            Span(f"GPU Load: {gpu_load}%"),
            style="text-align: center;")
    )
    return page

if __name__ == "__main__":
    serve(host='0.0.0.0',port=5000)