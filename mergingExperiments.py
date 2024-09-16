import argparse
from glob import glob
from rich.progress import track
from helpers import getProbStrat, updateStratHistory, makeMasterFromHistory
from collections import defaultdict, Counter
from incrementalExperiments import Experiment
import os

import IPython
# track = lambda x,*args,**kwargs: x # for debugging


def getMasterStrat(args):
    strats = {}
    dataDir = f"{args.problemsPath}/data_dir"
    for p in track(glob(f"{args.problemsPath}/*.p"), description="Getting strategies"):
        probName = os.path.split(p)[1]
        strats[probName] = getProbStrat(p, dataDir, args.higherOrder)
    
    stratHistory = defaultdict(Counter)
    for p,strat in track(strats.items(), description="Updating strategy history"):
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

    masterStratPath = getMasterStrat(args.problemsPath, args)

    exp = Experiment(name=args.name,
                     path=args.problemsPath,
                     higherOrder=args.higherOrder,
                     problems=glob(f"{args.problemsPath}/*.p"),
                     eArgs=f"--parse-strategy={masterStratPath} {args.eArgs}",
                     useDataDir=False)

    exp.run(numWorkers=args.numWorkers)


