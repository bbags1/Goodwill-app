import os
import sys
import subprocess
import time
import threading
import signal
import argparse

# Global variables to track running processes
processes = []
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down all processes."""
    global running
    print("\nShutting down all processes...")
    running = False
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.terminate()
    sys.exit(0)

def run_backend_server():
    """Run the Flask backend server."""
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        [sys.executable, os.path.join("backend", "app.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(backend_process)
    
    # Wait for the server to start
    time.sleep(2)
    if backend_process.poll() is not None:
        print("Error: Backend server failed to start.")
        print(backend_process.stderr.read())
        sys.exit(1)
    
    print("Backend server running at http://localhost:5000")
    return backend_process

def run_scheduler():
    """Run the scheduler for automatic updates."""
    print("Starting scheduler...")
    scheduler_process = subprocess.Popen(
        [sys.executable, os.path.join("backend", "scheduler.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(scheduler_process)
    
    # Wait for the scheduler to start
    time.sleep(2)
    if scheduler_process.poll() is not None:
        print("Error: Scheduler failed to start.")
        print(scheduler_process.stderr.read())
        sys.exit(1)
    
    print("Scheduler running")
    return scheduler_process

def run_frontend():
    """Run the React frontend server."""
    print("Starting frontend server...")
    os.chdir("frontend")
    frontend_process = subprocess.Popen(
        ["npm", "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    processes.append(frontend_process)
    os.chdir("..")
    
    # Wait for the server to start
    time.sleep(5)
    if frontend_process.poll() is not None:
        print("Error: Frontend server failed to start.")
        print(frontend_process.stderr.read())
        sys.exit(1)
    
    print("Frontend server running at http://localhost:3000")
    return frontend_process

def monitor_process_output(process, name):
    """Monitor and print the output of a process."""
    while running:
        if process.poll() is not None:
            print(f"{name} process has stopped with exit code {process.returncode}")
            break
        
        output = process.stdout.readline()
        if output:
            print(f"[{name}] {output.strip()}")
        
        error = process.stderr.readline()
        if error:
            print(f"[{name} ERROR] {error.strip()}")
        
        time.sleep(0.1)

def main():
    """Main function to run the application."""
    parser = argparse.ArgumentParser(description="Run the Goodwill Auction Analysis Tool")
    parser.add_argument("--backend-only", action="store_true", help="Run only the backend server")
    parser.add_argument("--scheduler", action="store_true", help="Run the scheduler for automatic updates")
    parser.add_argument("--frontend-only", action="store_true", help="Run only the frontend server")
    args = parser.parse_args()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the requested components
    if args.backend_only:
        backend_process = run_backend_server()
        threading.Thread(target=monitor_process_output, args=(backend_process, "Backend"), daemon=True).start()
    elif args.frontend_only:
        frontend_process = run_frontend()
        threading.Thread(target=monitor_process_output, args=(frontend_process, "Frontend"), daemon=True).start()
    else:
        # Start all components by default
        backend_process = run_backend_server()
        threading.Thread(target=monitor_process_output, args=(backend_process, "Backend"), daemon=True).start()
        
        if args.scheduler:
            scheduler_process = run_scheduler()
            threading.Thread(target=monitor_process_output, args=(scheduler_process, "Scheduler"), daemon=True).start()
        
        frontend_process = run_frontend()
        threading.Thread(target=monitor_process_output, args=(frontend_process, "Frontend"), daemon=True).start()
    
    print("\nAll components started successfully!")
    print("Press Ctrl+C to stop all processes")
    
    # Keep the main thread alive
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 