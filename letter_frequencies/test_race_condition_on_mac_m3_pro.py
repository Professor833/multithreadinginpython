import threading
import time
import json
import random

frequency = {c: 0 for c in "abcdefghijklmnopqrstuvwxyz"}
finished_count = 0
lock = threading.Lock()


def count_letters(text):
    global finished_count
    for letter in text:
        letter = letter.lower()
        if letter in frequency:
            # Simulate race-prone read-modify-write
            val = frequency[letter]
            time.sleep(random.uniform(0.00001, 0.0001))  # create race condition window
            frequency[letter] = val + 1

    with lock:
        finished_count += 1


def main():
    num_threads = 100
    dummy_text = "hello world abcdefghijklmnopqrstuvwxyz" * 1000
    threads = []

    for _ in range(num_threads):
        t = threading.Thread(target=count_letters, args=(dummy_text,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(json.dumps(frequency, indent=4))
    print("Total letters counted:", sum(frequency.values()))
    print("Expected total:", len(dummy_text) * num_threads)


main()
