"""Tests for DPLL solver."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dpll_solver import DPLLSolver


def test_simple_sat():
    """Test simple satisfiable formula: (x1 OR x2) AND (NOT x1 OR x2)"""
    clauses = [[1, 2], [-1, 2]]
    solver = DPLLSolver(2, clauses)
    is_sat, assignment, stats = solver.solve()

    assert is_sat
    assert assignment is not None
    # Verify assignment satisfies formula
    assert assignment[2] == True  # x2 must be true


def test_simple_unsat():
    """Test simple unsatisfiable formula: (x1) AND (NOT x1)"""
    clauses = [[1], [-1]]
    solver = DPLLSolver(1, clauses)
    is_sat, assignment, stats = solver.solve()

    assert not is_sat
    assert assignment is None


def test_unit_propagation():
    """Test unit propagation: (x1) AND (NOT x1 OR x2) should propagate to x1=T, x2=T"""
    clauses = [[1], [-1, 2]]
    solver = DPLLSolver(2, clauses)
    is_sat, assignment, stats = solver.solve()

    assert is_sat
    assert assignment[1] == True
    assert assignment[2] == True


def test_pure_literal():
    """Test pure literal elimination: (x1 OR x2) AND (x1 OR x3)"""
    clauses = [[1, 2], [1, 3]]
    solver = DPLLSolver(3, clauses)
    is_sat, assignment, stats = solver.solve()

    assert is_sat
    # x1 is pure positive, should be set to True
    assert assignment[1] == True


def test_three_sat():
    """Test 3-SAT instance."""
    clauses = [
        [1, 2, 3],
        [-1, -2, 3],
        [1, -2, -3],
        [-1, 2, -3]
    ]
    solver = DPLLSolver(3, clauses)
    is_sat, assignment, stats = solver.solve()

    assert is_sat
    # Verify assignment satisfies all clauses
    for clause in clauses:
        satisfied = any(
            (lit > 0 and assignment[abs(lit)]) or
            (lit < 0 and not assignment[abs(lit)])
            for lit in clause
        )
        assert satisfied


def test_pigeonhole_3_2():
    """Test pigeonhole principle: 3 pigeons, 2 holes (UNSAT)"""
    # Variables: x_ij means pigeon i in hole j
    # x11, x12, x21, x22, x31, x32 = 1, 2, 3, 4, 5, 6
    clauses = [
        # Each pigeon in at least one hole
        [1, 2],      # pigeon 1
        [3, 4],      # pigeon 2
        [5, 6],      # pigeon 3
        # At most one pigeon per hole
        [-1, -3],    # hole 1: not both pigeon 1 and 2
        [-1, -5],    # hole 1: not both pigeon 1 and 3
        [-3, -5],    # hole 1: not both pigeon 2 and 3
        [-2, -4],    # hole 2: not both pigeon 1 and 2
        [-2, -6],    # hole 2: not both pigeon 1 and 3
        [-4, -6],    # hole 2: not both pigeon 2 and 3
    ]
    solver = DPLLSolver(6, clauses)
    is_sat, assignment, stats = solver.solve()

    assert not is_sat


def test_empty_formula():
    """Test empty formula (SAT)"""
    clauses = []
    solver = DPLLSolver(0, clauses)
    is_sat, assignment, stats = solver.solve()

    assert is_sat


def test_single_empty_clause():
    """Test formula with empty clause (UNSAT)"""
    clauses = [[]]
    solver = DPLLSolver(0, clauses)
    is_sat, assignment, stats = solver.solve()

    assert not is_sat


if __name__ == '__main__':
    test_simple_sat()
    test_simple_unsat()
    test_unit_propagation()
    test_pure_literal()
    test_three_sat()
    test_pigeonhole_3_2()
    test_empty_formula()
    test_single_empty_clause()
    print("All tests passed!")
