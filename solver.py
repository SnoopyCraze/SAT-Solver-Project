#!/usr/bin/env python3
"""SAT Solver CLI - Command line interface for SAT solver."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dimacs_parser import parse_dimacs
from dpll_solver import DPLLSolver
from cdcl_solver import CDCLSolver


def main():
    parser = argparse.ArgumentParser(description='SAT Solver - DPLL and CDCL based solver')
    parser.add_argument('command', choices=['solve'], help='Command to execute')
    parser.add_argument('input_file', help='Input CNF file in DIMACS format')
    parser.add_argument('--mode', choices=['dpll', 'cdcl'], default='dpll',
                        help='Solver mode (default: dpll)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.command == 'solve':
        solve_command(args)


def solve_command(args):
    """Execute the solve command."""
    # Parse input file
    try:
        num_vars, num_clauses, clauses = parse_dimacs(args.input_file)
    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Loaded formula: {num_vars} variables, {num_clauses} clauses")

    # Create solver
    if args.mode == 'dpll':
        solver = DPLLSolver(num_vars, clauses)
    elif args.mode == 'cdcl':
        solver = CDCLSolver(num_vars, clauses)
    else:
        print(f"Error: Unknown mode '{args.mode}'", file=sys.stderr)
        sys.exit(1)

    # Solve
    if args.verbose:
        print(f"Solving with {args.mode.upper()}...")

    is_sat, assignment, stats = solver.solve()

    # Output results
    print("\n" + "="*60)
    if is_sat:
        print("SATISFIABLE")
        print("="*60)
        print("\nAssignment:")
        for var in sorted(assignment.keys()):
            value = assignment[var]
            print(f"  x{var} = {value}")
    else:
        print("UNSATISFIABLE")
        print("="*60)

    print("\nStatistics:")
    print(f"  Decisions:     {stats['decisions']}")
    print(f"  Propagations:  {stats['propagations']}")
    if 'max_depth' in stats:
        print(f"  Max depth:     {stats['max_depth']}")
    if 'conflicts' in stats:
        print(f"  Conflicts:     {stats['conflicts']}")
    if 'learned' in stats:
        print(f"  Learned:       {stats['learned']}")
    if 'restarts' in stats:
        print(f"  Restarts:      {stats['restarts']}")
    print(f"  Time:          {stats['time']:.6f} seconds")
    print("="*60)


if __name__ == '__main__':
    main()
