

# Component-wise subtraction, and if component of difference is negative, set it to 0
def vector_add(left, right):
	return tuple([a + b for a, b in zip(left, right)])

# Component-wise subtraction, and if component of difference is negative, set it to 0
def vector_sub(left, right):
	return tuple([a - b if a > b else 0 for a, b in zip(left, right)])

# If all components are less than or equal to the corresponding component
def vector_le(left, right):
	assert len(left) == len(right)

	for a, b in zip(left, right):
		if a > b:
			return False

	return True

# Vector of length n with all components 0
def vec_0(n):
	return (0,) * n

# x <= 0
def non_pos(x):
	for a in x:
		if a > 0:
			return False
	return True

# Returns a list of exactly the vectors v such that a <= v and v <= b
def enumerate_all_vectors_between(a, b):
	assert vector_le(a, b)

	diffs = vector_sub(b, a)

	def recurse(suffix):
		if suffix == []: return [[]]
		if len(suffix) == 1: return [[x] for x in range(suffix[0] + 1)]
		return [[i] + y for i in range(suffix[0] + 1) for y in recurse(suffix[1:])]

	offsets = recurse(diffs)
	out = [tuple([x + y for x, y in zip(a, z)]) for z in offsets]

	return out

# Returns a list of exactly the vectors v such that 0 <= v and v <= a
def all_subvectors_of(a):
	return enumerate_all_vectors_between(vec_0(len(a)), a)

# Encodes a vector as an int
def vector_to_int(maxes, vec):
	assert len(maxes) == len(vec)
	
	encoded = 0
	for a, b in zip(maxes, vec):
		assert b <= a
		encoded *= a + 1
		encoded += b
	return encoded

# int_to_vector(a, vector_to_int(a, b)) == b
def int_to_vector(maxes, encoded):
	out = []
	for a in maxes[::-1]:
		out = [encoded % (a + 1)] + out
		encoded //= (a + 1)
	assert encoded == 0
	return tuple(out)
