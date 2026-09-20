from propagation_recorder.domain.models import CouplingEstimate, PropagationGraph


class StdoutReporter:
    def emit(self, estimate: CouplingEstimate) -> None:
        w = estimate.window
        print(
            f"window {w.start.isoformat()} .. {w.end.isoformat()}: "
            f"k={estimate.k:.3f} coupled={estimate.coupled_actions} total={estimate.total_actions}"
        )

    def emit_graph(self, graph: PropagationGraph) -> None:
        edges = len(graph.productions) + len(graph.consumptions)
        print(f"graph: {len(graph.actions)} nodes, {edges} edges")
