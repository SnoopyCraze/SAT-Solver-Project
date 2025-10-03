"""Basic DPLL SAT solver with unit propagation and pure literal elimination."""

import time
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict


class DPLLSolver:
    """
    DPLL-based SAT solver implementing:
    - Unit propagation
    - Pure literal elimination
    - Backtracking search
    """

    def __init__(self, num_vars: int, clauses: List[List[int]]):
        """
        Initialize solver.

        Args:
            num_vars: Number of variables in the formula
            clauses: List of clauses (each clause is a list of literals)
        """
        self.num_vars = num_vars
        self.original_clauses = [list(clause) for clause in clauses]
        self.clauses = None
        self.assignment = {}

        # Statistics
        self.num_decisions = 0
        self.num_propagations = 0
        self.max_depth = 0

        # Occurrence lists: literal -> set of clause indices
        self.occurrence_lists = None

    def _init_data_structures(self):
        """Initialize data structures for solving."""
        self.clauses = [list(clause) for clause in self.original_clauses]
        self.assignment = {}
        self.num_decisions = 0
        self.num_propagations = 0
        self.max_depth = 0

        # Build occurrence lists
        self.occurrence_lists = defaultdict(set)
        for clause_idx, clause in enumerate(self.clauses):
            for lit in clause:
                self.occurrence_lists[lit].add(clause_idx)

    def solve(self) -> Tuple[bool, Optional[Dict[int, bool]], Dict]:
        """
        Solve the SAT instance.

        Returns:
            Tuple of (is_sat, assignment, stats)
            - is_sat: True if SAT, False if UNSAT
            - assignment: Variable assignment if SAT, None if UNSAT
            - stats: Dictionary of solver statistics
        """
        start_time = time.time()
        self._init_data_structures()

        result = self._dpll(0)

        end_time = time.time()

        stats = {
            'decisions': self.num_decisions,
            'propagations': self.num_propagations,
            'max_depth': self.max_depth,
            'time': end_time - start_time
        }

        if result:
            return True, dict(self.assignment), stats
        else:
            return False, None, stats

    def _dpll(self, depth: int) -> bool:
        """
        Main DPLL algorithm with backtracking.

        Args:
            depth: Current recursion depth

        Returns:
            True if SAT, False if UNSAT
        """
        self.max_depth = max(self.max_depth, depth)

        # Unit propagation
        if not self._unit_propagate():
            return False

        # Check if all clauses are satisfied
        if self._all_clauses_satisfied():
            return True

        # Check for empty clause (conflict)
        if self._has_empty_clause():
            return False

        # Pure literal elimination
        self._pure_literal_eliminate()

        # Check again after pure literal elimination
        if self._all_clauses_satisfied():
            return True

        if self._has_empty_clause():
            return False

        # Choose next variable to assign
        var = self._choose_variable()
        if var is None:
            # All variables assigned but still unsatisfied clauses
            return False

        # Try assigning True
        self.num_decisions += 1
        if self._try_assignment(var, True, depth):
            return True

        # Backtrack and try False
        self.num_decisions += 1
        if self._try_assignment(var, False, depth):
            return True

        return False

    def _unit_propagate(self) -> bool:
        """
        Perform unit propagation until fixpoint.

        Returns:
            False if conflict detected, True otherwise
        """
        changed = True
        while changed:
            changed = False
            unit_clauses = self._find_unit_clauses()

            if not unit_clauses:
                break

            for lit in unit_clauses:
                var = abs(lit)
                value = lit > 0

                if var in self.assignment:
                    # Already assigned
                    if self.assignment[var] != value:
                        # Conflict
                        return False
                    continue

                # Propagate
                self.assignment[var] = value
                self.num_propagations += 1
                changed = True

                # Simplify formula
                self._simplify_with_assignment(var, value)

        return True

    def _pure_literal_eliminate(self):
        """Eliminate pure literals from the formula."""
        pure_literals = self._find_pure_literals()

        for lit in pure_literals:
            var = abs(lit)
            value = lit > 0

            if var not in self.assignment:
                self.assignment[var] = value
                self._simplify_with_assignment(var, value)

    def _find_unit_clauses(self) -> List[int]:
        """
        Find all unit clauses in current formula.

        Returns:
            List of unit literals
        """
        unit_literals = []
        for clause in self.clauses:
            if len(clause) == 1:
                unit_literals.append(clause[0])
        return unit_literals

    def _find_pure_literals(self) -> Set[int]:
        """
        Find all pure literals in current formula.

        Returns:
            Set of pure literals
        """
        literal_counts = defaultdict(lambda: {'pos': 0, 'neg': 0})

        for clause in self.clauses:
            for lit in clause:
                var = abs(lit)
                if lit > 0:
                    literal_counts[var]['pos'] += 1
                else:
                    literal_counts[var]['neg'] += 1

        pure_literals = set()
        for var, counts in literal_counts.items():
            if var not in self.assignment:
                if counts['pos'] > 0 and counts['neg'] == 0:
                    pure_literals.add(var)
                elif counts['neg'] > 0 and counts['pos'] == 0:
                    pure_literals.add(-var)

        return pure_literals

    def _all_clauses_satisfied(self) -> bool:
        """Check if all clauses are satisfied."""
        return len(self.clauses) == 0

    def _has_empty_clause(self) -> bool:
        """Check if there's an empty clause (conflict)."""
        return any(len(clause) == 0 for clause in self.clauses)

    def _choose_variable(self) -> Optional[int]:
        """
        Choose next unassigned variable.

        Returns:
            Variable number or None if all assigned
        """
        # Find first unassigned variable that appears in remaining clauses
        appearing_vars = set()
        for clause in self.clauses:
            for lit in clause:
                appearing_vars.add(abs(lit))

        for var in appearing_vars:
            if var not in self.assignment:
                return var

        return None

    def _try_assignment(self, var: int, value: bool, depth: int) -> bool:
        """
        Try assigning a value to a variable and recursively solve.

        Args:
            var: Variable to assign
            value: Value to assign (True/False)
            depth: Current recursion depth

        Returns:
            True if this assignment leads to SAT
        """
        # Save state
        saved_clauses = [list(clause) for clause in self.clauses]
        saved_assignment = dict(self.assignment)

        # Make assignment
        self.assignment[var] = value
        self._simplify_with_assignment(var, value)

        # Recursively solve
        if self._dpll(depth + 1):
            return True

        # Backtrack
        self.clauses = saved_clauses
        self.assignment = saved_assignment

        return False

    def _simplify_with_assignment(self, var: int, value: bool):
        """
        Simplify formula with given assignment.

        Args:
            var: Variable assigned
            value: Value assigned to variable
        """
        lit = var if value else -var
        neg_lit = -lit

        # Remove satisfied clauses (containing lit)
        # Remove neg_lit from unsatisfied clauses
        new_clauses = []
        for clause in self.clauses:
            if lit in clause:
                # Clause is satisfied, remove it
                continue
            elif neg_lit in clause:
                # Remove neg_lit from clause
                new_clause = [l for l in clause if l != neg_lit]
                new_clauses.append(new_clause)
            else:
                # Clause unchanged
                new_clauses.append(clause)

        self.clauses = new_clauses
