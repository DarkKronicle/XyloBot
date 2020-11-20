import asyncio
import nest_asyncio


class QueueProcess:
    """
    Helper class for easily doing stuff inside and outside of the queue.
    """

    def __init__(self, queue):
        self.queue = queue

    async def __aenter__(self):
        await self.queue.wait_until_complete()
        self.queue.occupied = True

    async def __aexit__(self, *args):
        self.queue.occupied = False


class SimpleQueue:
    """
    A class for only allowing a certain process to be running at once. Useful for limiting api calls to once every half
    second.
    """

    def __init__(self, sleep_for, *, refresh=0.1):
        self.occupied = False
        self.sleep_for = sleep_for
        self.waiting = []
        self.running = False
        self.refresh = refresh

    async def loop(self):
        self.running = True
        while self.running:
            if not self.occupied:
                await asyncio.sleep(self.sleep_for)
                self.waiting.pop(0)
                if len(self.waiting) == 0:
                    self.running = False
                    break
                self.occupied = True
            await asyncio.sleep(0.1)

    async def wait_until_complete(self):
        key = self.get_key()
        self.waiting.append(key)
        print(str(key))
        if not self.running:
            self.running = True
            asyncio.new_event_loop().create_task(self.loop())
        while True:
            if key not in self.waiting:
                return
            await asyncio.sleep(self.refresh)

    def get_key(self):
        for i in range(1000):
            if i not in self.waiting:
                return i
        raise IndexError("There are too many objects in the queue!")
