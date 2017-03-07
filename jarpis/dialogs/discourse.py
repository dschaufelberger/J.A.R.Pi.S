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
            "interpretationFinished", self.start_semantic_evaluation)

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

    def start_semantic_evaluation(self):
        communication = jarpis.dialogs.communication

        discourse_tree = self._select_discourse_tree()
        if discourse_tree is None:
            # render response and retrieve further information from the user
            communication.publish("noFittingDiscourseTreeFound")
            return

        object_to_resolve = discourse_tree.get_next_unresolved_semantic_object()
        if object_to_resolve is not None:
            communication.publish("evaluationRequest", object_to_resolve)
        else:
            empty_discourse_unit = discourse_tree.get_next_empty_discourse_unit()

            # The rendered response must contain information about the needed entity type
            # e. g. "Which event (entity_type) would you like to move?".
            # Is this enough? Where does the whole response text come from? Stored in the most
            # detailed entity semantic class?
            communication.publish(
                "furtherInformationRequest", empty_discourse_unit.entity_type)

    def _select_discourse_tree(self):
        # TODO need some place to reset the _current_discourse_tree after
        # semantic binding
        if self._current_discourse_tree is not None:
            return self._current_discourse_tree
        else:
            if len(self._rooted_trees) > 0:
                self._set_current_discourse_tree(self._rooted_trees[0])
                return self._current_discourse_tree

            # TODO is a Nullobject-pattern-like tree an option?
            return None

    def _set_current_discourse_tree(self, tree):
        self._current_discourse_tree = tree

    def _reset_current_discourse_tree(self):
        del self._current_discourse_tree

    def _nothing_to_interpret(self):
        jarpis.dialogs.communication.publish("renderLatestResponse")

    def _semantic_object_evaluated(self, semantic_object):
        # TODO need to know which semantic_object was evaluated
        pass

    def _semantic_object_evaluation_failed(self, semantic_object):
        pass

    def _invalid_semantic_object_information(self, semantic_object):
        pass


class DiscourseTree:

    def __init__(self, root_node):
        self._tree_root = root_node

    def insert(self, semantic_object):
        class InsertionVisitor:

            def visit(self, discourse_unit):
                type_fits = discourse_unit.entity_type == semantic_object.entity_type
                contains_no_object = discourse_unit.semantic_object is None

                if type_fits and contains_no_object:
                    discourse_unit.semantic_object = semantic_object
                else:
                    for child in discourse_unit._children:
                        child.accept_visitor(self)

        self._tree_root.accept_visitor(InsertionVisitor())

    def is_rooted(self):
        return self._tree_root.semantic_object is not None

    def get_next_unresolved_semantic_object(self):
        class UnresolvedObjectVisitor:

            def visit(self, discourse_unit):
                if discourse_unit.has_unresolved_children():
                    child = discourse_unit.next_unresolved_child()
                    child.accept_visitor(self)
                else:
                    self.semantic_object = discourse_unit.semantic_object

        visitor = UnresolvedObjectVisitor()
        self._tree_root.accept_visitor(visitor)
        return visitor.semantic_object

    def get_next_empty_discourse_unit(self):
        class EmpyDiscourseUnitVisitor:

            def visit(self, discourse_unit):
                if discourse_unit.has_empty_children():
                    child = discourse_unit.next_empty_child()
                    child.accept_visitor(self)
                else:
                    self.discourse_unit = discourse_unit

        visitor = EmpyDiscourseUnitVisitor()
        self._tree_root.accept_visitor(visitor)
        return visitor.discourse_unit


class DiscourseUnit:

    def __init__(self, evaluation_strategy, entity_type, children):
        self._evaluation_strategy = evaluation_strategy
        self._is_resolved = False
        self._type = entity_type
        self._children = children
        self._semantic_object = None

    @property
    def is_resolved(self):
        return self._is_resolved and self.semantic_object is not None

    @property
    def semantic_object(self):
        return self._semantic_object

    @semantic_object.setter
    def semantic_object(self, value):
        self._semantic_object = value

    @property
    def entity_type(self):
        return self._type

    def accept_visitor(self, visitor):
        visitor.visit(self)

    def resolve(self):
        self._is_resolved = True

    def has_unresolved_children(self):
        unresolved = self._get_children_by_condition(
            lambda child: (not child.is_resolved))
        return len(unresolved) > 0

    def has_empty_children(self):
        empty = self._get_children_by_condition(
            lambda child: (child.semantic_object is None))
        return len(empty) > 0

    def _get_children_by_condition(self, matches):
        return [child for child in self._children if matches(child)]

    def next_unresolved_child(self):
        unresolved = self._get_unresolved_children()

        if len(unresolved) > 0:
            return unresolved[0]

        return None

    def next_empty_child(self):
        empty = self._get_empty_children()

        if len(empty) > 0:
            return empty[0]

        return None


class SemanticEvaluationError(Exception):
    pass
