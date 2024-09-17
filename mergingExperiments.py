import argparse
from glob import glob
from rich.progress import Progress, track
from helpers import getProbStrat, updateStratHistory, makeMasterFromHistory
from collections import defaultdict, Counter
from incrementalExperiments import Experiment
import os
from multiprocessing import Pool

# Ensure getProbStrat is picklable
def process_file(args):
    p, dataDir, higherOrder = args
    probName = os.path.split(p)[1]
    strat = getProbStrat(p, dataDir, higherOrder)
    return (probName, strat)

def getMasterStrat(args):
    dataDir = f"{args.problemsPath}/data_dir"
    file_list = glob(f"{args.problemsPath}/*.p")
    higherOrder = args.higherOrder

    # Prepare list of arguments for multiprocessing
    args_list = [(p, dataDir, higherOrder) for p in file_list]
    results = []

    with Progress() as progress:
        task_id = progress.add_task("Getting strategies", total=len(args_list))

        with Pool(processes=args.numWorkers) as pool:
            for result in pool.imap_unordered(process_file, args_list):
                results.append(result)
                progress.advance(task_id)

    # Collect strategies into a dictionary
    strats = dict(results)

    # Update strategy history
    stratHistory = defaultdict(Counter)
    for p, strat in track(strats.items(), description="Updating strategy history"):
        updateStratHistory(stratHistory, strat)

    return makeMasterFromHistory(stratHistory, dataDir)







if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("problemsPath")
    parser.add_argument("--higherOrder", action="store_true")
    parser.add_argument("--eArgs", default="")
    parser.add_argument("--numWorkers", type=int, default=4)
    args = parser.parse_args()

    masterStratPath = getMasterStrat(args)

    exp = Experiment(
        name=args.name,
        path=args.problemsPath,
        higherOrder=args.higherOrder,
        problems=glob(f"{args.problemsPath}/*.p"),
        eArgs=f"--parse-strategy={masterStratPath} {args.eArgs}",
        useDataDir=False,
    )

    exp.run(numWorkers=args.numWorkers)
