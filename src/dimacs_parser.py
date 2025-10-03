"""DIMACS CNF file parser for SAT solver."""

from typing import List, Tuple


def parse_dimacs(filename: str) -> Tuple[int, int, List[List[int]]]:
    """
    Parse a DIMACS CNF file.

    Args:
        filename: Path to DIMACS CNF file

    Returns:
        Tuple of (num_vars, num_clauses, clauses)
        where clauses is a list of lists of integers (literals)
    """
    num_vars = 0
    num_clauses = 0
    clauses = []

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('c'):
                continue

            # Parse problem line
            if line.startswith('p'):
                parts = line.split()
                if len(parts) != 4 or parts[1] != 'cnf':
                    raise ValueError(f"Invalid problem line: {line}")
                num_vars = int(parts[2])
                num_clauses = int(parts[3])
                continue

            # Parse clause
            literals = [int(x) for x in line.split()]
            if literals[-1] != 0:
                raise ValueError(f"Clause must end with 0: {line}")

            # Remove trailing 0 and add clause
            clause = literals[:-1]
            if clause:  # Skip empty clauses
                clauses.append(clause)

    return num_vars, num_clauses, clauses


def write_dimacs(filename: str, num_vars: int, clauses: List[List[int]]) -> None:
    """
    Write clauses to a DIMACS CNF file.

    Args:
        filename: Path to output file
        num_vars: Number of variables
        clauses: List of clauses (each clause is a list of literals)
    """
    with open(filename, 'w') as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(' '.join(str(lit) for lit in clause) + ' 0\n')
