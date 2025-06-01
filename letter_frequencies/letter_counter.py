import json
from threading import Thread, Lock
import urllib.request
import time

finished_count = 0


def count_letters(url, frequency, lock: Lock):
    response = urllib.request.urlopen(url)
    txt = str(response.read())
    lock.acquire()
    for letter in txt:
        letter = letter.lower()
        if letter in frequency:
            frequency[letter] += 1
    global finished_count
    finished_count += 1
    lock.release()


def main():
    frequency = {}
    lock = Lock()
    for c in "abcdefghijklmnopqrstuvwxyz":
        frequency[c] = 0
    start = time.time()
    for i in range(1000, 1020):
        Thread(
            target=count_letters,
            args=(f"https://www.rfc-editor.org/rfc/rfc{i}.txt", frequency, lock),
        ).start()
    while True:
        lock.acquire()
        if finished_count == 20:
            lock.release()
            break
        lock.release()
        time.sleep(0.05)
    end = time.time()
    print(json.dumps(frequency, indent=4))
    print("Done, time taken", end - start)


main()
