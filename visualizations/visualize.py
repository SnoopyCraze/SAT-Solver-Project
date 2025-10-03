"""Visualization tools for SAT solver analysis."""

import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
import json


class SearchTreeVisualizer:
    """Visualize the search tree of DPLL/CDCL solver."""

    def __init__(self):
        self.tree = nx.DiGraph()
        self.node_id = 0
        self.node_labels = {}

    def add_decision(self, parent_id: Optional[int], var: int, value: bool, level: int) -> int:
        """
        Add a decision node to the search tree.

        Args:
            parent_id: Parent node ID (None for root)
            var: Variable decided
            value: Value assigned
            level: Decision level

        Returns:
            Node ID of created node
        """
        node_id = self.node_id
        self.node_id += 1

        label = f"x{var}={value}\nL{level}"
        self.node_labels[node_id] = label
        self.tree.add_node(node_id, var=var, value=value, level=level, type='decision')

        if parent_id is not None:
            self.tree.add_edge(parent_id, node_id)

        return node_id

    def add_conflict(self, parent_id: int) -> int:
        """
        Add a conflict node.

        Args:
            parent_id: Parent node ID

        Returns:
            Node ID of created node
        """
        node_id = self.node_id
        self.node_id += 1

        self.node_labels[node_id] = "CONFLICT"
        self.tree.add_node(node_id, type='conflict')
        self.tree.add_edge(parent_id, node_id)

        return node_id

    def add_solution(self, parent_id: int) -> int:
        """
        Add a solution node.

        Args:
            parent_id: Parent node ID

        Returns:
            Node ID of created node
        """
        node_id = self.node_id
        self.node_id += 1

        self.node_labels[node_id] = "SAT"
        self.tree.add_node(node_id, type='solution')
        self.tree.add_edge(parent_id, node_id)

        return node_id

    def visualize(self, output_file: str = 'search_tree.png', max_nodes: int = 100):
        """
        Visualize the search tree.

        Args:
            output_file: Output image file
            max_nodes: Maximum number of nodes to display (for large trees)
        """
        if len(self.tree.nodes) == 0:
            print("Empty search tree")
            return

        # Sample nodes if tree is too large
        if len(self.tree.nodes) > max_nodes:
            print(f"Tree has {len(self.tree.nodes)} nodes, sampling {max_nodes}")
            # Keep root and do BFS to get first max_nodes nodes
            nodes_to_keep = []
            queue = [0]
            visited = set([0])
            while queue and len(nodes_to_keep) < max_nodes:
                node = queue.pop(0)
                nodes_to_keep.append(node)
                for child in self.tree.successors(node):
                    if child not in visited:
                        visited.add(child)
                        queue.append(child)

            subtree = self.tree.subgraph(nodes_to_keep)
        else:
            subtree = self.tree

        # Layout
        pos = nx.spring_layout(subtree, k=2, iterations=50)

        # Colors based on node type
        colors = []
        for node in subtree.nodes():
            node_type = subtree.nodes[node].get('type', 'decision')
            if node_type == 'conflict':
                colors.append('red')
            elif node_type == 'solution':
                colors.append('green')
            else:
                colors.append('lightblue')

        # Draw
        plt.figure(figsize=(12, 8))
        nx.draw(subtree, pos, node_color=colors, with_labels=False,
                node_size=500, arrows=True)

        # Labels
        labels = {node: self.node_labels.get(node, str(node)) for node in subtree.nodes()}
        nx.draw_networkx_labels(subtree, pos, labels, font_size=8)

        plt.title("SAT Solver Search Tree")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Search tree saved to {output_file}")


class ImplicationGraphVisualizer:
    """Visualize implication graph during conflict analysis."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_labels = {}

    def add_decision(self, lit: int, level: int):
        """Add a decision literal."""
        self.graph.add_node(lit, level=level, type='decision')
        self.node_labels[lit] = f"{lit}@{level}"

    def add_implication(self, lit: int, level: int, antecedent_lits: List[int]):
        """
        Add an implied literal.

        Args:
            lit: Implied literal
            level: Decision level
            antecedent_lits: Literals that caused the implication
        """
        self.graph.add_node(lit, level=level, type='implied')
        self.node_labels[lit] = f"{lit}@{level}"

        for ante_lit in antecedent_lits:
            if ante_lit != lit:
                self.graph.add_edge(ante_lit, lit)

    def add_conflict(self, conflict_lits: List[int]):
        """
        Add conflict node.

        Args:
            conflict_lits: Literals in conflict clause
        """
        self.graph.add_node('CONFLICT', level=-1, type='conflict')
        self.node_labels['CONFLICT'] = 'CONFLICT'

        for lit in conflict_lits:
            if lit in self.graph:
                self.graph.add_edge(lit, 'CONFLICT')

    def visualize(self, output_file: str = 'implication_graph.png',
                  highlight_uip: Optional[int] = None):
        """
        Visualize the implication graph.

        Args:
            output_file: Output image file
            highlight_uip: Literal to highlight as UIP
        """
        if len(self.graph.nodes) == 0:
            print("Empty implication graph")
            return

        # Layout - hierarchical by decision level
        pos = nx.spring_layout(self.graph, k=1, iterations=50)

        # Colors
        colors = []
        for node in self.graph.nodes():
            if node == 'CONFLICT':
                colors.append('red')
            elif node == highlight_uip:
                colors.append('yellow')
            elif self.graph.nodes[node].get('type') == 'decision':
                colors.append('lightgreen')
            else:
                colors.append('lightblue')

        # Draw
        plt.figure(figsize=(12, 8))
        nx.draw(self.graph, pos, node_color=colors, with_labels=False,
                node_size=800, arrows=True, edge_color='gray')

        # Labels
        nx.draw_networkx_labels(self.graph, pos, self.node_labels, font_size=10)

        plt.title("Implication Graph" + (f" (UIP: {highlight_uip})" if highlight_uip else ""))
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Implication graph saved to {output_file}")


def plot_solver_comparison(results: Dict[str, Dict], output_file: str = 'comparison.png'):
    """
    Plot comparison of solver results.

    Args:
        results: Dictionary mapping solver name to statistics
        output_file: Output image file
    """
    solvers = list(results.keys())
    metrics = ['decisions', 'propagations', 'conflicts', 'time']

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        values = [results[solver].get(metric, 0) for solver in solvers]

        ax.bar(solvers, values, color=['blue', 'orange', 'green'][:len(solvers)])
        ax.set_ylabel(metric.capitalize())
        ax.set_title(f'{metric.capitalize()} Comparison')
        ax.grid(axis='y', alpha=0.3)

        # Log scale for time
        if metric == 'time':
            ax.set_yscale('log')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Comparison plot saved to {output_file}")


def plot_performance_scatter(our_times: List[float], reference_times: List[float],
                             instance_names: List[str], output_file: str = 'scatter.png'):
    """
    Create scatter plot comparing solving times.

    Args:
        our_times: List of solving times for our solver
        reference_times: List of solving times for reference solver
        instance_names: Names of instances
        output_file: Output image file
    """
    plt.figure(figsize=(10, 10))

    plt.scatter(reference_times, our_times, alpha=0.6, s=50)

    # Diagonal line (equal performance)
    max_time = max(max(our_times), max(reference_times))
    plt.plot([0, max_time], [0, max_time], 'r--', label='Equal performance')

    plt.xlabel('Reference Solver Time (s)')
    plt.ylabel('Our Solver Time (s)')
    plt.title('Solving Time Comparison')
    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Scatter plot saved to {output_file}")


if __name__ == '__main__':
    # Example usage
    viz = SearchTreeVisualizer()
    root = viz.add_decision(None, 1, True, 1)
    child1 = viz.add_decision(root, 2, True, 2)
    viz.add_conflict(child1)
    child2 = viz.add_decision(root, 2, False, 2)
    viz.add_solution(child2)
    viz.visualize('example_tree.png')

    # Implication graph example
    impl_viz = ImplicationGraphVisualizer()
    impl_viz.add_decision(1, 1)
    impl_viz.add_implication(2, 1, [1])
    impl_viz.add_implication(-3, 1, [1, 2])
    impl_viz.add_conflict([2, -3])
    impl_viz.visualize('example_impl.png', highlight_uip=2)
