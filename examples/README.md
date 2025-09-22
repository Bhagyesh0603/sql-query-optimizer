# 📚 SQL Query Optimizer - Example Queries

This directory contains example SQL queries demonstrating various optimization scenarios and use cases.

## Query Categories

### 1. **Basic Optimization Examples**
Simple queries showing fundamental optimization principles.

### 2. **Performance Anti-Patterns**
Queries with common performance issues that the optimizer can detect and fix.

### 3. **Complex Query Scenarios**
Advanced queries demonstrating the optimizer's capabilities with multi-table operations.

### 4. **Index Recommendation Examples**
Queries that benefit from specific index recommendations.

## Usage

```bash
# Analyze any example query
python main.py --query "$(cat examples/basic_select.sql)"

# Run enhanced analysis
python enhanced_demo.py --query "$(cat examples/complex_joins.sql)"

# Benchmark multiple queries
python benchmark_runner.py --file examples/benchmark_set.sql
```

## Files

- `basic_select.sql` - Simple SELECT statements with common issues
- `complex_joins.sql` - Multi-table JOIN scenarios
- `performance_issues.sql` - Queries with known performance problems
- `index_examples.sql` - Queries that need specific indexes
- `benchmark_set.sql` - Complete set for benchmarking