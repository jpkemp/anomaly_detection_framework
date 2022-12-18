# Python Anomaly Detection Framework
This repository contains an extract of a broader framework built to discover anomalous patterns among providers in MBS and PBS datasets, as part of an Industry PhD (IPhD) scholarship.<br/>
It was designed to allow rapid prototyping of anomaly detection processes, as well as providing flexibility of input data, and reproducibility and traceability through automated logging functions. <br/>
Implemented detection processes will be released alongside publication of papers describing the processes, as they occur. <br/>
Two processes are currently included:
• A sequence pattern detection process, presented at the Machine Learning and Artificial Intelligence in Bioinformatics and Medical Informatics workshop of the IEEE International Conference on Bioinformatics and Biomedicine 2022. <br/>
• A context discovery and cost estimation process, to be presented at HEALTHINF 2023. <br/>

## Structure
### Overview
The data analysis framework is set up as a module, with analyses specified in related test cases within sub-modules.

The code is split into two types within the src folder:<br/>
• The 'core' folder contains tools shared across analyses, such as logging, graphing, and file I/O. It also contains abstract classes describing how the  and a template for data analyses<br/>
• The 'analyses' folder contains the implemented anomaly detection processes, which extend the abstract classes from the code folder. Each analysis is separated into its own sub-module, and contains at minimum an implementation of the abstract analysis class, and a data extraction folder with an implementation of the abstract data extraction class. Each analysis includes its own README.md for further information. Output from each run of an analysis is located in the top-level 'Output' folder.<br/>

Parameters for each analysis are passed in when an analysis is run. Available parameters are established in the RequiredParams sub-class within each analysis file, and may be set either in the analysis file or in the analysis_runner file.

Analyses are run with analysis_runner.py in the top-level folder, which calls functions expected to exist as per the abstract classes for data extraction and analysis; while the actions of those functions is specified in the sub-modules of the analyses folder, the function definitions should remain the same.

### Data extraction
Medical claims datasets have millions of rows and many features. It is expected that a subset will be used for each analysis, as the class of problems each solves is not generally applicable to a whole dataset.
The framework expects each analysis folder to contain a 'data_extraction' folder, which contains scripts extending the abstract data extraction class. The scripts should contain code for extracting a data subset from the primary data source.
Loading previously extracted and processed data from a file is a possible alternative, which bypasses the extraction and processing steps.
In this case, data is expected to be stored in the top-level 'data' folder. <br/>

For the IPhD project, two data sources were used: a publicly released (now retracted) sample of 10% of patients in the Australian Medicare and Pharmaceutical Benefits Scheme (PBS); and the full, current versions of those sets of data stored at the Australian Government Department of Health.
The former was contained in parquet files, and was often used for prototyping even where the full set was used for the final publication.
Data from the latter was accessed using a custom wrapper for a Spark/Hadoop implementation. As the wrapper contains some sensitive information, it has been removed from the public release of this code.

## Software version compatibility
This code was built in Python 3.8.5 in Ubuntu 20.04.1 LTS.<br/>
Python package versions are documented in requirements.txt<br/>
Some external packages may be required. <br/>
-The 'sequence_detection' analysis relies on SPMF, available <a href=http://www.philippe-fournier-viger.com/spmf/>here</a>.<br/>
-Python's pygraphviz package depends on graphviz. Documentation for installing pygraphviz can be found <a href=https://pygraphviz.github.io/documentation/stable/install.html>here</a>.<br/>
-Construction of graph images can alternately be done with rpy2 and R's visnetwork package.

### Usage
• A config file must be set up with header information. This allows the same analysis to be used across different data sets with different headers, but which may have similar features. An example is given in example_config.json<br/>
• Test parameters, including the config file location and which data analysis file to run, should be specified in analysis_runner.py in the parent directory. Required parameters for an analysis can be found within the relevant file.<br/>
• The test can then be run with `python analysis_runner.py`<br/>

## Tests
Unit tests are located in the top-level 'tests' folder. They can be run within VSCode using the unittest framework or programmatically e.g. with the unittests script in the parent directory.

## Contact
Please contact me with any questions
<a href=https://au.linkedin.com/in/james-kemp-11874a93><img src=https://blog-assets.hootsuite.com/wp-content/uploads/2018/09/In-2C-54px-R.png
    width = 18 height = 15 /></a>
<a href=https://www.researchgate.net/profile/James_Kemp6><img src=https://www.researchgate.net/apple-touch-icon-180x180.png
    width=15 height=15 /></a>