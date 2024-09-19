# Experiments In Strategy Merging for the E Theorem Prover

These scripts assume you have `eprover` cloned within this repository,
although it is in the .gitignore file, so you must clone it yourself.
These scripts also all use `argparse`, so you can see all command line args with the `--help` flag. Add the `--higherOrder` flag if you want to use `eprover-ho` instead of `eprover`.

---

To test full (non-incremental) strategy merging for an existing set of problems:

```shell
python mergingExperiments.py --name="ExperimentNameGoesHere" \
    --problemsPath="path/to/problems" \
    --eArgs="--auto --soft-cpu-limit=60 --cpu-limit=65" \
    --numWorkers=4
```
`--auto` is included for the sake of presaturation interreduction,
while the actual strategy used for the main proof search is determined by a `--parse-strategy` flag that is injected later.

---


To test incremental strategy merging for a set of problems<br>
(These problems will be processed in alphabetic order):

```shell
python incrementalExperiments.py --name="ExperimentNameGoesHere" \
    --problemsPath="path/to/problems" \
    --useDataDir \
    --eArgs="--auto --soft-cpu-limit=60 --cpu-limit=65" \
    --numWorkers=4
```

---

To test E's normal `--auto` setup for comparison, run: <br>
(The only difference is the lack of `--useDataDir`)

```shell
python incrementalExperiments.py --name="ExperimentNameGoesHere" \
    --problemsPath="path/to/problems" \
    --eArgs="--auto --soft-cpu-limit=60 --cpu-limit=65" \
    --numWorkers=4
```

---

To compare experiments, it's easy to do from IPython or simply the python
command line interpreter:

```python
from incrementalExperiments import Experiment
Experiment.compareExperiments("ExperimentName1.results.pkl",
                              "ExperimentName2.results.pkl", 
                              ...)

```