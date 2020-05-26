

'''
Dynamic programming table file format:

vector elements are stored with 1 byte.
vector indices are stored with two bytes.
We use big endian unsigned integer binary encoding to store integers.
Values v which cannot equal 0 will have v-1 stored.

file format:

1 byte: if 0x00 then the table has been completely computed. Any other value means the table has not been completely computed.
1 byte: unsigned integer M, M + 1 = the number of hub unit categories
2 bytes: big endian unsigned integer N, N + 1 = the number of vectors
M + 1 bytes:
	Each byte is an unsigned integer, one for each category. Let x be the value of that byte. x + 1 is the value of credit_maxes in that category.
N + 1 times:
	Each of these constitute a vector.
	2 bytes: big endian unsigned integer a, a + 1 = the id of the vector
	M + 1 bytes:
		Each byte is an unsigned integer, one for each category.
		Let x be the value of that byte. x + 1 is the value of that vector in that category.
for i in range(vector_to_int(credit_maxes, credit_maxes)):
	2 bytes: big endian unsigned integer whose value is table[int_to_vector(credit_maxes, i)][0] - 1
		Exception: If int_to_vector(credit_maxes, i) == credit_maxes, these two bytes can be any value.
	2 bytes: big endian unsigned integer whose value is table[int_to_vector(credit_maxes, i)][1]
		Exception: If int_to_vector(credit_maxes, i) == credit_maxes, these two bytes can be any value.
'''

from collections import deque
import time
import sys
import random
import os

from vector_operations import vector_sub, non_pos, vector_le, vector_to_int, int_to_vector
from download_problems import read_problem

# This table class code is very tightly coupled to the algorithm.
class Table:
	def __init__(self, file_name):
		# Attempt to read the file
		try:
			file_was_opened = False
			file = open(file_name, 'r+b')
			file_was_opened = True
			file.seek(0)
			
			if file.read(1) != bytes([0]): raise RuntimeError
			
			next_bytes = file.read(1)
			if len(next_bytes) != 1: raise RuntimeError
			len_credit_maxes = int.from_bytes(next_bytes, byteorder='big', signed='False') + 1
			
			next_bytes = file.read(2)
			if len(next_bytes) != 2: raise RuntimeError
			len_vectors = int.from_bytes(next_bytes, byteorder='big', signed='False') + 1
			
			credit_maxes = deque()
			for _ in range(len_credit_maxes):
				next_bytes = file.read(1)
				if len(next_bytes) != 1: raise RuntimeError
				credit_maxes.append(int.from_bytes(next_bytes, byteorder='big', signed='False') + 1)
			credit_maxes = tuple(credit_maxes)
			
			vectors_with_ids = deque()
			for i in range(len_vectors):
				next_bytes = file.read(2)
				if len(next_bytes) != 2: raise RuntimeError
				id = int.from_bytes(next_bytes, byteorder='big', signed='False')
				assert id == i
				
				vector = deque()
				for _ in range(len_credit_maxes):
					next_bytes = file.read(1)
					if len(next_bytes) != 1: raise RuntimeError
					vector.append(int.from_bytes(next_bytes, byteorder='big', signed='False'))
				vector = tuple(vector)
				vectors_with_ids.append((id, vector))
			vectors_with_ids = tuple(vectors_with_ids)
			
			file.seek(0, 2)
			if file.tell() != 1 + 1 + 2 + len(credit_maxes) + len(vectors_with_ids) * (2 + len(credit_maxes)) + (vector_to_int(credit_maxes, credit_maxes) + 1) * 4:
				raise RuntimeError
			
			self.credit_maxes = credit_maxes
			self.vector_id_table = dict()
			for id, vector in vectors_with_ids:
				if vector not in self.vector_id_table:
					self.vector_id_table[vector] = set()
				self.vector_id_table[vector].add(id)
			self.vector_id_table = {k: tuple(v) for k, v in self.vector_id_table.items()}
			self.table_offset = 4 + len(credit_maxes) + len(vectors_with_ids) * (2 + len(credit_maxes))
			self.file = file
			self.initialized = True
			self.finalized = True
		except Exception as e:
			if file_was_opened:
				file.close()
		
			# Make directory of write location
			try:
				os.makedirs(os.path.dirname(file_name))
			except FileExistsError:
				pass

			# Open file
			self.file = open(file_name, 'w+b')
			self.file.seek(0, 2)
			assert self.file.tell() == 0
			self.initialized = False
			self.finalized = False

	def init_empty_table(self, credit_maxes, vectors_with_ids):
		if self.is_initialized():
			raise RuntimeError
		self.credit_maxes = credit_maxes
		self.vector_id_table = dict()
		for id, vector in vectors_with_ids:
			if vector not in self.vector_id_table:
				self.vector_id_table[vector] = set()
			self.vector_id_table[vector].add(id)
		self.vector_id_table = {k: tuple(v) for k, v in self.vector_id_table.items()}
		self.table_offset = 4 + len(credit_maxes) + len(vectors_with_ids) * (2 + len(credit_maxes))
		self.table_keys = set()
		
		self.file.seek(0)
		
		# Write finalized flag
		self.file.write(bytes([255]))
	
		# Write M
		self.file.write((len(credit_maxes) - 1).to_bytes(1, byteorder='big', signed = False))
		
		# Write N
		self.file.write((len(vectors_with_ids) - 1).to_bytes(2, byteorder='big', signed = False))
		
		# Write credit_maxes
		for x in credit_maxes:
			self.file.write((x - 1).to_bytes(1, byteorder='big', signed = False))
		
		# Write vectors
		for i, (id, vector) in enumerate(vectors_with_ids):
			assert i == id
			self.file.write(id.to_bytes(2, byteorder='big', signed = False))
			for x in vector:
				self.file.write(x.to_bytes(1, byteorder='big', signed = False))
		
		assert self.table_offset == self.file.tell()
		
		# Write all 0xFF to table - These values indicate unwritten to table if len(credit_maxes) != 1 << 8 or len(vectors_with_ids) != 1 << 16
		for i in range(vector_to_int(credit_maxes, credit_maxes)):
			for _ in range(4):
				self.file.write(bytes([255]))
		
		self.initialized = True

		# Write table[credit_maxes]
		self.__setitem__(credit_maxes, None)

	def __setitem__(self, key, value):
		if self.is_finalized():
			raise RuntimeError
		if not self.is_initialized():
			raise RuntimeError
		self.file.seek(self.table_offset + vector_to_int(self.credit_maxes, key) * 4)
		if key == credit_maxes:
			self.file.write(bytes([255]) * 4)
		else:
			self.file.write((value[0] - 1).to_bytes(2, byteorder='big', signed = False))
			self.file.write(value[1].to_bytes(2, byteorder='big', signed = False))
		self.table_keys.add(key)
	
	# TODO: Assert that key is a vector v such that 0 <= v and v <= self.credit_maxes
	def __contains__(self, key):
		if not self.is_initialized():
			raise RuntimeError
		if self.is_finalized():
			return True
		return key in self.table_keys
	
	def __getitem__(self, key):
		if not self.is_initialized():
			raise RuntimeError
		if not self.__contains__(key):
			raise RuntimeError
		if key == self.credit_maxes:
			return (0, -1)

		self.file.seek(self.table_offset + vector_to_int(self.credit_maxes, key) * (4))
		value_0 = int.from_bytes(self.file.read(2), byteorder='big', signed = False) + 1
		value_1 = int.from_bytes(self.file.read(2), byteorder='big', signed = False)
		if value_0 > 1 << 14 and value_1 > 1 << 14:
			print('here1')
		return (value_0, value_1)
	
	def finalize(self):
		if not self.is_initialized():
			raise RuntimeError
		self.file.seek(0)
		self.file.write(bytes([0]))
		del self.table_keys
		self.finalized = True
	
	def is_finalized(self):
		return self.finalized
	
	def is_initialized(self):
		return self.initialized
	
	def vector_to_id(self, vector):
		if not self.is_initialized():
			raise RuntimeError
		if vector not in self.vector_id_table:
			raise RuntimeError
		return random.choice(self.vector_id_table[vector])

# Input: the credit_maxes and vectors of the vector problem
# Return: A function that takes as input a set of unfulfilled credits and returns a set of indices of vectors that fulfills those credits
# TODO: Change return value to vectors selected or course codes selected.
def make_query_function(credit_maxes, vectors, table_file_name):
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
	for x in credit_maxes:
		assert 1 <= x
		assert x <= 256

	max_nodes = 1
	for x in credit_maxes:
		max_nodes *= x + 1

	# Sort vectors
	vectors_with_ids = list(enumerate(vectors))
	vectors = sorted(vectors, reverse = True)

	table = Table(table_file_name)

	# Compute table if not already computed in provided table file
	if not table.is_finalized():
		storage_cost = 1 + 1 + 2 + len(credit_maxes) + len(vectors) * (2 + len(credit_maxes)) + max_nodes * 4
		print('Writing tables to file will use {:d} bytes = {:.2f} KB = {:.2f} MB disk space.'.format(storage_cost, storage_cost / 1024, storage_cost / 1024 / 1024))

		table.init_empty_table(credit_maxes, vectors_with_ids)

		# Computation path priority queue
		# We recurse on all sets of vectors in the standard order.
		# new_queue holds the largest subsets (by size) to be recursed on.
		new_queue = set()
		new_queue.add(credit_maxes)

		# table[unfulfilled_credits] = min over all seen sets S of vectors that leave unfulfilled_credits unfulfilled of (len(S), S[-1])
		# unfulfilled_credits == credit_maxes is an exception to the above statement. table[credit_maxes] = (0, -1)
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
					print('At least {:5.2f} % complete.'.format(processed_nodes / max_nodes * 100))
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

		# table[unfulfilled_credits] stores values for subsets that leave at most unfulfilled_credits unfulfilled
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

		table.finalize()

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

		res = query_helper(fulfilled_credits, [])
		
		# Assert set is minimal
		assert len(res) == table[fulfilled_credits][0]
		
		# Output the indices of the vectors under the original order.
		out = set()
		for index in res:
			y = table.vector_to_id(vectors[index])
			while y in out:
				y = table.vector_to_id(vectors[index])
			out.add(y)
		return sorted(out)

	return query

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage:')
		print()
		print('python3 {:s} filename'.format(__file__))
	else:
		credit_maxes, unsorted_vectors = read_problem(sys.argv[1])
		query = make_query_function(credit_maxes, unsorted_vectors, 'Solution/{:s}/{:s}'.format(__file__[:__file__.rfind('.')], os.path.basename(sys.argv[1])))

		start = time.time()
		for i in range(1 << 14):
			random_fulfilled_credits = [random.randint(0, x) for x in credit_maxes]
			random_fulfilled_credits = tuple(random_fulfilled_credits)
			res = query(random_fulfilled_credits)
			
			# Assert set has no duplicates
			assert len(res) == len(set(res))
			
			# Assert set fulfills classes
			unfulfilled_credits = credit_maxes
			unfulfilled_credits = vector_sub(unfulfilled_credits, random_fulfilled_credits)
			for x in res:
				unfulfilled_credits = vector_sub(unfulfilled_credits, unsorted_vectors[x])
			assert non_pos(unfulfilled_credits)
			
			if i % (1 << 10) == 0:
				print(i, res)
		print('computing {:d} sets required {:.2f} seconds'.format(1 << 14, time.time() - start))
		start = time.time()
