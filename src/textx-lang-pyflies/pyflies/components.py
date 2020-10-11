from textx import get_parent_of_type, get_children_of_type
from .evaluated import EvaluatedBase
from .exceptions import PyFliesException


class ComponentTimeInst(EvaluatedBase):
    """
    Represents an evaluated instance of component-time specification
    """
    def __init__(self, spec, context=None, last_comp=None):
        super().__init__(spec, context)
        spec.inst = self
        self.at = spec.at.eval(context).time
        if spec.at.relative_op == '-':
            self.at = -self.at
        relative_to = spec.at.relative_to or last_comp
        if relative_to:
            relative = (spec.at.relative_op is not None
                        or spec.at.start_relative
                        or spec.at.relative_to)
            if relative:
                self.at += relative_to.inst.at
                if not spec.at.start_relative:
                    self.at += relative_to.inst.duration
        self.duration = spec.duration.eval(context)
        self.component = spec.component.eval(context)

    def __repr__(self):
        return 'at {} {} for {}'.format(str(self.at), str(self.component),
                                        str(self.duration))


class ComponentInst(EvaluatedBase):
    """
    An evaluated instance of a component.
    """
    def __init__(self, spec, context=None):
        super().__init__(spec, context)
        test = get_parent_of_type("Test", self.spec)
        if test is None:
            # We are using testing meta-model
            test_name = 'testing'
        else:
            test_name = test.name

        # Calculate component name based on the value provided in the model or
        # component index if name is not given
        if spec.parent.name:
            self.name = '{}_{}'.format(test_name, spec.parent.name)
        else:
            cc_index = spec.parent.parent.parent.components_cond.index(spec.parent.parent)
            index = sum([len(x.comp_times)
                         for x in spec.parent.parent.parent.components_cond[:cc_index]])
            index += spec.parent.parent.comp_times.index(spec.parent)
            # Calculate component instance name if not given in the model
            self.name = '{}_{}_{}'.format(test_name, self.spec.type.name, index)

        # Instantiate parameters
        self._params = {}
        for p in spec.all_params:
            self._params[p.type.name] = p.eval(context)

    @property
    def params(self):
        return list(self._params.values())

    def __getattr__(self, name):
        try:
            return self._params[name].value
        except KeyError:
            raise AttributeError('"{}" object has no attribute "{}"'.format(
                type(self).__name__, name))

    def __repr__(self):
        return '{}({})'.format(self.spec.type.name, ', '.join([str(x) for x in self.params]))


class ComponentParamInst(EvaluatedBase):
    def __init__(self, spec, context=None):
        super().__init__(spec, context)

        # Find out if this param is dependent on trial condition variables
        test = get_parent_of_type("Test", self.spec)
        cond_var_names = test.table_spec.variables
        self.is_constant = all([c.name not in cond_var_names
                                for c in get_children_of_type("VariableRef", spec.value)])

        if not self.is_constant and context is None:
            # Use default value
            self.value = spec.type.default.eval()
        else:
            self.value = self.value.eval(context)

    @property
    def name(self):
        return self.type.name

    def __repr__(self):
        return '{} {}'.format(self.spec.type.name, self.value)
