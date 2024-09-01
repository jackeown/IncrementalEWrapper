#!/usr/bin/env python3

# This script is meant to wrap eprover for use within Isabelle's Sledgehammer:
# 1.) It decides whether to run eprover or eprover-ho based on the provided file, $PROBLEM.
# 2.) It will run using --auto (or --auto-schedule if specified) unless...
# 3.) The SLH_PERSISTENT_DATA_DIR environment variable is set, in which case...:
#      a.) E will be run using --auto and --print-strategy with output to $SLH_PERSISTENT_DATA_DIR/tmp/$PROBLEM.
#      b.) The saved strategy from step 3.a. will be used to update a file "$SLH_PERSISTENT_DATA_DIR/strat_history.pkl":
#          - containing the counts for every strategy key so that computing 3.c. doesn't require looping over all strategies.
#      c.) strat_history.pkl will be used to compute $SLH_PERSISTENT_DATA_DIR/MASTER.pid.strat
#      d.) All of this must be done with locking.
#          - Lock before 3.b. and unlock after 3.c.
# 4.) All learning can be reset then by deleting the file "$SLH_PERSISTENT_DATA_DIR/strat_history.pkl"
# 5.) The MASTER.pid.strat files are passed to E, but can be deleted immediately after use.
#     - Same with the $SLH_PERSISTENT_DATA_DIR/tmp/$PROBLEM file.

import os
import argparse

from helpers import runE, getProbStrat, \
    loadStratHistory, updateStratHistory, saveStratHistory, makeMasterFromHistory, \
    obtainLock, releaseLock


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("problem")
    parser.add_argument("--eArgs", default="")
    parser.add_argument("--higherOrder", action="store_true")

    args = parser.parse_args()

    if os.environ.get("SLH_PERSISTENT_DATA_DIR") is not None:
        print("Running E with persistent data")
        dataDir = os.environ["SLH_PERSISTENT_DATA_DIR"]
        lockPath = f"{dataDir}/lockfile"
        newStrat = getProbStrat(args.problem, dataDir, args.higherOrder) # Saves to $SLH_PERSISTENT_DATA_DIR/tmp/$PROBLEM

        obtainLock(lockPath)
        stratHist = updateStratHistory(loadStratHistory(dataDir), newStrat) # 3.b.
        saveStratHistory(stratHist, dataDir)                                # 3.b. 
        masterStratPath = makeMasterFromHistory(stratHist, dataDir)         # 3.c.
        releaseLock(lockPath)

        runE(args, masterStratPath)
    else:
        print("Running E without persistent data")
        runE(args, None)
