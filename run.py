import sys
import time
import subprocess

def run_project():
    processes = []
    try:
        server_process = subprocess.Popen([sys.executable, "server.py"], text=True)
        processes.append(server_process)
        time.sleep(2)
        evac_process = subprocess.Popen([sys.executable, "evacuate.py"], text=True)
        processes.append(evac_process)
        time.sleep(2)
        #client_process = subprocess.Popen([sys.executable, "client.py"], text=False)
        #processes.append(client_process)
        #time.sleep(2)
        subprocess.call([sys.executable, "yolo.py"])
    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except Exception:
                pass

if __name__ == "__main__":
    run_project()