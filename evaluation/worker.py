from rq import SimpleWorker

from evaluation.queue import evaluation_queue


if __name__ == "__main__":

    print("Ragas worker started...")

    worker = SimpleWorker(
        queues=[evaluation_queue],
        connection=evaluation_queue.connection
    )

    worker.work()