import subprocess
import sys
import time

def run_project():
    python_executable = sys.executable  
    processes = {}

    try:
        print("1/3 server")
        processes['server'] = subprocess.Popen([python_executable, "server.py"])
        time.sleep(2)
        
        print("2/3 evacuation")
        processes['evacuation'] = subprocess.Popen([python_executable, "evac.py"])
        time.sleep(2)

        print("3/3 yolo detection")
        processes['YOLOv26n'] = subprocess.Popen([python_executable, "yolo.py"])

        print("\nall process activated")
        
        while True:
            dead_processes = []
            for name, proc in processes.items():
                exit_code = proc.poll()
                if exit_code is not None:
                    print(f"\n[ERROR]  '{name}.py' Exit Code: {exit_code})")
                    dead_processes.append(name)
            
            for name in dead_processes:
                del processes[name]
                
            if not processes:
                print("system jongryo.")
                break
                
            time.sleep(5)

    except FileNotFoundError as e:
        print(f"\nFileNotFoundError {e}")
    except Exception as e:
        print(f"\nException {e}")
    except KeyboardInterrupt:
        print("\nkeyboardInterrupt")
    finally:
        print("\nquit_process_start")
        for name in ['yolo', 'evacuate', 'server']:
            proc = processes.get(name)
            if proc and proc.poll() is None:
                print(f"||||| {name}.py quiting")
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print(f"||||{name}.py killed.")
        print("quit_success")

if __name__ == "__main__":
    run_project()