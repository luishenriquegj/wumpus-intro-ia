import subprocess
import time
import sys


# esse script serve para rodar o FastAPI e o Streamlit juntos
# ele inicia o FastAPI, espera 2 segundos e depois inicia o Streamlit

#porém, ele não lida com atualizações no ambiente (hot reload), então não utilizamos mais
def run_fastapi():
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "simulations_api:app", "--reload"])

def run_streamlit():
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    print("Starting FastAPI...")
    fastapi_process = run_fastapi()
    
    time.sleep(2)

    print("Starting Streamlit...")
    streamlit_process = run_streamlit()

    print("Both services are running.")

    fastapi_process.wait()
    streamlit_process.wait()