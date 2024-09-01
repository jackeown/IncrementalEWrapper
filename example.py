from multiprocessing import Manager, Pool
from random import randint
from time import sleep

def waitForWorkers(asyncResults):
    while any(not r.ready() for r in asyncResults):
        sleep(0.1)


def runJob(jobName, successMap):
    print(f"Running job {jobName}")
    result = randint(0, 100) > 50
    successMap[jobName] = result
    return result


class Example:
    def __init__(self, jobs):
        self.jobNames = jobs
        self.manager = Manager()
        self.successMap = self.manager.dict()
    
    def runJobs(self, jobs):
        tasks = []
        with Pool(4) as p:
            for i, job in enumerate(jobs):
                task = p.apply_async(runJob, args=(job,self.successMap ))
                tasks.append(task)
                # Check and wait for the completion of tasks at every 10th job submission
                if (i + 1) % 10 == 0:
                    waitForWorkers(tasks)
            # Final check to ensure all tasks have completed
            waitForWorkers(tasks)
        print("Finished!")

if __name__ == "__main__":
    jobs = ["job_{}".format(i) for i in range(100)]
    e = Example(jobs)
    e.runJobs(jobs)
    print(e.successMap)
