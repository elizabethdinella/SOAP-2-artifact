## On the Effectiveness of Modular Testing with EvoSuite

This repository contains the artifact for evaluation of 

[On the Effctiveness of Modular Testing with EvoSuite]

Our modification to EvoSuite (MUSE) can be found [here](https://github.com/elizabethdinella/evosuite), but the built jar is included in this repository.

This repository contains:
1. Target benchmark jars (First five projects of SF100)
2. EvoSuite jars (plain EvoSuite 1.1.0 and EvoSuite with our proposed modification for modular testing)
3. Evaluation scripts

To reproduce the evaluation:
First run the `setup.sh` script to expand the SF100 jar files.
Next, run `run_evo.sh` modify the flags for which EvoSuite jar to use (`OG`) and which target project to generate tests for (`proj`).
The script will execute EvoSuite in modular testing mode for each method in the given project. 

Prerequisites are included in the Dockerfile. If you wish to run without docker, ensure you have the following requirements:
- java 11.0.11
- python3

