from collections import deque
import time
import sys
import random

from vector_operations import vector_sub, non_pos, all_subvectors_of
from download_problems import read_problem

# Input: the credit_maxes and vectors of the vector problem
# Return: A function that takes as input zero arguments and returns a set of courses that fulfills credit_maxes
# TODO: The vectors were sorted, so they are not in the same order as the input order. Make something so that the return value makes sense with the vectors in the order from the input.
# TODO: Change return value to vectors selected or course codes selected.
def make_query_function(credit_maxes, vectors):
	start = time.time()

	assert isinstance(credit_maxes, tuple), 'The credits vector was a non-tuple'
	for x in credit_maxes:
		assert isinstance(x, int), 'A credits value was a non-int'
		assert 1 <= x, 'A credits value was not 0 or 1'

	assert isinstance(vectors, tuple), 'The list of vectors was a non-tuple'
	assert 1 <= len(vectors), '0 vectors were provided'

	for v in vectors:
		assert isinstance(v, tuple), 'A vector was a non-tuple'

	for v in vectors:
		assert len(v) == len(credit_maxes), 'Vectors differ in length'

	for v in vectors:
		for x in v:
			assert isinstance(x, int), 'A vector value was a non-int'
			assert x == 0 or x == 1, 'A vector value was not 0 or 1'

	print('Assertions on input took {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	# Sort vectors
	vectors = sorted(vectors, reverse = True)
	print('Sorting vectors took {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	# Computation path priority queue
	# new_queue[unfulfilled_credits] = minimal subset (by key = lambda x: (len(x), x[-1])) of vectors seen that leaves exactly unfulfilled_credits unfulfilled and should be recursed on
	new_queue = dict()
	new_queue[credit_maxes] = []

	# table1[unfulfilled_credits] = size of least set (according to the order) that leaves exactly unfulfilled_credits unfulfilled
	# table2[unfulfilled_credits] = max of that least set
	# values are of all subsets seen.
	# unfulfilled_credits == credit_maxes is an exception to the above statements
	table1 = dict()
	table2 = dict()
	table1[credit_maxes] = 0

	# Computation status
	processed_nodes = 0

	# Print status
	print('we have {:d} vectors, each of length {:d}'.format(len(vectors), len(vectors[0])))
	print('we must fulfill credits {!s:s}'.format(credit_maxes))
	print('building the input required {:.2f} seconds'.format(time.time() - start))
	
	right_bounds = [0] * len(credit_maxes)
	i = 0
	for j in range(len(credit_maxes)):
		while i < len(vectors) and vectors[i][j] == 1:
			i += 1
		right_bounds[j] = i
	
	start = time.time()

	# Computation loop
	while len(new_queue) > 0:
		# Progress priority queue
		old_queue = new_queue
		new_queue = dict()

		for credits_required, selected_vectors in old_queue.items():
			# Print computation status
			if processed_nodes % 1000 == 0:
				print('Processed nodes:', processed_nodes)
			processed_nodes += 1

			# Extract node from queue
			len_selected_vectors = len(selected_vectors)
			assert not non_pos(credits_required)

			# Select classes in order
			if len_selected_vectors == 0:
				left_bound = 0
			else:
				left_bound = selected_vectors[-1] + 1

			# Break when the set of all vectors with position greater than or equal to i is not enough to fulfill credits_required.
			least_unfulfilled_credit = 0
			while credits_required[least_unfulfilled_credit] == 0:
				least_unfulfilled_credit += 1
			right_bound = right_bounds[least_unfulfilled_credit]
			
			# Add classes
			for i in range(left_bound, right_bound):
				# Inlined vector_sub function call for slightly better performance
				# new_credits_required = vector_sub(credits_required, vectors[i])
				new_credits_required = tuple([a - b if a > b else 0 for a, b in zip(credits_required, vectors[i])])
				
				assert (new_credits_required not in table1) is (new_credits_required not in table2)
				
				# Store minimal subsets in tables
				if new_credits_required not in table1 or 1 + len_selected_vectors < table1[new_credits_required] or (1 + len_selected_vectors == table1[new_credits_required] and i < table2[new_credits_required]):
					table1[new_credits_required] = 1 + len_selected_vectors
					table2[new_credits_required] = i

					# Recurse on minimal subsets
					if not non_pos(new_credits_required):
						new_queue[new_credits_required] = selected_vectors + [i]

	print('building dp tables required {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	# Make query function out of vectors and table1 and table2

	def vector_add(a, b):
		return vector_sub(credit_maxes, vector_sub(vector_sub(credit_maxes, a), b))
	
	def query_helper(fulfilled_credits, selected_vectors):
		if fulfilled_credits == credit_maxes:
			return selected_vectors

		legal_paths = deque()
		
		right_bound = len(vectors)
		if len(selected_vectors) > 0:
			right_bound = selected_vectors[0]
		
		res = None
		
		# Select random vector
		vec_indices = range(table2[fulfilled_credits], right_bound)
		vec_indices = list(vec_indices)
		random.shuffle(vec_indices)
		for i in vec_indices:
			# Select random subvector
			subvectors = all_subvectors_of(vectors[i])
			random.shuffle(subvectors)
			for subvector in subvectors:
				# Select vector if it leads closer to fulfilling credit_maxes
				next_fulfilled_credits = vector_add(subvector, fulfilled_credits)
				if next_fulfilled_credits not in table1: continue
				if table1[fulfilled_credits] <= table1[next_fulfilled_credits]: continue
				
				# Find prefix
				res = query_helper(next_fulfilled_credits, [i] + selected_vectors)
				if res is not None:	break
			if res is not None:	break
		
		# Return set of vectors
		return res
	
	def query():
		# Compute set of courses
		res = query_helper((0,) * len(credit_maxes), [])
		if res is None:
			return None

		# Assert set fulfills credit_maxes
		unfulfilled_credits = credit_maxes[:]
		for x in res:
			unfulfilled_credits = vector_sub(unfulfilled_credits, vectors[x])
		assert non_pos(unfulfilled_credits)
		
		# Assert set is minimal
		assert len(res) == table1[(0,) * len(credit_maxes)], str(len(res)) + ' vs ' + str(table1[(0,) * len(credit_maxes)])
		
		# Assert set contains no duplicates
		assert len(res) == len(set(res))
		
		# Return indices of vectors selected
		return res
	
	return query

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage:')
		print()
		print('python3 algo.py filename')
	else:
		credit_maxes, unsorted_vectors = read_problem(sys.argv[1])
		query = make_query_function(credit_maxes, unsorted_vectors)

		for i in range(1 << 10):
			res = query()
			if i % (1 << 6) == 0:
				print(i, res)