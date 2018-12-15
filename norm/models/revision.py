"""A collection of ORM sqlalchemy models for Revision"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, ForeignKey, Text, orm, JSON
from sqlalchemy import Table
from sqlalchemy.orm import relationship

from norm.models.mixins import ParametrizedMixin
from norm.models.norm import Lambda, Variable
import norm.config as config

from pandas import DataFrame
import pandas as pd

import logging
logger = logging.getLogger(__name__)

Model = config.Model
metadata = Model.metadata
user_model = config.user_model


class Revision(Model, ParametrizedMixin):
    """Revision of the Lambda. All revisions for the same version are executed in memory."""
    __tablename__ = 'revisions'
    category = Column(String(128))

    PARQUET_EXT = 'parq'

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, default='')
    lambda_id = Column(Integer, ForeignKey("lambdas.id"))
    lam = relationship(Lambda, back_populates="revisions")

    __mapper_args__ = {
        'polymorphic_identity': 'revision',
        'polymorphic_on': category
    }

    def __init__(self, query):
        self.query = query

    def save(self):
        """
        Save revision information
        """
        raise NotImplementedError

    def apply(self):
        """
        Apply revision on the Lambda
        """
        raise NotImplementedError

    def redo(self):
        """
        Re-apply revision on the Lambda
        """
        raise NotImplementedError

    def undo(self):
        """
        Revert the revision on the Lambda
        """
        raise NotImplementedError


revision_variable = Table(
    'revision_variable', metadata,
    Column('id', Integer, primary_key=True),
    Column('revision_id', Integer, ForeignKey('revisions.id')),
    Column('variable_id', Integer, ForeignKey('variables.id'))
)


class SchemaRevision(Revision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_schema'
    }

    renames = Column(JSON, default={})
    variables = relationship(Variable, secondary=revision_variable)

    def __init__(self):
        super().__init__('')

    def save(self):
        pass

    def redo(self):
        self.apply()


class AddVariableRevision(SchemaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_schema_add'
    }

    def __init__(self, variables):
        super().__init__()
        assert(isinstance(variables, list))
        assert(all(isinstance(v, Variable) for v in variables))
        self.variables = variables
        current_variable_names = set((v.name for v in self.lam.variables))
        new_variable_names = set((v.name for v in variables))
        assert(current_variable_names.isdisjoint(new_variable_names))

    def apply(self):
        self.lam.variables.extends(self._variables)

    def undo(self):
        for v in reversed(self._variables):
            vp = self.lam.variables.pop()
            assert(v.name == vp.name)


class RenameVariableRevision(SchemaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_schema_rename'
    }

    def __init__(self, renames):
        super().__init__()
        assert(isinstance(renames, dict))
        self.renames = renames
        current_variable_names = set((v.name for v in self.lam.variables))
        old_names = set(renames.keys())
        assert(old_names.issubset(current_variable_names))

    def apply(self):
        for v in self.lam.variables:
            new_name = self.renames.get(v.name)
            if new_name is not None:
                v.name = new_name

    def undo(self):
        renames_r = dict((new_name, old_name) for old_name, new_name in self.renames.items())
        for v in self.lam.variables:
            old_name = renames_r.get(v.name)
            if old_name is not None:
                v.name = old_name


class RetypeVariableRevision(SchemaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_schema_rename'
    }

    def __init__(self, variables):
        super().__init__()
        assert(isinstance(variables, list))
        self.variables = variables
        current_variable_names = set((v.name for v in self.lam.variables))
        variable_names = set((v.name for v in variables))
        assert(len(variables) == len(variable_names))
        assert(variable_names.issubset(current_variable_names))
        self.variables.extend([v for v in self.lam.variables if v.name in variable_names])

    @property
    def num(self):
        return int(len(self.variables) / 2)

    def apply(self):
        to_variables = self.variables[:self.num]
        retypes = dict((v.name, v.type_) for v in to_variables)
        for v in self.lam.variables:  # type: Variable
            t = retypes.get(v.name)
            if t is not None:
                v.type_ = t

    def undo(self):
        from_variables = self.variables[self.num:]
        retypes = dict((v.name, v.type_) for v in from_variables)
        for v in self.lam.variables:  # type: Variable
            t = retypes.get(v.name)
            if t is not None:
                v.type_ = t


class DeleteVariableRevision(SchemaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_schema_delete'
    }

    def __init__(self, names):
        super().__init__()
        assert(isinstance(names, list))
        self.renames = dict((name, '') for name in names)
        current_variable_names = set((v.name for v in self.lam.variables))
        assert(set(names).issubset(current_variable_names))
        self.variables = [v for v in self.lam.variables]

    def apply(self):
        self.lam.variables = [v for v in self.lam.variables if v.name not in self.renames]

    def undo(self):
        self.lam.variables = [v for v in self.lam.variables]


class DeltaRevision(Revision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_delta'
    }

    def __init__(self, query):
        super().__init__(query)
        self._delta = None

    @orm.reconstructor
    def init_on_load(self):
        self._delta = None

    @property
    def path(self):
        return '{}/{}.{}'.format(self.lam.folder, self.id, self.PARQUET_EXT)

    @property
    def delta(self):
        """
        Retrieve the delta. Load from path if not in memory.
        :return: the delta DataFrame
        :rtype: DataFrame
        """
        if self._delta is not None:
            return self._delta

        try:
            self._delta = pd.read_parquet(self.path)
        except FileNotFoundError:
            msg = 'Can not find delta from {}'.format(self.path)
            logger.error(msg)
            raise RuntimeError(msg)
        except:
            self._delta = None
        return self._delta

    @delta.setter
    def delta(self, delta):
        """
        Set the delta if it is not set yet.
        :type delta: DataFrame
        """
        if self._delta is None:
            self._delta = delta

    def save(self):
        if self.delta is None:
            return

        try:
            self._delta.to_parquet(self.path)
        except IOError:
            msg = 'IO problem: can not save delta to {}'.format(self.path)
            logger.error(msg)
            raise
        except:
            msg = 'Other problem: can not save delta to {}'.format(self.path)
            logger.error(msg)
            raise


class ConjunctionRevision(DeltaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_delta_conjunction'
    }

    def __init__(self, query):
        super().__init__(query)

    def apply(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


class DisjunctionRevision(DeltaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_delta_disjunction'
    }

    def __init__(self, query):
        super().__init__(query)

    def apply(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


class FitRevision(DeltaRevision):

    __mapper_args__ = {
        'polymorphic_identity': 'revision_delta_fit'
    }

    def __init__(self, query):
        super().__init__(query)

    def apply(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass
