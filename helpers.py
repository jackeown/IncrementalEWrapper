import os, re, subprocess, pickle, math
from glob import glob
from collections import defaultdict, Counter

def runE(args, masterStratPath):
    executable = "eprover-ho" if args.higherOrder else "eprover"
    executable = f"./eprover/PROVER/{executable}"
    
    if masterStratPath is not None:
        eArgs = f"{args.eArgs} --parse-strategy={masterStratPath}"
    else:
        eArgs = args.eArgs
    subprocess.run(f"{executable} {eArgs} {args.problem}", shell=True)



def getProbStrat(problem, dataDir, higherOrder):
    probName = os.path.split(problem)[1]
    executable = "eprover-ho" if higherOrder else "eprover"
    executable = f"./eprover/PROVER/{executable}"
    
    eArgs = f"--auto --print-strategy"
    os.makedirs(f"{dataDir}/tmp", exist_ok=True)
    with open(f"{dataDir}/tmp/{probName}", "w") as f:
        subprocess.run(f"{executable} {eArgs} {problem}", shell=True, stdout=f)

    return parseStrat(f"{dataDir}/tmp/{probName}")





###### File Locking #########################################

def obtainLock(lock_path):
    try:
        # os.O_CREAT - Create file if it does not exist.
        # os.O_EXCL - Ensure atomic creation of the file.
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        # Write the current process PID to the lock file for reference
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    
    except FileExistsError:
        return False


def releaseLock(lock_path):
    try:
        os.remove(lock_path)
    except OSError:
        print("Error releasing lock!")





######## Actual Strategy merging ###########################

def parseStrat(stratFile):
    def parseKeyVal(k,v):
        if v == "true":
            return True
        elif v == "false":
            return False
        elif v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        else:
            try:
                return int(v)
            except:
                try:
                    return float(v)
                except:
                    return v
                
    def fixHeuristicDef(strat):
        if "heuristic_def" in strat:
            strat["heuristic_def"] = re.findall(r"([0-9]+)[.*](\w+\([^\)]*\))", strat["heuristic_def"])
            strat["heuristic_def"] = tuple(sorted([(int(w),f) for w,f in strat["heuristic_def"]]))


    with open(stratFile) as f:
        lines = f.readlines()
        lines = [l for l in lines if not l.startswith("#") and len(l.strip()) > 1 and ":" in l]

    strat = {k.strip():v.strip() for k,v in [l.split(":") for l in lines]}
    assert len(strat) == len(lines) # There should be no duplicate keys.

    for k,v in strat.items():
        strat[k] = parseKeyVal(k,v)
    
    fixHeuristicDef(strat)

    return strat

def loadStratHistory(dataDir):
    stratHist = defaultdict(Counter)
    stratHistPath = f"{dataDir}/strat_history.pkl"
    if os.path.exists(stratHistPath):
        with open(stratHistPath, "rb") as f:
            stratHist = pickle.load(f)
            
    return stratHist

def updateStratHistory(hist, newStrat):
    for k,v in newStrat.items():
        hist[k][v] += 1

    return hist

def saveStratHistory(hist, dataDir):
    stratHistPath = f"{dataDir}/strat_history.pkl"
    with open(stratHistPath, "wb") as f:
        pickle.dump(hist, f)

def makeMasterFromHistory(hist, dataDir, toFile=True):
    masterStratPath = f"{dataDir}/MASTER.{os.getpid()}.strat"
    master = makeMasterStrat(hist, all_ones=False)
    if toFile:
        with open(masterStratPath, "w") as f:
            f.write(serializeStrat(master))
        return masterStratPath
    else:
        return master






######## Implementation of strategy merging ######################

def makeMasterHeuristic(counter: Counter, all_ones: bool):
    maxCEFWeight = 20

    master = defaultdict(lambda:0)
    for CEFs, probCount in counter.items():
        for weight, CEF in CEFs:
            master[CEF] += weight * probCount

    # Scale the weights so that the max weight is maxCEFWeight.
    scalingFactor = maxCEFWeight / max(master.values())
    for k,v in master.items():
        master[k] = math.ceil(v*scalingFactor)

    d = sorted([(v,k) for k,v in master.items()], key=lambda x:x[0], reverse=True)
    if all_ones:
        d = [(1,k) for _,k in d]

    return d


def makeMasterStrat(summary, all_ones, instead=None, keepCommon="heuristic"):
    # Make a master strategy that is the most common value for each key, except for heuristic_def
    # where we call makeMasterHeuristic.
    master = {}
    
    assert keepCommon in ["heuristic", "else"]

    if keepCommon == "heuristic":
        for k,counter in summary.items():
            if k == "heuristic_def":
                master[k] = makeMasterHeuristic(counter, all_ones)
            else:
                master[k] = counter.most_common(1)[0][0] if instead is None else instead[k]

    else:
        for k,counter in summary.items():
            if k == "heuristic_def":
                master[k] = makeMasterHeuristic(counter, all_ones) if instead is None else instead[k]
            else:
                master[k] = counter.most_common(1)[0][0]

    return master





################### Serialization functions ######################

def unparse(k,v):
    if isinstance(v, bool):
        return "true" if v else "false"
    elif isinstance(v, str) and v=="" or k =='sine':
        return f'"{v}"'
    else:
        return str(v)
    
def serializeStrat(summary):
    # Need to convert types back to strings (undoing what parseStrat did)
    # Also need to convert heuristic_def back to a string.

    for k,v in list(summary.items()):
        if k == "heuristic_def":
            l = []
            for _, (weight, cef) in enumerate(v):
                l.append(f"{weight}.{cef}")
            summary[k] = '"(' + ",".join(l) + ')"'
        else:
            summary[k] = unparse(k,v)
    
    s = "{\n   {\n"
    indentLevel=2
    for k,v in summary.items():
        if k == "no_preproc":
            indentLevel = 1
            s += "   }\n"
        s += indentLevel*"   " + f"{k}:  {v}\n"
    s += "}"

    return s
