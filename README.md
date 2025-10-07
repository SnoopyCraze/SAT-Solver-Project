# SAT-Solver-Project
Python SAT Solver (DPLL + CDCL + VSIDS) – A from-scratch implementation of modern SAT solving algorithms with clause learning, non-chronological backtracking, heuristics, and visualizations.

This project is my independent research into SAT solvers written entirely in Python, designed to explore the theory and practice of propositional satisfiability. It begins with a baseline DPLL algorithm and extends to modern techniques including unit propagation, pure literal elimination, watched literals, conflict-driven clause learning (CDCL), non-chronological backtracking, and the VSIDS heuristic used in industrial solvers.

The solver accepts DIMACS CNF files, provides detailed statistics and logs, and includes visualizations of search trees and implication graphs. A benchmarking suite compares its performance against positively known solvers such as MiniSAT and PySAT.
