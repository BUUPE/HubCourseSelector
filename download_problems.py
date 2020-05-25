import requests  # http requests to the BU course search page
import re  # Regular expressions parsing

import time
import datetime
import os

from constants import ALL_SEMESTER_CODES, REQUEST_HOST, REQUEST_URL, REQUEST_DEFAULT_TIMEOUT_IN_SECONDS, PROBLEM_PARAMETERS

'''
Makes an http request to the BU course search page and returns the page's html.

This requires internet access.

If the request times out but you have internet access and can access the BU Hub
course search through the browser, try increasing request_timeout_limit.
'''
def request_courses(semester_code, hub_code, timeout = REQUEST_DEFAULT_TIMEOUT_IN_SECONDS):
	headers = {
		'Accept' : 'text/html',
		'Accept-Encoding': 'gzip, deflate, br',
		'Accept-Language': 'en-US,en;q=0.9',
		'DNT': '1',
		'Host': REQUEST_HOST,
		'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
	}
	params = {
		'page': 'w0',
		'pagesize': -1,
		'showdesc': 'Show',
		'adv': '1',
		'nolog': '',
		'search': '',
		'yearsem': semester_code,
		'search_adv_all': '',
		'search_adv_phrase': '',
		'search_adv_exclude': '',
		'yearsem_adv': semester_code,
		'credits': '*',
		'hub_match': 'all',
		'hub[]': hub_code,
	}

	print('downloading {:s} {:s}'.format(semester_code, hub_code))
	r = requests.get(REQUEST_URL, headers=headers,params=params, timeout=timeout)
	r = r.text
	return r

'''
Reads the html produced by request_courses, extracts the course information using regex,
and returns a list of dictionaries, where each dictionary contains the information
about a course.

The returned dictionaries have the following keys:
College
Department
Course Number
Title
Prereq
Grad Prereq
Coreq
Grad Coreq
Description
Credits
'''
def read_downloaded_html(html):
	# Regex pattern to read the html of the search result page and capture a course's information
	course_result_pattern = r'<li class="coursearch-result" id="coursearch-result-([A-Z]{3})([A-Z]{2})(\d{3})">\n[ \t]+<div class="coursearch-result-content">\n[ \t]+<div class="coursearch-result-heading">\n[ \t]+<h6>\1 \2 \3</h6>\n[ \t]+<h2>([^\n]*)</h2>\n[ \t]+</div>\n[ \t]*\n[ \t]+<div class="coursearch-result-content-description">\n[ \t]*\n[ \t]+<p>((?:Prereq: [^\n]*<br />)?)</p>\n[ \t]*\n[ \t]+<p>((?:Grad Prereq: [^\n]*<br />)?)</p>\n[ \t]*\n[ \t]+<p>((?:Coreq: [^\n]*<br />)?)</p>\n[ \t]*\n[ \t]+<p>((?:Grad Coreq: [^\n]*<br />)?)</p>\n[ \t]*\n[ \t]*\n[ \t]+<p>([^\n]*)</p>\n[ \t]+<p>([^\n]+)</p>\n(?:[ \t]*|[ \t]+Offered:[^\n]+<br /><br />)\n[ \t]+</div>\n[ \t]+</div>'

	results = re.findall(course_result_pattern, html)
	
	# Ensure that our html parser finds as many results as returned by the site's search.
	searches_found_pattern = 'returned <strong>(\d+)</strong> classes'
	searches_found_result = re.search(searches_found_pattern, html)
	assert searches_found_result is not None
	# print('Found {:d} results but was given {:d} results'.format(len(results), int(searches_found_result.expand(r'\1'))))
	assert int(searches_found_result.expand(r'\1')) == len(results)

	# Converts elements of re.findall(course_result_pattern, ...) to dictionaries.
	# TODO: Clean up the values of prereqs
	def regex_match_to_course(item):
		return {
			'College': item[0],
			'Department': item[1],
			'Course Number': item[2],
			'Title': re.sub(r'[ \n]+', ' ', item[3]),
			'Prereq': re.sub(r'[ \n]+', ' ', item[4]),
			'Grad Prereq': re.sub(r'[ \n]+', ' ', item[5]),
			'Coreq': re.sub(r'[ \n]+', ' ', item[6]),
			'Grad Coreq': re.sub(r'[ \n]+', ' ', item[7]),
			'Description': re.sub(r'[ \n]+', ' ', item[8]),
			'Credits': item[9].strip('[]').strip(' '),
		}

	results_as_dicts = list(map(regex_match_to_course, results))
	# for x in results_as_dicts:
		# print()
		# for k, v in x.items():
			# print(k, v)
	return results_as_dicts

'''
This uses request_courses, which makes an internet connection and downloads the html.
This function takes in the graduation requirements (eg first years or transfers) and gathers all the hub course information and writes out the vector problem.

If there are more courses that fulfill the same set of units than the number of each unit required, then the excess duplicate vectors are not listed.
'''
def write_problem(output_file_name, semester_codes, credit_maxes, hub_columns):
	start = time.time()
	
	if isinstance(semester_codes, list):
		semester_codes = tuple(semester_codes)
	if isinstance(credit_maxes, list):
		credit_maxes = tuple(credit_maxes)
	if isinstance(hub_columns, list):
		hub_columns = tuple(hub_columns)
	
	assert isinstance(output_file_name, str)
	
	assert isinstance(semester_codes, tuple)
	for x in semester_codes:
		assert isinstance(x, str)
	
	assert isinstance(credit_maxes, tuple)
	assert len(credit_maxes) == len(hub_columns)
	
	assert isinstance(hub_columns, tuple)
	for hub_codes in hub_columns:
		assert isinstance(hub_codes, tuple)
		for code in hub_codes:
			assert isinstance(code, str)
	
	# Assert no duplicate hub codes
	assert len(set([y for x in hub_columns for y in x])) == len([y for x in hub_columns for y in x])
	
	print('assertions took {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	# Gather course vectors
	course_to_vector = dict()
	for semester_code in semester_codes:
		for hub_credit_index, hub_codes in enumerate(hub_columns):
			for hub_code in hub_codes:
				html = request_courses(semester_code, hub_code)
				course_infos = read_downloaded_html(html)
				for course_info in course_infos:
					# Courses are indexed by (college, dept, num)
					course = (course_info['College'], course_info['Department'], course_info['Course Number'])
					
					if course not in course_to_vector:
						course_to_vector[course] = [0] * len(hub_columns)
					course_to_vector[course][hub_credit_index] = 1

	print('building vectors took {:.2f} seconds'.format(time.time() - start))
	start = time.time()
	
	# Remove extra vectors if there exist more equal vectors than the max of that vector.
	vec_count = dict()
	for course in course_to_vector:
		key = tuple(course_to_vector[course])
		if key not in vec_count:
			vec_count[key] = 0
		vec_count[key] += 1
	for vec in vec_count:
		dot_product = [a * b for a, b in zip(vec, credit_maxes)]
		highest_requirement_of_fulfilled = max(dot_product)
		if vec_count[vec] > highest_requirement_of_fulfilled:
			vec_count[vec] = highest_requirement_of_fulfilled
	
	# Make directory of write location
	try:
		os.makedirs(os.path.dirname(output_file_name))
	except FileExistsError:
		pass
		
	# Write to file
	with open(output_file_name, 'w') as f:
		f.write('3\n')
		f.write('date generated: {!s:s}\n'.format(datetime.datetime.now()))
		f.write('columns: {!s:s}\n'.format(hub_columns))
		f.write('semester codes: {!s:s}\n'.format(semester_codes))
		f.write('{:d}\n'.format(len(hub_columns)))
		f.write('{:d}\n'.format(sum(vec_count.values())))
		f.write(' ' * 5 + ' '.join(map(str, credit_maxes)))
		f.write('\n')
		vector_id = 0
		for vec in sorted(vec_count.keys()):
			for _ in range(vec_count[vec]):
				f.write('{:4d} '.format(vector_id) + ' '.join(map(str, vec)))
				f.write('\n')
				vector_id += 1

	print('writing vectors to file took {:.2f} seconds'.format(time.time() - start))
	start = time.time()

# Import this where the course vectors and credit_maxes vector has to be extracted from a file.
# TODO: possibly include vector id in return value.
def read_problem(input_file_name):
	# Read files into strings
	with open(input_file_name, 'r') as f:
		content = f.readlines()
		
		content = map(lambda x: x.strip(), content)
		content = list(content)
		
		A = int(content[0])
		M = int(content[A + 1])
		N = int(content[A + 2])
		
		string_to_vector = lambda x: tuple(map(int, re.sub(' +', ' ', x.strip(' ')).split(' ')))
		
		credit_maxes = string_to_vector(content[A + 3])
		assert len(credit_maxes) == M
		
		vectors = [None] * N
		for i in range(N):
			ints_on_line = string_to_vector(content[A + 4 + i])
			vector_id = ints_on_line[0]
			assert vector_id == i
			vectors[i] = ints_on_line[1:]
			assert len(vectors[i]) == M
		vectors = tuple(vectors)

	return credit_maxes, vectors

# request_courses uses cached values
def table_decorator(func):
	table = dict()
	def wrapper(a, b):
		if (a, b) not in table:
			table[(a, b)] = func(a, b)
		return table[(a, b)]
	return wrapper
request_courses = table_decorator(request_courses)

# Run your programs!
# Writes the course vectors to a file.
if __name__ == '__main__':
	for file_name, columns, credit_maxes in PROBLEM_PARAMETERS:
		write_problem(file_name, ALL_SEMESTER_CODES, credit_maxes, columns)