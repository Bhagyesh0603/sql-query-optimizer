from rewriter import generate_join_candidates

# Test candidate generation
query = "SELECT * FROM employees WHERE salary > 50000 ORDER BY salary"
print(f"Testing query: {query}")
print("Generating candidates...")

candidates = generate_join_candidates(query)
print(f"Generated {len(candidates)} candidates")

for i, candidate in enumerate(candidates):
    print(f"\nCandidate {i+1}:")
    print(candidate[:200] + ("..." if len(candidate) > 200 else ""))