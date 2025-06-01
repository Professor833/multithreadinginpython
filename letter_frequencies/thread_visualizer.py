import json
import time
import csv
import os
from threading import Thread, Lock
import urllib.request
import matplotlib.pyplot as plt
import numpy as np

# Global variables for visualization
thread_states = {}  # To track thread states
lock_holder = None  # To track which thread holds the lock
finished_threads = 0  # Count of finished threads
frequency = {}  # Letter frequency dictionary
visualization_data = []  # Store events for visualization
start_time = None  # Program start time

# Initialize frequency dictionary
for c in "abcdefghijklmnopqrstuvwxyz":
    frequency[c] = 0

# Lock with tracking capabilities
class TrackedLock:
    def __init__(self):
        self.lock = Lock()
        self.holder = None
    
    def acquire(self, thread_id=None):
        global lock_holder, visualization_data
        self.lock.acquire()
        self.holder = thread_id
        lock_holder = thread_id
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'lock_acquire',
            'thread': thread_id
        })
    
    def release(self):
        global lock_holder, visualization_data
        thread_id = self.holder  # Store before setting to None
        self.holder = None
        lock_holder = None
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'lock_release',
            'thread': thread_id
        })
        self.lock.release()

# Modified count_letters function with visualization
def count_letters(url, frequency, lock, thread_id):
    global thread_states, finished_threads, visualization_data
    
    # Record thread start
    thread_states[thread_id] = 'fetching'
    visualization_data.append({
        'time': time.time() - start_time,
        'event': 'start',
        'thread': thread_id,
        'url': url
    })
    
    # Fetch data
    try:
        response = urllib.request.urlopen(url)
        txt = str(response.read())
        
        # Record processing state
        thread_states[thread_id] = 'processing'
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'processing',
            'thread': thread_id
        })
        
        # Process letters
        lock.acquire(thread_id)
        for letter in txt:
            letter = letter.lower()
            if letter in frequency:
                frequency[letter] += 1
        lock.release()
                
        # Record completion
        thread_states[thread_id] = 'finished'
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'finish',
            'thread': thread_id
        })
        
        finished_threads += 1
    except Exception as e:
        thread_states[thread_id] = 'error'
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'error',
            'thread': thread_id,
            'error': str(e)
        })

# Main function with visualization
def main_with_visualization():
    global start_time, thread_states, finished_threads, visualization_data
    
    # Reset global state
    thread_states = {}
    finished_threads = 0
    visualization_data = []
    
    # Create tracked lock
    lock = TrackedLock()
    
    # Record start time
    start_time = time.time()
    
    # Start threads
    threads = []
    for i in range(1000, 1020):
        thread_id = f"Thread-{i}"
        t = Thread(
            target=count_letters,
            args=(f"https://www.rfc-editor.org/rfc/rfc{i}.txt", frequency, lock, thread_id),
            name=thread_id
        )
        threads.append(t)
        t.start()
        
        # Record thread creation
        visualization_data.append({
            'time': time.time() - start_time,
            'event': 'create',
            'thread': thread_id
        })
    
    # Wait for threads to complete
    while finished_threads < 20:
        time.sleep(0.05)
    
    # Record end time and results
    end_time = time.time()
    execution_time = end_time - start_time
    
    visualization_data.append({
        'time': execution_time,
        'event': 'program_end',
        'frequency': frequency.copy()
    })
    
    print(json.dumps(frequency, indent=4))
    print("Done, time taken", execution_time)
    
    # Return data for visualization
    return visualization_data, execution_time

# Create visualization - simplified version for faster generation
def visualize_threads(data, execution_time):
    # Extract thread IDs and create a color map
    thread_ids = sorted(list({event['thread'] for event in data if 'thread' in event and event['thread'] is not None}))
    colors = plt.cm.tab20(np.linspace(0, 1, len(thread_ids)))
    thread_colors = {thread_id: colors[i] for i, thread_id in enumerate(thread_ids)}
    
    # Create figure for thread timeline
    plt.figure(figsize=(12, 8))
    
    # Thread timeline visualization
    for i, thread_id in enumerate(thread_ids):
        thread_events = [event for event in data if event.get('thread') == thread_id]
        
        # Get key events
        fetch_events = [event for event in thread_events if event['event'] == 'start']
        process_events = [event for event in thread_events if event['event'] == 'processing']
        finish_events = [event for event in thread_events if event['event'] == 'finish']
        lock_events = [event for event in thread_events if event['event'] == 'lock_acquire']
        
        # Plot timeline
        if fetch_events:
            plt.plot([fetch_events[0]['time']], [i], 'go', markersize=8)
            
        if fetch_events and process_events:
            plt.plot([fetch_events[0]['time'], process_events[0]['time']], [i, i], 'b-', linewidth=2)
        
        if process_events and finish_events:
            plt.plot([process_events[0]['time'], finish_events[0]['time']], [i, i], 'g-', linewidth=2)
        
        if lock_events:
            for event in lock_events:
                plt.plot([event['time']], [i], 'ro', markersize=6)
        
        if finish_events:
            plt.plot([finish_events[0]['time']], [i], 'ko', markersize=8)
    
    # Set y-ticks to thread IDs
    plt.yticks(range(len(thread_ids)), [f"RFC {tid.split('-')[1]}" for tid in thread_ids])
    plt.xlabel('Time (seconds)')
    plt.title('Thread Activity Timeline')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    plt.plot([], [], 'go', markersize=8, label='Thread Start')
    plt.plot([], [], 'b-', linewidth=2, label='Fetching Data')
    plt.plot([], [], 'g-', linewidth=2, label='Processing Data')
    plt.plot([], [], 'ro', markersize=6, label='Lock Acquisition')
    plt.plot([], [], 'ko', markersize=8, label='Thread Completed')
    plt.legend(loc='upper right')
    
    # Save the visualization
    plt.tight_layout()
    plt.savefig('thread_timeline.png')
    plt.close()
    
    # Create frequency visualization
    final_freq = next((event['frequency'] for event in reversed(data) if 'frequency' in event), {})
    sorted_freq = sorted(final_freq.items(), key=lambda x: x[1], reverse=True)
    
    plt.figure(figsize=(10, 6))
    letters, counts = zip(*sorted_freq)
    plt.bar(letters, counts, color='skyblue')
    plt.title('Letter Frequency Distribution')
    plt.xlabel('Letters')
    plt.ylabel('Frequency')
    plt.savefig('letter_frequency.png')
    plt.close()
    
    # Save data to CSV for further analysis
    with open('thread_events.csv', 'w', newline='') as csvfile:
        fieldnames = ['time', 'event', 'thread']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for event in data:
            if 'thread' in event and 'time' in event and 'event' in event:
                writer.writerow({
                    'time': event['time'],
                    'event': event['event'],
                    'thread': event['thread']
                })
    
    print(f"\nVisualization complete! Images saved as 'thread_timeline.png' and 'letter_frequency.png'")
    print(f"Thread event data saved to 'thread_events.csv' for further analysis")
    print(f"\nSummary:")
    print(f"- Execution Time: {execution_time:.2f} seconds")
    print(f"- Number of Threads: {len(thread_ids)}")
    print(f"- Lock Acquisitions: {len([e for e in data if e['event'] == 'lock_acquire'])}")

# Run the program and visualize
if __name__ == "__main__":
    print("Running letter counter with thread visualization...")
    data, execution_time = main_with_visualization()
    visualize_threads(data, execution_time)
