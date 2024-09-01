import argparse
import pickle as pkl
from glob import glob
from multiprocessing import Pool, Manager
from rich.progress import Progress, track
import subprocess
from collections import defaultdict
from time import sleep, time
import re


# args = environmentVars, prob, eArgs
proverTemplate = "{} python incrementalEWrapper.py {} --eArgs='{} -l2'"

safePercent = lambda a,b: "undefined" if b == 0 else round(100*a/b,2)


def waitForWorkers(asyncResults, numWorkers):
    while sum(1 for r in asyncResults if not r.ready()) > numWorkers:
        sleep(0.1)

    asyncResults = [r for r in asyncResults if not r.ready()]
    return asyncResults


def runE(useDataDir, eArgs, problem, successMap, procCountMap):
    environmentVars = "SLH_PERSISTENT_DATA_DIR=data_dir" if useDataDir else ""
    command = proverTemplate.format(environmentVars, problem, eArgs)
    # print(command)
    p = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # check SZS status:
    stdout = p.stdout.decode("utf-8")
    if "SZS status Theorem" in stdout:
        print("Solved")
        successMap[problem] = True
        # Extract number of processed clauses from a line like this:
        # "# Processed clauses                    : 5337"
        numProcessed = re.search(r"# Processed clauses                    : (\d+)", stdout).group(1)
        procCountMap[problem] = int(numProcessed)
    else:
        print("Failed")
        successMap[problem] = False



class Experiment:

    def __init__(self, name, path, higherOrder, problems, eArgs, useDataDir):
        self.name = name
        self.path = path
        self.higherOrder = higherOrder
        self.problems = problems # set of problem paths

        self.manager = Manager()
        self.successMap = self.manager.dict()
        self.procCountMap = self.manager.dict()

        self.eArgs = eArgs
        self.finished = False
        self.useDataDir = useDataDir

    @staticmethod
    def load(path):
        with open(path, "rb") as f:
            obj = pkl.load(f)

        # Reinitialize the Manager and assign loaded data to managed dictionaries
        obj.manager = Manager()
        obj.successMap = obj.manager.dict(obj.temp_successMap)
        obj.procCountMap = obj.manager.dict(obj.temp_procCountMap)

        # Cleanup temporary attributes if they were stored
        del obj.temp_successMap, obj.temp_procCountMap

        return obj

    def save(self):
        # Temporarily replace manager dictionaries with regular dictionaries for pickling
        temp_successMap = dict(self.successMap)
        temp_procCountMap = dict(self.procCountMap)

        # Temporarily unset the manager dictionaries in self
        self.successMap, self.procCountMap = None, None

        # Save the instance of Experiment without Manager attributes
        with open(f"{self.name}.results.pkl", "wb") as f:
            pkl.dump(self, f)

        # Restore the managed dictionaries
        self.successMap = self.manager.dict(temp_successMap)
        self.procCountMap = self.manager.dict(temp_procCountMap)

        
    def __repr__(self):
        solved = len({k for k in self.successMap.keys() if self.successMap[k]})
        return f"""
#########################################################
Experiment: {self.name}
Path: {self.path}
Higher Order: {self.higherOrder}
Attempted: {len(self.successMap)} / {len(self.problems)} ({safePercent(len(self.successMap),len(self.problems))}%)
Solved: {solved} / {len(self.successMap)} ({safePercent(solved,len(self.successMap))}%)
eArgs: "{self.eArgs}"
Finished: {self.finished}
useDataDir: {self.useDataDir}
Average processed clauses: {sum(self.procCountMap.values()) / max(len(self.procCountMap),1):.2f}
"""
    
    def run(self, numWorkers=4):

        # problem files are formatted like:
        # timestamp_random_prob_id_sequentialIgnore.p
        # e.g. 20240720T040828_808bb49e_prob_E6AE79D3445F7F0A_133872092_1.p
        # There are multiple files for the same problem:
        # 20240720T040828_485393dd_prob_E6AE79D3445F7F0A_133859110_1.p
        # 20240720T040828_641057b4_prob_E6AE79D3445F7F0A_133855720_1.p
        # 20240720T040828_710d9d07_prob_E6AE79D3445F7F0A_133862682_1.p
        # ...

        # group problems by problem id
        getProbId = lambda p: p.split("_prob_")[1].split("_")[0] # should work with full path or just filename
        probGroups = defaultdict(list)
        for p in track(self.problems, description="Grouping"):
            probGroups[getProbId(p)].append(p)

        groupsAttempted = set()
        with Pool(numWorkers) as p:
            tasks = []
            t1 = time()
            for i, problem in enumerate(track(self.problems, description="Running")):
                tasks.append(p.apply_async(runE, args=(self.useDataDir, self.eArgs, problem, self.successMap, self.procCountMap)))
                groupsAttempted.add(getProbId(problem))

                tasks = waitForWorkers(tasks, numWorkers)

                if i % 20 == 0:
                    minsElapsed = (time() - t1) / 60
                    attemptsPerMin = i / minsElapsed
                    if attemptsPerMin > 0:
                        leftToAttempt = len(self.problems) - i
                        minsLeft = leftToAttempt / attemptsPerMin
                        print(f"{attemptsPerMin:.2f} attempts/min (Hours remaining: {round(minsLeft / 60, 2)})")
                    
                    
                    numSolved = len({k for k in self.successMap.keys() if self.successMap[k]})
                    print(f"{i} / {len(self.problems)} attempted ({numSolved} solved)")

                    successGroups = {getProbId(k) for k in self.successMap.keys() if self.successMap[k]}
                    attemptedGroups = {getProbId(k) for k in self.successMap.keys()}
                    print("{} / {} groups have successful attempts ({}%)".format(
                        len(successGroups), 
                        len(attemptedGroups), 
                        safePercent(len(successGroups), len(attemptedGroups))
                    ))

                    print(self)

        self.finished = True
        self.save()








if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("problemsPath")
    parser.add_argument("--useDataDir", action="store_true")
    parser.add_argument("--higherOrder", action="store_true")
    parser.add_argument("--eArgs", default="")
    parser.add_argument("--numWorkers", type=int, default=4)
    args = parser.parse_args()

    exp = Experiment(args.name, args.problemsPath, args.higherOrder, glob(f"{args.problemsPath}/*.p"), args.eArgs, args.useDataDir)
    exp.run(numWorkers=args.numWorkers)