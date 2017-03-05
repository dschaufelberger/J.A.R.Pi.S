import jarpis.dialogs


class DialogManager:

    def __init__(self, discourse_trees=None):
        if discourse_trees is None:
            discourse_trees = []

        self._discourse_trees = discourse_trees
        self._register_events()

    def _register_events(self):
        # semantic interpreter events
        jarpis.dialogs.communication.register(
            "interpretationSuccessfull", self._insert_into_discourse_trees)
        jarpis.dialogs.communication.register(
            "nothingToInterpret", self._nothing_to_interpret)
        jarpis.dialogs.communication.register(
            "interpretationFinished", self._start_semantic_evaluation)

        # discourse analysis events
        jarpis.dialogs.communication.register(
            "evaluationSuccessfull", self._semantic_object_evaluated)
        jarpis.dialogs.communication.register(
            "evaluationFailed", self._semantic_object_evaluation_failed)
        jarpis.dialogs.communication.register(
            "invalidInformation", self._invalid_semantic_object_information)

    def _insert_into_discourse_trees(self, semantic_object):
        rooted_trees = []
        for tree in self._discourse_trees:
            tree.insert(semantic_object)
            if tree.is_rooted():
                rooted_trees.append(tree)

        self._rooted_trees = rooted_trees

    def _start_semantic_evaluation(self):
        # evaluation algorithm:

        # 1 select the best rooted tree
        # 2 get unresolved semantic object from non-empty DU
        # 3 request evaluation for the semantic object
        # 4 respond to event:
        #       success -> go to 2.
        #       failure -> error handling
        #       invalid -> error handling
        # 5 handle empty DU (ask user)

        pass

    def _nothin_to_interpret(self):
        pass

    def _semantic_object_evaluated(self, semantic_object):
        pass

    def _semantic_object_evaluation_failed(self, semantic_object):
        pass

    def _invalid_semantic_object_information(self, semantic_object):
        pass


class DiscourseTree:

    def __init__(self, root_node):
        self._tree_root = root_node

    def insert(self, semantic_object):
        def visit(self, discourse_unit):
            type_fits = discourse_unit.entity_type == semantic_object.entity_type
            contains_no_object = discourse_unit.semantic_object is None

            if type_fits and contains_no_object:
                discourse_unit.semantic_object = semantic_object
            else:
                for child in discourse_unit._children.accept_visitor(visit)

        self._tree_root.accept_visitor(visit)

    def is_rooted(self):
        return self._tree_root.semantic_object is not None


class DiscourseUnit:

    def __init__(self, evaluation_strategy, entity_type, children):
        self._evaluation_strategy = evaluation_strategy
        self._is_resolved = False
        self._type = entity_type
        self._children = children
        self._semantic_object = None

    def resolve(self):
        self._is_resolved = True

    @property
    def _is_resolved(self):
        return self._is_resolved

    @property
    def semantic_object(self):
        return self._semantic_object

    @semantic_object.setter
    def semantic_object(self, value):
        self._semantic_object = value

    @property
    def entity_type(self):
        return self._type

    def accept_visitor(self, visit):
        visit(self)


class SemanticEvaluationError(Exception):
    pass
