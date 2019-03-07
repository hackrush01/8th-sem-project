class Graph(object):
    def __init__(self, graph_file, weights_file, reverse: bool = False):
        self.num_nodes = None
        self.graph = None
        self.ratio_matrix = None
        self.reverse = reverse

        self.create_graph(graph_file)
        self.set_ratio_matrix(weights_file)

    @staticmethod
    def _get_edge(n1: int, n2: int):
        return 'x{}{}'.format(n1, n2)

    def create_graph(self, graph_file):
        self.graph = {}

        with open(graph_file, 'r') as f:
            for line in f:
                if line.startswith("#"):
                    continue
                if self.num_nodes is None:
                    self.num_nodes = int(line.strip())
                else:
                    e1, e2, cap = line.strip().split()
                    edge = 'x' + e1 + e2
                    cap = int(cap)
                    if not self.graph.get(edge):
                        self.graph[edge] = cap
                    else:
                        if self.graph.get(edge) != cap:
                            raise ValueError("Ambiguous capacity value for "
                                             "edge {} {}".format(e1, e2))

    def set_ratio_matrix(self, ratio_file):
        num_nodes = None
        with open(ratio_file, 'r') as f:
            for line in f:
                if line.startswith("#"):
                    continue
                if num_nodes is None:
                    num_nodes = int(line.strip())
                    self.ratio_matrix = list()
                else:
                    row = (
                        list(map(int, line.strip().split()))
                    )
                    self.ratio_matrix.append(row)

    @staticmethod
    def _return_edge(edge: str, **_kwargs):
        return edge

    @staticmethod
    def _return_inequation(edge, **kwargs):
        return "{} <= {};".format(edge, kwargs.get('cap'))

    @staticmethod
    def _return_ratio_ineqations(edge, **kwargs):
        if edge == kwargs.get('fixed_edge'):
            return
        return "{} {} = {} {};".format(
            kwargs.get('ratio'), kwargs.get('fixed_edge'),
            kwargs.get('fixed_ratio'), edge
        )

    def _iterate_ratio_matrix(self, function):
        assert self.graph is not None
        assert self.ratio_matrix is not None

        for i, row in enumerate(self.ratio_matrix, start=1):
            fixed_edge, fixed_ratio = None, None
            if self.reverse:
                row = row[:i]
                start = 1
            else:
                row = row[i:]
                start = i + 1

            for j, ratio in enumerate(row, start=start):
                edge = self._get_edge(i, j)

                if ratio > 0:
                    cap = self.graph.get(edge)
                    if fixed_ratio is None and fixed_edge is None:
                        fixed_edge, fixed_ratio = edge, ratio
                    if cap:
                        yield function(
                            edge,
                            cap=cap,
                            fixed_edge=fixed_edge,
                            fixed_ratio=fixed_ratio,
                            ratio=ratio
                        )
                    else:
                        raise ValueError("Missing edge {} from the input"
                                         .format(edge))

    def get_objective_equation(self):
        objective = "max:"
        for edge in self._iterate_ratio_matrix(self._return_edge):
            objective += " + " + edge
        objective += ';'

        return objective

    def gen_bounds(self):
        return self._iterate_ratio_matrix(self._return_inequation)

    def gen_constraints(self):
        return self._iterate_ratio_matrix(self._return_ratio_ineqations)


if __name__ == '__main__':
    reverse = True

    graph = Graph(
        graph_file="Examples\\test_ILP.graph",
        weights_file="Examples\\test_ILP.weights",
        reverse=reverse
    )

    if reverse:
        filename = "optimised_flow_rev.lp"
    else:
        filename = "optimised_flow.lp"

    with open(filename, 'w') as f:
        f.write("/* Objective function */" + '\n')
        f.write(graph.get_objective_equation() + '\n')

        f.write('\n' + "/* Variable bounds */" + '\n')
        for bound in graph.gen_bounds():
            f.write(bound + '\n')

        f.write('\n' + "/* Constraints */" + '\n')
        for constraint in graph.gen_constraints():
            if constraint is not None:
                f.write(constraint + '\n')
