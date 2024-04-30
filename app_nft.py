import random
import threading
from queue import Queue
import requests
import urllib3
from progress.bar import IncrementalBar
from pyuseragents import random as random_useragent

urllib3.disable_warnings()

def load_proxies(fp: str = "prx.txt"):
    if fp == "": fp = "prx.txt"

    proxies = []
    with open(file=fp, mode="r", encoding="utf-8") as File:
        lines = File.read().split("\n")
    for line in lines:
        try:
            if line != "": proxies.append(f"http://{line}")
        except ValueError:
            pass

    if proxies.__len__() < 1:
        raise Exception("can't load empty proxies file!")

    print("{} proxies loaded successfully!".format(proxies.__len__()))

    return proxies

class PrintThread(threading.Thread):
    def __init__(self, queue, file):
        threading.Thread.__init__(self)
        self.queue = queue
        self.file = file

    def printfiles(self, addr, file):
        with open(file, "a", encoding="utf-8") as ff:
            ff.write(addr)

    def run(self):
        while True:
            addr = self.queue.get()
            self.printfiles(addr, self.file)
            self.queue.task_done()

class ProcessThread(threading.Thread):
    def __init__(self, in_queue, out_queue):
        threading.Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            addr = self.in_queue.get()
            response = self.func(addr)
            if response != "": self.out_queue.put(response)
            self.in_queue.task_done()

    def func(self, addr):
        profile_bal = {}
        profile_sum_bal = 0
        while True:
            try:
                sess = requests.session()
                proxie = random.choice(prox)
                if proxie == "": continue
                sess.proxies = {'all': proxie}
                sess.headers = {
                    'user-agent': random_useragent(),
                    'accept': 'application/json, text/plain, */*',
                    'origin': 'https://sonar.watch/',
                    'referer': 'https://sonar.watch/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'Authorization': 'Bearer v2MLnrwNSQ3tRd5PCKAGXzxupsZg6c',
                    'te': 'trailers'
                }
                sess.verify = False
                ss = sess.get(f'https://portfolio-api-public.sonar.watch/v1/portfolio/fetch?address={addr}&addressSystem=solana')
                status = ss.status_code
                if ss.json():
                    for el in ss.json()['elements']:
                        if el['value'] != None and el['value'] != 0 and el['platformId'] != None:
                            profile_sum_bal += el['value']
                            if el['platformId'] in profile_bal:
                                profile_bal[el['platformId']] += el['value']
                            else: profile_bal[el['platformId']] = el['value']
                if status == 200: 
                    break
            except Exception as e:
                pass
        bar.next()
        if profile_bal.__len__() > 0:
            profile = f'https://sonar.watch/portfolio/{addr} | TOKENS: {round(profile_sum_bal, 2)}'
            for key, value in profile_bal.items():
                profile += f" | {key}: {round(value, 2)}"
            return profile + "\n"
        return ""

prox = load_proxies(input('Path to proxies: '))
# prox = load_proxies("prx.txt")

file = input('Path to file with adr: ')
# file = 'adr.txt'

threads = int(input('Max threads: '))
# threads = 1

path_to_save = input('Path to save: ')
# path_to_save = "h123hhhhh.txt"

with open(file, encoding="utf-8") as f:
    mnemonics = f.read().splitlines()

print(f'Loaded {len(mnemonics)} address')
bar = IncrementalBar('Countdown', max=len(mnemonics))

print('started')

pathqueue = Queue()
resultqueue = Queue()

# spawn threads to process
for i in range(0, threads):
    t = ProcessThread(pathqueue, resultqueue)
    t.daemon = True
    t.start()

# spawn threads to print
t = PrintThread(resultqueue, path_to_save)
t.daemon = True
t.start()

# add paths to queue
for path in mnemonics:
    pathqueue.put(path)

# wait for queue to get empty
pathqueue.join()
resultqueue.join()
