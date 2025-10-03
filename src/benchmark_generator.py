"""Benchmark generator for SAT instances."""

import random
from typing import List, Optional
from dimacs_parser import write_dimacs


def generate_random_3sat(num_vars: int, num_clauses: int, seed: Optional[int] = None) -> List[List[int]]:
    """
    Generate random 3-SAT instance.

    Args:
        num_vars: Number of variables
        num_clauses: Number of clauses
        seed: Random seed for reproducibility

    Returns:
        List of clauses
    """
    if seed is not None:
        random.seed(seed)

    clauses = []
    for _ in range(num_clauses):
        clause = []
        vars_in_clause = random.sample(range(1, num_vars + 1), 3)
        for var in vars_in_clause:
            lit = var if random.random() < 0.5 else -var
            clause.append(lit)
        clauses.append(clause)

    return clauses


def generate_pigeonhole(num_pigeons: int, num_holes: int) -> List[List[int]]:
    """
    Generate pigeonhole principle formula.

    Args:
        num_pigeons: Number of pigeons
        num_holes: Number of holes

    Returns:
        List of clauses

    Variables: x_{i,j} = pigeon i in hole j
    Variable encoding: (i-1) * num_holes + j
    """
    clauses = []

    # Each pigeon must be in at least one hole
    for i in range(1, num_pigeons + 1):
        clause = []
        for j in range(1, num_holes + 1):
            var = (i - 1) * num_holes + j
            clause.append(var)
        clauses.append(clause)

    # At most one pigeon per hole
    for j in range(1, num_holes + 1):
        for i1 in range(1, num_pigeons + 1):
            for i2 in range(i1 + 1, num_pigeons + 1):
                var1 = (i1 - 1) * num_holes + j
                var2 = (i2 - 1) * num_holes + j
                clauses.append([-var1, -var2])

    return clauses


def generate_parity(num_vars: int) -> List[List[int]]:
    """
    Generate parity formula (XOR chain).

    Args:
        num_vars: Number of variables

    Returns:
        List of clauses
    """
    clauses = []

    # XOR of all variables = 1
    # Encode using Tseitin transformation
    # x1 XOR x2 XOR ... XOR xn = 1

    # For simplicity, generate clauses that assert odd parity
    # This requires 2^n clauses in CNF, so we'll use a different encoding

    # Use auxiliary variables for parity chain
    # y1 = x1
    # y2 = y1 XOR x2
    # y3 = y2 XOR x3
    # ...
    # yn = 1 (final parity must be odd)

    # XOR encoding: a XOR b = c
    # CNF: (a v b v c) & (a v ~b v ~c) & (~a v b v ~c) & (~a v ~b v c)

    aux_start = num_vars + 1

    # y1 = x1
    clauses.append([-1, aux_start])
    clauses.append([1, -aux_start])

    # yi = y(i-1) XOR xi
    for i in range(2, num_vars + 1):
        prev_aux = aux_start + i - 2
        curr_aux = aux_start + i - 1
        xi = i

        # prev_aux XOR xi = curr_aux
        clauses.append([prev_aux, xi, curr_aux])
        clauses.append([prev_aux, -xi, -curr_aux])
        clauses.append([-prev_aux, xi, -curr_aux])
        clauses.append([-prev_aux, -xi, curr_aux])

    # Final auxiliary must be true (odd parity)
    final_aux = aux_start + num_vars - 1
    clauses.append([final_aux])

    return clauses


if __name__ == '__main__':
    from typing import Optional
    import argparse

    parser = argparse.ArgumentParser(description='Generate SAT benchmarks')
    parser.add_argument('type', choices=['3sat', 'pigeonhole', 'parity'],
                        help='Type of benchmark')
    parser.add_argument('output', help='Output file')
    parser.add_argument('--vars', type=int, default=10, help='Number of variables')
    parser.add_argument('--clauses', type=int, help='Number of clauses (for 3-SAT)')
    parser.add_argument('--pigeons', type=int, help='Number of pigeons')
    parser.add_argument('--holes', type=int, help='Number of holes')
    parser.add_argument('--seed', type=int, help='Random seed')

    args = parser.parse_args()

    if args.type == '3sat':
        num_clauses = args.clauses if args.clauses else int(args.vars * 4.3)
        clauses = generate_random_3sat(args.vars, num_clauses, args.seed)
        write_dimacs(args.output, args.vars, clauses)
        print(f"Generated 3-SAT: {args.vars} vars, {len(clauses)} clauses")

    elif args.type == 'pigeonhole':
        pigeons = args.pigeons if args.pigeons else 4
        holes = args.holes if args.holes else 3
        clauses = generate_pigeonhole(pigeons, holes)
        num_vars = pigeons * holes
        write_dimacs(args.output, num_vars, clauses)
        print(f"Generated pigeonhole: {pigeons} pigeons, {holes} holes, {num_vars} vars, {len(clauses)} clauses")

    elif args.type == 'parity':
        clauses = generate_parity(args.vars)
        num_vars = args.vars + args.vars - 1  # Original + auxiliary
        write_dimacs(args.output, num_vars, clauses)
        print(f"Generated parity: {args.vars} vars, {len(clauses)} clauses")
