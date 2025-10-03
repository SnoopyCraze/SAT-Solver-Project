```python
#Installation

# Install required packages
pip install -r requirements.txt

## Run Tests

# Run all unit tests
python tests/test_dpll_solver.py

Expected output:
"All tests passed!"

#Basic Usage

### 1. Solve Existing Benchmarks

# Solve simple SAT instance with DPLL
python solver.py solve benchmarks/simple_sat.cnf --mode=dpll

# Solve with verbose output
python solver.py solve benchmarks/simple_sat.cnf --mode=dpll --verbose

# Try CDCL solver
python solver.py solve benchmarks/simple_sat.cnf --mode=cdcl

### 2. Generate and Solve New Instances

# Generate random 3-SAT
python -c "
import sys
sys.path.insert(0, 'src')
from benchmark_generator import generate_random_3sat
from dimacs_parser import write_dimacs

clauses = generate_random_3sat(15, 64, seed=123)
write_dimacs('my_instance.cnf', 15, clauses)
print('Generated random 3-SAT with 15 variables')
"

# Solve it
python solver.py solve my_instance.cnf --mode=dpll

### 3. Use Python API

Create a file `test_solver.py`:

import sys
sys.path.insert(0, 'src')

from dimacs_parser import parse_dimacs
from dpll_solver import DPLLSolver

# Load instance
num_vars, num_clauses, clauses = parse_dimacs('benchmarks/simple_sat.cnf')

# Solve
solver = DPLLSolver(num_vars, clauses)
is_sat, assignment, stats = solver.solve()

# Print results
if is_sat:
    print("SATISFIABLE")
    for var in sorted(assignment.keys()):
        print(f"  x{var} = {assignment[var]}")
else:
    print("UNSATISFIABLE")

print(f"\nStatistics:")
print(f"  Time: {stats['time']:.6f}s")
print(f"  Decisions: {stats['decisions']}")
print(f"  Propagations: {stats['propagations']}")

Run it:
python test_solver.py

## Example Outputs

### Simple SAT Instance
============================================================
SATISFIABLE
============================================================

Assignment:
  x2 = True

Statistics:
  Decisions:     0
  Propagations:  0
  Max depth:     0
  Time:          0.000016 seconds
============================================================

### Simple UNSAT Instance
============================================================
UNSATISFIABLE
============================================================

Statistics:
  Decisions:     0
  Propagations:  1
  Max depth:     0
  Time:          0.000011 seconds
============================================================

### Random 3-SAT (10 variables)
============================================================
SATISFIABLE
============================================================

Assignment:
  x1 = True
  x2 = True
  x4 = True
  x5 = False
  x6 = False
  x7 = True
  x8 = True
  x9 = False
  x10 = True

Statistics:
  Decisions:     4
  Propagations:  5
  Max depth:     3
  Time:          0.000144 seconds
============================================================

## Generate Benchmarks

### Random 3-SAT
from src.benchmark_generator import generate_random_3sat
from src.dimacs_parser import write_dimacs

# At phase transition (ratio ~4.3)
clauses = generate_random_3sat(num_vars=20, num_clauses=86, seed=42)
write_dimacs('random_20.cnf', 20, clauses)

### Pigeonhole Principle
from src.benchmark_generator import generate_pigeonhole
from src.dimacs_parser import write_dimacs

# 5 pigeons, 4 holes (UNSAT)
clauses = generate_pigeonhole(5, 4)
write_dimacs('php_5_4.cnf', 20, clauses)

### Parity Formula
from src.benchmark_generator import generate_parity
from src.dimacs_parser import write_dimacs

# Odd parity of 10 variables
clauses = generate_parity(10)
write_dimacs('parity_10.cnf', 19, clauses)  # 10 + 9 auxiliary vars

## Jupyter Notebook Evaluation

# Start Jupyter
jupyter notebook

# Open notebooks/evaluation.ipynb

The notebook includes:
- Automatic benchmark generation
- DPLL vs CDCL comparison
- Performance visualization
- Statistical analysis

## Troubleshooting


### CDCL Timeout
The CDCL solver may timeout on complex instances. This is a known issue being debugged. Use DPLL for reliable results:
python solver.py solve instance.cnf --mode=dpll

### Missing Dependencies
Install all requirements:
pip install python-sat numpy matplotlib networkx graphviz jupyter pytest

### File Structure
```
src/
  dimacs_parser.py      - DIMACS CNF I/O
  dpll_solver.py        - DPLL solver (working)
  cdcl_solver.py        - CDCL solver (experimental)
  benchmark_generator.py - Instance generator
tests/
  test_dpll_solver.py   - Unit tests
benchmarks/
  *.cnf                 - Test instances
solver.py              - Main CLI

### Command Summary
# Run tests
python tests/test_dpll_solver.py

# Solve with DPLL (recommended)
python solver.py solve <file.cnf> --mode=dpll

# Solve with CDCL (experimental)
python solver.py solve <file.cnf> --mode=cdcl

# Verbose output
python solver.py solve <file.cnf> --mode=dpll --verbose

## MADE BY Zeran Johannsen ##
```

