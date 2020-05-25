# CourseSelector

The main programs are a web scraper for the BU course search page and algorithms that compute sets of courses that fulfill given sets of unfulfilled hub requirements.

| File | Description |
| :--- | :--- |
| README.md | This file. |
| AlgorithmDescription.txt | Discussion about the main algorithmic problem to solve, the nature of the problem, and the implemented algorithms to solve the problem. |
| ProblemComplexity.txt | Upper and lower bounds on complexity of various generalized versions of the main algorithmic problem. |
| CourseInfoScraping.txt | Description of the BU course search page scraper and instructions on changing the request headers and params in case the page changes. |
| VectorProblemFormat.txt | Description of the vector problem file format, which encodes the hub units each course fulfills and the graduation requirements. |
| FutureFeatures.txt | A list of features or improvements that can be added to this project. |
| vector\_operations.py | Library of some vector operations used by the algorithm. |
| constants.py | The constants that need to be changed most frequently (every semester). |
| download\_problems.py | Scrapes the BU course search page and writes information to vector problem files. |
| algo.py | A fast algorithm that computes sets of courses from vector problem files that fulfill exactly credit_maxes. |
| algo2.py | A slow, complete algorithm that computes sets of courses from vector problem files that fulfill any given subvector of credit\_maxes. |
| algo3.py | algo2.py but 5x slower and writes tables to a file. |
| benchmark_results.txt | List of running times for different problem sizes.

download_problems.py will write files for the vector problems outlined by the constants in constants.py. Run this file by running `python download_problems.py` in terminal.

algo.py will read a vector problem file and compute sets of courses based on the vector problem.
Run this file by running `python algo.py filename` in terminal, where filename is the file name of the vector problem file.
algo2.py is run in the same way.

Python programs were developed and tested on python 3.6.5.
Although the code is littered with assertions, it may not be the case that all relevant true statements have been asserted or that all assertions are always true.
