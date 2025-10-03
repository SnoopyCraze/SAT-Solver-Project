"""CDCL SAT solver with watched literals, activity-based heuristics, and conflict learning."""

import time
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
import heapq


class CDCLSolver:
    """
    CDCL-based SAT solver implementing:
    - Watched literals for efficient propagation
    - Activity-based variable ordering
    - Trail with decision levels
    - Implication graph
    - Conflict-driven clause learning with 1-UIP
    - Non-chronological backtracking
    - Restarts
    """

    def __init__(self, num_vars: int, clauses: List[List[int]]):
        """
        Initialize solver.

        Args:
            num_vars: Number of variables in the formula
            clauses: List of clauses (each clause is a list of literals)
        """
        self.num_vars = num_vars
        self.original_clauses = [list(clause) for clause in clauses if clause]

        # Clause database
        self.clauses = []  # List of Clause objects
        self.learned_clauses = []
        self.clause_activity = []  # Activity scores for learned clauses
        self.max_learned_clauses = 1000  # Clause deletion threshold

        # Watched literals: lit -> list of clause indices watching this literal
        self.watch_list = defaultdict(list)

        # Trail: sequence of assignments with metadata
        self.trail = []  # List of (lit, decision_level, antecedent_clause_idx)
        self.trail_lim = []  # Indices in trail where each decision level starts

        # Assignment: var -> value (True/False) or None if unassigned
        self.assignment = [None] * (num_vars + 1)  # 1-indexed

        # Decision level tracking
        self.decision_level = 0

        # Variable activity scores for VSIDS
        self.activity = [0.0] * (num_vars + 1)  # 1-indexed
        self.activity_inc = 1.0
        self.activity_decay = 0.95

        # Heap for variable selection (max-heap using negative activity)
        self.var_order = []
        self.var_pos = {}  # var -> position in heap

        # Statistics
        self.num_decisions = 0
        self.num_propagations = 0
        self.num_conflicts = 0
        self.num_learned = 0
        self.num_restarts = 0

        # Conflict analysis
        self.seen = [False] * (num_vars + 1)

    def _init_data_structures(self):
        """Initialize data structures for solving."""
        # Create clause objects with watched literals
        self.clauses = []
        for clause_lits in self.original_clauses:
            clause_idx = len(self.clauses)
            self.clauses.append(list(clause_lits))

            # Initialize watched literals (first two literals)
            if len(clause_lits) >= 1:
                self.watch_list[clause_lits[0]].append(clause_idx)
            if len(clause_lits) >= 2:
                self.watch_list[clause_lits[1]].append(clause_idx)

        # Initialize variable order heap
        self.var_order = []
        self.var_pos = {}
        for var in range(1, self.num_vars + 1):
            self._heap_insert(var)

        # Reset state
        self.trail = []
        self.trail_lim = []
        self.assignment = [None] * (self.num_vars + 1)
        self.decision_level = 0
        self.learned_clauses = []
        self._propagate_head = 0

        # Reset stats
        self.num_decisions = 0
        self.num_propagations = 0
        self.num_conflicts = 0
        self.num_learned = 0
        self.num_restarts = 0

    def solve(self, time_limit: Optional[float] = None) -> Tuple[bool, Optional[Dict[int, bool]], Dict]:
        """
        Solve the SAT instance.

        Args:
            time_limit: Optional time limit in seconds

        Returns:
            Tuple of (is_sat, assignment, stats)
        """
        start_time = time.time()
        self._init_data_structures()

        # Check for empty clause
        if any(len(clause) == 0 for clause in self.clauses):
            return False, None, self._get_stats(start_time)

        # Initial propagation of unit clauses
        conflict_clause = self._initial_propagate()
        if conflict_clause is not None:
            return False, None, self._get_stats(start_time)

        # Main CDCL loop
        while True:
            # Check time limit
            if time_limit and (time.time() - start_time) > time_limit:
                return None, None, self._get_stats(start_time)

            # Unit propagation
            conflict_clause = self._propagate()

            if conflict_clause is not None:
                # Conflict occurred
                self.num_conflicts += 1

                # At decision level 0, formula is UNSAT
                if self.decision_level == 0:
                    return False, None, self._get_stats(start_time)

                # Analyze conflict and learn clause
                learned_clause, backtrack_level = self._analyze_conflict(conflict_clause)

                # Backtrack
                self._backtrack(backtrack_level)

                # Add learned clause
                self._add_learned_clause(learned_clause)

                # Decay activities
                self._decay_activities()

                # Clause deletion (periodic database reduction)
                if len(self.learned_clauses) > self.max_learned_clauses:
                    self._reduce_learned_clauses()

                # Restart heuristic (simple geometric restart)
                if self.num_conflicts % 100 == 0:
                    self._restart()
            else:
                # No conflict

                # Check if all variables are assigned (SAT)
                if len(self.trail) == self.num_vars:
                    assignment = {}
                    for var in range(1, self.num_vars + 1):
                        assignment[var] = self.assignment[var]
                    return True, assignment, self._get_stats(start_time)

                # Make decision
                self._make_decision()

    def _initial_propagate(self) -> Optional[int]:
        """Find and propagate initial unit clauses."""
        # Scan for unit clauses
        for clause_idx, clause in enumerate(self.clauses):
            if len(clause) == 1:
                lit = clause[0]
                var = abs(lit)
                value = lit > 0

                if self.assignment[var] is None:
                    self.assignment[var] = value
                    self.trail.append((lit, 0, clause_idx))
                    self.num_propagations += 1
                elif self.assignment[var] != value:
                    # Conflict at decision level 0
                    return clause_idx

        # Now propagate
        return self._propagate()

    def _propagate(self) -> Optional[int]:
        """
        Perform unit propagation using watched literals.

        Returns:
            Index of conflict clause if conflict detected, None otherwise
        """
        # Track which trail entries we've already propagated
        if not hasattr(self, '_propagate_head'):
            self._propagate_head = 0

        while self._propagate_head < len(self.trail):
            lit = self.trail[self._propagate_head][0]
            self._propagate_head += 1

            # Check clauses watching ~lit
            neg_lit = -lit
            watch_list_copy = list(self.watch_list[neg_lit])

            for clause_idx in watch_list_copy:
                clause = self.clauses[clause_idx]

                # Find the watched literals
                if clause[0] == neg_lit:
                    watched_idx = 0
                    other_watched_idx = 1
                elif clause[1] == neg_lit:
                    watched_idx = 1
                    other_watched_idx = 0
                else:
                    # This clause no longer watches neg_lit
                    continue

                # Check if other watched literal is true
                other_watched = clause[other_watched_idx] if other_watched_idx < len(clause) else None
                if other_watched and self._lit_value(other_watched) == True:
                    continue

                # Try to find a new literal to watch
                new_watch_idx = None
                for i in range(2, len(clause)):
                    if self._lit_value(clause[i]) != False:
                        new_watch_idx = i
                        break

                if new_watch_idx is not None:
                    # Found new literal to watch
                    clause[watched_idx], clause[new_watch_idx] = clause[new_watch_idx], clause[watched_idx]
                    self.watch_list[neg_lit].remove(clause_idx)
                    self.watch_list[clause[watched_idx]].append(clause_idx)
                else:
                    # Could not find new watch
                    if other_watched and self._lit_value(other_watched) == False:
                        # Both watched literals are false -> conflict
                        return clause_idx
                    elif other_watched:
                        # Unit clause: propagate other_watched
                        var = abs(other_watched)
                        value = other_watched > 0
                        self.assignment[var] = value
                        self.trail.append((other_watched, self.decision_level, clause_idx))
                        self.num_propagations += 1

        return None

    def _analyze_conflict(self, conflict_clause_idx: int) -> Tuple[List[int], int]:
        """
        Analyze conflict and derive learned clause using 1-UIP.

        Args:
            conflict_clause_idx: Index of conflict clause

        Returns:
            Tuple of (learned_clause, backtrack_level)
        """
        if self.decision_level == 0:
            return [], 0

        learned = []
        seen = [False] * (self.num_vars + 1)
        counter = 0
        p = None

        clause = self.clauses[conflict_clause_idx]

        while True:
            # Process current clause
            for lit in clause:
                var = abs(lit)
                if not seen[var] and var > 0:
                    seen[var] = True

                    # Get decision level of this variable
                    var_level = self._var_level(var)

                    if var_level == self.decision_level:
                        counter += 1
                    elif var_level > 0:
                        learned.append(-lit)

            # Find next literal to resolve
            while len(self.trail) > 0:
                p, _, _ = self.trail[-1]
                var = abs(p)
                if seen[var]:
                    break
                self.trail.pop()

            if counter == 1:
                break

            counter -= 1
            seen[var] = False

            # Get antecedent of p
            antecedent_idx = self._get_antecedent(var)
            if antecedent_idx is None:
                break
            clause = self.clauses[antecedent_idx]

        # Add UIP literal
        learned.append(-p if p else 0)

        # Calculate backtrack level
        if len(learned) == 1:
            backtrack_level = 0
        else:
            max_level = 0
            for lit in learned[:-1]:
                var = abs(lit)
                level = self._var_level(var)
                max_level = max(max_level, level)
            backtrack_level = max_level

        # Bump activity of variables in learned clause
        for lit in learned:
            var = abs(lit)
            if var > 0:
                self._bump_activity(var)

        self.num_learned += 1
        return learned, backtrack_level

    def _add_learned_clause(self, clause: List[int]):
        """Add learned clause to database."""
        if not clause:
            return

        clause_idx = len(self.clauses)
        self.clauses.append(list(clause))
        self.learned_clauses.append(clause_idx)
        self.clause_activity.append(0.0)

        # Set up watched literals
        if len(clause) >= 1:
            self.watch_list[clause[0]].append(clause_idx)
        if len(clause) >= 2:
            self.watch_list[clause[1]].append(clause_idx)

    def _backtrack(self, level: int):
        """Backtrack to given decision level."""
        if level >= self.decision_level:
            return

        # Find trail position for target level
        if level < 0:
            target_trail_pos = 0
        elif level < len(self.trail_lim):
            target_trail_pos = self.trail_lim[level]
        else:
            return

        # Undo assignments
        for i in range(len(self.trail) - 1, target_trail_pos - 1, -1):
            if i >= len(self.trail):
                break
            lit, _, _ = self.trail[i]
            var = abs(lit)
            self.assignment[var] = None
            self._heap_insert(var)

        # Truncate trail
        self.trail = self.trail[:target_trail_pos]
        self.trail_lim = self.trail_lim[:level]
        self.decision_level = level

        # Reset propagation head
        self._propagate_head = len(self.trail)

    def _make_decision(self):
        """Make a decision on next variable."""
        # Choose variable with highest activity
        var = self._choose_variable()
        if var is None:
            return

        # Choose value (default: True)
        value = True
        lit = var if value else -var

        # Increase decision level
        self.decision_level += 1
        self.trail_lim.append(len(self.trail))

        # Assign
        self.assignment[var] = value
        self.trail.append((lit, self.decision_level, None))
        self.num_decisions += 1

    def _restart(self):
        """Restart search (backtrack to level 0 but keep learned clauses)."""
        self._backtrack(0)
        self.num_restarts += 1

    def _reduce_learned_clauses(self):
        """Remove low-activity learned clauses from database."""
        # Sort learned clauses by activity
        learned_with_activity = []
        for idx in self.learned_clauses:
            activity_idx = idx - len(self.original_clauses)
            if activity_idx >= 0 and activity_idx < len(self.clause_activity):
                learned_with_activity.append((self.clause_activity[activity_idx], idx))

        # Keep top 50% most active clauses
        learned_with_activity.sort(reverse=True)
        keep_count = len(learned_with_activity) // 2

        clauses_to_remove = set()
        for _, idx in learned_with_activity[keep_count:]:
            # Don't remove clauses that are reasons for current assignments
            is_reason = any(antecedent == idx for _, _, antecedent in self.trail if antecedent is not None)
            if not is_reason:
                clauses_to_remove.add(idx)

        # Remove clauses from watch lists and clause database
        for clause_idx in clauses_to_remove:
            if clause_idx < len(self.clauses):
                clause = self.clauses[clause_idx]
                # Remove from watch lists
                if len(clause) >= 1:
                    if clause_idx in self.watch_list[clause[0]]:
                        self.watch_list[clause[0]].remove(clause_idx)
                if len(clause) >= 2:
                    if clause_idx in self.watch_list[clause[1]]:
                        self.watch_list[clause[1]].remove(clause_idx)
                # Mark as deleted (set to empty)
                self.clauses[clause_idx] = []

        # Update learned_clauses list
        self.learned_clauses = [idx for idx in self.learned_clauses if idx not in clauses_to_remove]

    def _choose_variable(self) -> Optional[int]:
        """Choose next unassigned variable using activity scores."""
        while self.var_order:
            var = self._heap_pop()
            if self.assignment[var] is None:
                return var
        return None

    def _lit_value(self, lit: int) -> Optional[bool]:
        """Get value of literal (True/False/None)."""
        var = abs(lit)
        val = self.assignment[var]
        if val is None:
            return None
        return val if lit > 0 else not val

    def _var_level(self, var: int) -> int:
        """Get decision level where variable was assigned."""
        for lit, level, _ in self.trail:
            if abs(lit) == var:
                return level
        return -1

    def _get_antecedent(self, var: int) -> Optional[int]:
        """Get antecedent clause index for variable."""
        for lit, _, antecedent in self.trail:
            if abs(lit) == var:
                return antecedent
        return None

    def _bump_activity(self, var: int):
        """Increase activity score of variable."""
        self.activity[var] += self.activity_inc

        # Rescale if necessary
        if self.activity[var] > 1e100:
            for v in range(1, self.num_vars + 1):
                self.activity[v] *= 1e-100
            self.activity_inc *= 1e-100

        # Update heap
        if var in self.var_pos:
            self._heap_decrease(var)

    def _decay_activities(self):
        """Decay all activity scores."""
        self.activity_inc /= self.activity_decay

    # Heap operations for variable ordering (max-heap based on activity)

    def _heap_insert(self, var: int):
        """Insert variable into heap."""
        if var in self.var_pos:
            return
        self.var_pos[var] = len(self.var_order)
        self.var_order.append(var)
        self._heap_decrease(var)

    def _heap_pop(self) -> Optional[int]:
        """Remove and return variable with highest activity."""
        if not self.var_order:
            return None

        var = self.var_order[0]
        last = self.var_order.pop()
        del self.var_pos[var]

        if self.var_order:
            self.var_order[0] = last
            self.var_pos[last] = 0
            self._heap_percolate_down(0)

        return var

    def _heap_decrease(self, var: int):
        """Update heap after increasing activity of var."""
        if var not in self.var_pos:
            return
        pos = self.var_pos[var]

        while pos > 0:
            parent = (pos - 1) // 2
            if self.activity[self.var_order[parent]] >= self.activity[var]:
                break

            # Swap with parent
            self.var_order[pos], self.var_order[parent] = self.var_order[parent], self.var_order[pos]
            self.var_pos[self.var_order[pos]] = pos
            self.var_pos[self.var_order[parent]] = parent
            pos = parent

    def _heap_percolate_down(self, pos: int):
        """Restore heap property downward from pos."""
        size = len(self.var_order)
        var = self.var_order[pos]

        while True:
            left = 2 * pos + 1
            right = 2 * pos + 2
            largest = pos

            if left < size and self.activity[self.var_order[left]] > self.activity[self.var_order[largest]]:
                largest = left
            if right < size and self.activity[self.var_order[right]] > self.activity[self.var_order[largest]]:
                largest = right

            if largest == pos:
                break

            # Swap
            self.var_order[pos], self.var_order[largest] = self.var_order[largest], self.var_order[pos]
            self.var_pos[self.var_order[pos]] = pos
            self.var_pos[self.var_order[largest]] = largest
            pos = largest

    def _get_stats(self, start_time: float) -> Dict:
        """Get solver statistics."""
        return {
            'decisions': self.num_decisions,
            'propagations': self.num_propagations,
            'conflicts': self.num_conflicts,
            'learned': self.num_learned,
            'restarts': self.num_restarts,
            'time': time.time() - start_time
        }
