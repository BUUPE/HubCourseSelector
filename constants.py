
# Lists are in no particular order
ALL_SEMESTER_CODES = ['2020-FALL', '2020-SUMM', '*']

REQUEST_HOST = 'www.bu.edu'
REQUEST_URL = 'https://www.bu.edu/phpbin/course-search/search.php'
REQUEST_DEFAULT_TIMEOUT_IN_SECONDS = 10

# Elements of PROBLEM_PARAMETERS are tuples of length 3.
# The first element is the file name to write the problem to.
# Each hub credit code is a string. It's the value of the param to search by on the BU course search page.
# The second element of these tuples is the columns. Each element of columns is a tuple of hub credit codes.
# Completing any credit in the tuple fulfills one unit in that category. This is the way to input requirements like "Social Inquiry II or Scientific Inquiry II."
# The third element is the credit_maxes vector, the number of credits required per category.
PROBLEM_PARAMETERS = []

# T for transfer students, F for first year students
# The number afterwards is the number of categories omitted. The full problems have number = 0. Number != 0 is for benchmarking performance.

# Real problems containing graduation requirements
PROBLEM_PARAMETERS += [('Problem/T0.txt', [(x,) for x in '1234'] + [('6', 'M')] + [('A', 'B', 'C')] + [('D', 'F')] + [('E', 'P')] + [('H',)] + [('I', 'J', 'K')], (1,) * 10)]
PROBLEM_PARAMETERS += [('Problem/F0.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ12346'], (1,) * 14 + (2,) * 6)]

# Smaller problems for benchmarking performance
PROBLEM_PARAMETERS += [('Problem/F1.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ1234'], (1,) * 14 + (2,) * 5)]		
PROBLEM_PARAMETERS += [('Problem/F2.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ123'], (1,) * 14 + (2,) * 4)]
PROBLEM_PARAMETERS += [('Problem/F3.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ12'], (1,) * 14 + (2,) * 3)]
PROBLEM_PARAMETERS += [('Problem/F4.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ1'], (1,) * 14 + (2,) * 2)]
PROBLEM_PARAMETERS += [('Problem/F5.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNOJ'], (1,) * 14 + (2,) * 1)]
PROBLEM_PARAMETERS += [('Problem/F6.txt', [(x,) for x in 'ABCDE'] + [('F', 'P')] + [(x,) for x in 'GHIKLMNO'], (1,) * 14)]

'''
There are constants in request_courses and read_downloaded_html in download_problems.py, but these likely do not need to be changed frequently.
'''