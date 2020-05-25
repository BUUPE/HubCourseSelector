from collections import deque
import time
import sys
import random

from vector_operations import vector_sub, non_pos, vector_le
from download_problems import read_problem

# Input: the credit_maxes and vectors of the vector problem
# Return: A function that takes as input a set of unfulfilled credits and returns a set of indices of vectors that fulfills those credits
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
	
	# These assertions ensure that the tables can be written to file.
	# TODO: Write the part that writes dynamic programming table to file after computing the table.
	assert len(credit_maxes) <= (1 << 8)
	assert len(vectors) <= (1 << 16)

	max_nodes = 1
	for x in credit_maxes:
		max_nodes *= x + 1
	
	print('Writing tables to file will use {:d} bytes = {:.2f} KB = {:.2f} MB disk space.'.format(max_nodes * 3, max_nodes * 3 / 1024, max_nodes * 3 / 1024 / 1024))

	# Sort vectors
	vectors = sorted(vectors, reverse = True)

	# Computation path priority queue
	# We recurse on all sets of vectors in the standard order.
	# new_queue holds the largest subsets (by size) to be recursed on.
	new_queue = set()
	new_queue.add(credit_maxes)

	# table[unfulfilled_credits] = min over all seen sets S of vectors that leave unfulfilled_credits unfulfilled of (len(S), S[-1])
	# unfulfilled_credits == credit_maxes is an exception to the above statement. table[credit_maxes] = (0, -1)
	table = dict()
	table[credit_maxes] = (0, -1)

	# Computation status
	processed_nodes = 0
	
	right_bounds = [0] * len(credit_maxes)
	i = 0
	for j in range(len(credit_maxes)):
		while i < len(vectors) and vectors[i][j] == 1:
			i += 1
		right_bounds[j] = i

	# Computation loop
	while len(new_queue) > 0:
		# Progress priority queue
		old_queue = new_queue
		new_queue = set()
		for credits_required in old_queue:
			# Print computation status
			if processed_nodes % 1000 == 0:
				print('At least {:6.2f} % complete.'.format(processed_nodes / max_nodes * 100))
			processed_nodes += 1

			# Extract node from queue
			assert not non_pos(credits_required)
			len_selected_vectors, left_bound = table[credits_required]
			left_bound += 1
			assert (len_selected_vectors == 0) is (left_bound == 0)

			# Add classes
			for i in range(left_bound, len(vectors)):
				# Add vector i to selected vectors
				# Inlined vector_sub function call for slightly better performance
				# new_credits_required = vector_sub(credits_required, vectors[i])
				new_credits_required = tuple([a - b if a > b else 0 for a, b in zip(credits_required, vectors[i])])
				new_set_values = (1 + len_selected_vectors, i)
				
				# Store minimal subsets in tables
				if new_credits_required not in table or new_set_values < table[new_credits_required]:
					table[new_credits_required] = new_set_values

					# Recurse on minimal subsets
					if not non_pos(new_credits_required):
						new_queue.add(new_credits_required)

	print('building dp tables required {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	def recurse(prefix):
		if len(prefix) < len(credit_maxes):
			for i in range(credit_maxes[len(prefix)] + 1):
				recurse(prefix + [i])
		else:
			for i in range(len(credit_maxes)):
				if 0 < prefix[i]:
					# Same vector except ith place decremented
					subvector = tuple([x - 1 if i == j else x for j, x in enumerate(prefix)])
					assert subvector in table
					tuple_prefix = tuple(prefix)
					table_subvector = table[subvector]
					if tuple_prefix not in table or table_subvector < table[tuple_prefix]:
						table[tuple_prefix] = table_subvector

	recurse([])

	print('recursing through vector space required {:.2f} seconds'.format(time.time() - start))
	start = time.time()

	def vector_add(a, b):
		return vector_sub(credit_maxes, vector_sub(vector_sub(credit_maxes, a), b))
	
	def query_helper(fulfilled_credits, selected_vectors):
		# Base case: All credits fulfilled
		if fulfilled_credits == credit_maxes:
			return selected_vectors

		# Must select courses in order
		right_bound = len(vectors)
		if len(selected_vectors) > 0:
			right_bound = selected_vectors[0]
		
		# Randomly select a vector to add to the set
		vec_indices = range(table[fulfilled_credits][1], right_bound)
		vec_indices = list(vec_indices)
		random.shuffle(vec_indices)
		for i in vec_indices:
			# Ignore vectors that do not lead closer to fulfilling credit_maxes
			next_fulfilled_credits = vector_add(vectors[i], fulfilled_credits)
			if table[fulfilled_credits][0] <= table[next_fulfilled_credits][0]: continue

			# Recurse to find the full set of vectors
			res = query_helper(next_fulfilled_credits, [i] + selected_vectors)
			if res is not None:	return res

		return None
	
	def query(fulfilled_credits):
		assert isinstance(fulfilled_credits, tuple)
		for x in fulfilled_credits:
			assert isinstance(x, int)
			assert 0 <= x
		assert vector_le(fulfilled_credits, credit_maxes)

		credits_to_fulfill = vector_sub(credit_maxes, fulfilled_credits)
		
		# Compute set of vectors
		res = query_helper(fulfilled_credits, [])
		if res is None:
			return None

		# Assert set fulfills credit_maxes
		unfulfilled_credits = credits_to_fulfill[:]
		for x in res:
			unfulfilled_credits = vector_sub(unfulfilled_credits, vectors[x])
		assert non_pos(unfulfilled_credits)
		
		# Assert set is minimal
		assert len(res) == table[fulfilled_credits][0]
		
		# Assert set contains no duplicates
		assert len(res) == len(set(res))
		
		# Return indices of vectors selected
		return res
	
	return query

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage:')
		print()
		print('python3 {:s} filename'.format(__file__))
	else:
		credit_maxes, unsorted_vectors = read_problem(sys.argv[1])
		query = make_query_function(credit_maxes, unsorted_vectors)

		start = time.time()
		for i in range(1 << 14):
			res = query(tuple([random.randint(0, x) for x in credit_maxes]))
			if i % (1 << 10) == 0:
				print(i, res)
		print('computing {:d} sets required {:.2f} seconds'.format(1 << 14, time.time() - start))
		start = time.time()
