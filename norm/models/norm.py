"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import errno

from datetime import datetime
import enum

from future.standard_library import install_aliases

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, Enum, desc, UniqueConstraint, orm
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, with_polymorphic
from sqlalchemy.ext.orderinglist import ordering_list

from norm.models.mixins import lazy_property, ParametrizedMixin, new_version
from norm.models.license import License
from norm.utils import current_user
import norm.config as config

from pandas import DataFrame
import pandas as pd
import numpy as np

import logging
logger = logging.getLogger(__name__)

install_aliases()

Model = config.Model
metadata = Model.metadata
user_model = config.user_model


class Variable(Model, ParametrizedMixin):
    """Variable placeholder"""

    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    name = Column(String(256), default='')
    type_id = Column(Integer, ForeignKey('lambdas.id'))
    type_ = relationship('Lambda', foreign_keys=[type_id])

    def __init__(self, name, type_):
        """
        Construct the variable
        :param name: the full name of the variable
        :type name: str
        :param type_: the type of the variable
        :type type_: Lambda
        """
        self.id = None
        self.name = name
        self.type_ = type_


lambda_variable = Table(
    'lambda_variable', metadata,
    Column('id', Integer, primary_key=True),
    Column('lambda_id', Integer, ForeignKey('lambdas.id')),
    Column('variable_id', Integer, ForeignKey('variables.id')),
)


class Status(enum.Enum):
    """
    Indicate whether the lambda function can be modified or not
    """
    DRAFT = 0
    READY = 1


class Level(enum.IntEnum):
    """
    Different computational level for Lambda functions:
        1. any function that can compute the outputs given inputs is at level computable.
        2. any function that can record the input-output as data such that a query can search through data to provide
           statistics and aggregations is at level queryable.
        3. any function that can adapt the parameters by fitting the recorded input-output data with respect to a
           certain objective function.
    """
    COMPUTABLE = 0
    QUERYABLE = 1
    ADAPTABLE = 2


def default_version(context):
    params = context.get_current_parameters()
    namespace = params['namespace']
    name = params['name']
    return new_version(namespace, name)


class Lambda(Model, ParametrizedMixin):
    """Lambda model is a function"""
    __tablename__ = 'lambdas'
    category = Column(String(128))

    COLUMN_OUTPUT = 'output'
    COLUMN_LABEL = 'label'
    COLUMN_LABEL_T = 'float'
    COLUMN_OID = 'oid'
    COLUMN_OID_T = 'object'
    COLUMN_PROB = 'prob'
    COLUMN_PROB_T = 'float'
    COLUMN_TIMESTAMP = 'timestamp'
    COLUMN_TIMESTAMP_T = 'datetime64[ns]'
    COLUMN_TENSOR = 'tensor'
    COLUMN_TOMBSTONE = 'tombstone'
    COLUMN_TOMBSTONE_T = 'bool'

    # identifiers
    id = Column(Integer, primary_key=True, autoincrement=True)
    namespace = Column(String(512), default='')
    name = Column(String(256), nullable=False)
    # data type
    dtype = Column(String(16), default='object')
    # tensor type and shape
    ttype = Column(String(16), default='float32')
    shape = Column(ARRAY(Integer), default=[100])
    # complexity level
    level = Column(Enum(Level), default=Level.COMPUTABLE)
    # owner
    created_by_id = Column(Integer, ForeignKey(user_model.id))
    owner = relationship(user_model, backref='lambdas', foreign_keys=[created_by_id])
    # audition
    created_on = Column(DateTime, default=datetime.now)
    changed_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # schema
    description = Column(Text, default='')
    variables = relationship(Variable, secondary=lambda_variable)
    # version
    anchor = Column(Boolean, default=True)
    cloned_from_id = Column(Integer, ForeignKey('lambdas.id'))
    cloned_from = relationship('Lambda', remote_side=[id])
    merged_from_ids = Column(ARRAY(Integer))
    version = Column(Integer, default=default_version, nullable=False)
    # revision
    revisions = relationship('Revision', order_by='Revision.position', collection_class=ordering_list('position'))
    current_revision = Column(Integer, default=-1)
    status = Column(Enum(Status), default=Status.DRAFT)
    # license
    license_id = Column(Integer, ForeignKey(License.id))
    license = relationship(License, foreign_keys=[license_id])

    __mapper_args__ = {
        'polymorphic_identity': 'lambda',
        'polymorphic_on': category
    }

    __table_args__ = tuple(UniqueConstraint('namespace', 'name', 'version', name='unique_lambda'))

    def __init__(self, namespace='', name='', description='', params='{}', variables=None, dtype=None, ttype=None,
                 shape=None):
        self.id = None
        self.namespace = namespace
        self.name = name
        self.version = None
        self.description = description
        self.params = params
        self.owner = current_user()
        self.status = Status.DRAFT
        self.merged_from_ids = []
        self.variables = variables or []
        self.revisions = []
        self.current_revision = -1
        self.dtype = dtype or 'object'
        self.ttype = ttype or 'float32'
        self.shape = shape or [100]
        self.anchor = True
        self.level = Level.COMPUTABLE
        self.df = None

    @orm.reconstructor
    def init_on_load(self):
        self.df = None

    @hybrid_property
    def nargs(self):
        return len(self.variables)

    @hybrid_property
    def dim(self):
        return len(self.shape)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.signature

    @property
    def signature(self):
        if self.namespace:
            return '@'.join((self.namespace + '.' + self.name, str(self.version)))
        else:
            return '@'.join((self.name, str(self.version)))

    def clone(self):
        """
        Clone itself and bump up the version. Make sure updates are done after clone.
        :return: the cloned version of it
        :rtype: Lambda
        """
        lam = self.__class__(namespace=self.namespace, name=self.name, description=self.description,
                             params=self.params, variables=self.variables)
        lam.cloned_from = self
        lam.anchor = False
        if self.df:
            lam.df = self.df.copy(False)
        return lam

    def merge(self, others):
        """
        Clone itself and merge several other versions into the new version
        :param others: other versions
        :type others: List[Lambda]
        :return: the merged version
        :rtype: Lambda
        """
        assert(all([o.namespace == self.namespace and o.name == self.name for o in others]))

        lam = self.clone()
        lam.merged_from_ids = [o.id for o in others]
        for o in others:
            lam.revisions.extend(o.revisions)
        while not self.end_of_revisions:
            self.forward()
        lam.status = Status.READY
        return lam

    def compact(self):
        """
        Compact this version with previous versions to make an anchor version
        :return:
        """
        raise NotImplementedError

    def _check_draft_status(func):
        """
        A decorator to check whether the current Lambda is in draft status
        :param func: a function to wrap
        :type func: Callable
        :return: a wrapped function
        :rtype: Callable
        """
        def wrapper(self, *args, **kwargs):
            if self.status != Status.DRAFT:
                msg = '{} is not in Draft status. Please clone first to modify'.format(self)
                logger.error(msg)
                raise RuntimeError(msg)
            return func(self, *args, **kwargs)
        return wrapper

    def _only_queryable(func):
        """
        A decorator to bypass the function if the current Lambda is below queryable
        :param func: a function to wrap
        :type func: Callable
        :return: a wrapped function
        :rtype: Callable
        """
        def wrapper(self, *args, **kwargs):
            if self.level < Level.QUERYABLE:
                return
            return func(self, *args, **kwargs)
        return wrapper

    def _only_adaptable(func):
        """
        A decorator to bypass the function if the current Lambda is below adaptable
        :param func: a function to wrap
        :type func: Callable
        :return: a wrapped function
        :rtype: Callable
        """
        def wrapper(self, *args, **kwargs):
            if self.level < Level.ADAPTABLE:
                return
            return func(self, *args, **kwargs)
        return wrapper

    @_check_draft_status
    def conjunction(self):
        """
        Revise with conjunction (AND)
        """
        from norm.models.revision import ConjunctionRevision
        # TODO: implement the query
        revision = ConjunctionRevision('', '')
        self._add_revision(revision)

    @_check_draft_status
    def disjunction(self):
        """
        Revise with disjunction (OR)
        """
        from norm.models.revision import DisjunctionRevision
        # TODO: implement the query
        revision = DisjunctionRevision('', '')
        self._add_revision(revision)

    def fit(self):
        """
        Fit the model with all the existing data
        """
        from norm.models.revision import FitRevision
        # TODO: implement the query
        revision = FitRevision('', '')
        self._add_revision(revision)

    def adapt(self):
        """
        Adapt the model with the data for this version
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def add_variable(self, *variables):
        """
        Add new new variables to the Lambda
        :type variables: Tuple[Variable]
        """
        if len(variables) == 0:
            return
        from norm.models.revision import AddVariableRevision
        revision = AddVariableRevision(list(variables))
        self._add_revision(revision)

    @_check_draft_status
    def delete_variable(self, *names):
        """
        Delete variables from the Lambda
        :type names: Tuple[str]
        """
        if len(names) == 0:
            return
        from norm.models.revision import DeleteVariableRevision
        revision = DeleteVariableRevision(list(names))
        self._add_revision(revision)

    @_check_draft_status
    def rename_variable(self, **renames):
        """
        Change a variable name to another. The argument is a on keyword argument format. The key should exist in
        the Lambda and the value to be the target name.
        :type renames: Dict[str, str]
        """
        if len(renames) == 0:
            return
        from norm.models.revision import RenameVariableRevision
        revision = RenameVariableRevision(renames)
        self._add_revision(revision)

    @_check_draft_status
    def astype(self, *variables):
        """
        Change the type of variables. The variable names to be changed should exist in current Lambda. The new types
        are specified in the variable type_ attribute.
        :type variables: Tuple[Variable]
        """
        if len(variables) == 0:
            return
        from norm.models.revision import RetypeVariableRevision
        revision = RetypeVariableRevision(list(variables))
        self._add_revision(revision)

    def _add_revision(self, revision):
        self.revisions.append(revision)
        revision.apply()
        self.current_revision += 1

    @_check_draft_status
    def save(self):
        """
        Save the current version
        """
        self._save_data()
        self._save_model()

    @property
    def empty_revisions(self):
        return len(self.revisions) == 0

    @property
    def end_of_revisions(self):
        return self.current_revision == len(self.revisions) - 1

    @property
    def begin_of_revisions(self):
        return self.current_revision == -1

    @_check_draft_status
    def rollback(self):
        """
        Rollback to the previous revision if it is in draft status
        """
        if 0 <= self.current_revision < len(self.revisions):
            self.revisions[self.current_revision].undo()
            self.current_revision -= 1
        else:
            if self.current_revision == -1:
                msg = '{} has already rolled back to the beginning of the version.\n ' \
                      'Might want to rollback the version'.format(self)
                logger.warning(msg)
            else:
                msg = 'Current revision {} is higher than it has {}'.format(self.current_revision, len(self.revisions))
                logger.error(msg)
                raise RuntimeError(msg)

    @_check_draft_status
    def forward(self):
        """
        Forward to the next revision if it is in draft status
        """
        if self.current_revision < len(self.revisions) - 1:
            self.revisions[self.current_revision + 1].redo()
            self.current_revision += 1
        else:
            if self.current_revision == len(self.revisions) - 1:
                msg = '{} is already at the latest revision.\n ' \
                      'Might want to forward the version'.format(self)
                logger.warning(msg)
            else:
                msg = 'Current revision {} is higher than it has {}'.format(self.current_revision, len(self.revisions))
                logger.error(msg)
                raise RuntimeError(msg)

    def __call__(self, *args, **kwargs):
        """
        TODO: implement
        """
        raise NotImplementedError

    @property
    def folder(self):
        return '{}/{}/{}'.format(config.DATA_STORAGE_ROOT,
                                 self.namespace.replace('.', '/'),
                                 self.name,
                                 self.version)

    @_only_queryable
    def _create_folder(self):
        """
        Create the folder for the namespace.
        """
        # TODO: abstract the data storage folder creation
        try:
            # for the case of concurrent processing
            os.makedirs(self.folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                msg = 'Can not create the folder {}'.format(self.folder)
                logger.error(msg)
                logger.error(str(e))
                raise e

    @property
    def _tensor_columns(self):
        return ['{}_{}'.format(self.COLUMN_TENSOR, i) for i in range(int(np.prod(self.shape)))]

    @property
    def _all_columns(self):
        return [self.COLUMN_OID, self.COLUMN_PROB, self.COLUMN_LABEL, self.COLUMN_TIMESTAMP,
                self.COLUMN_TOMBSTONE] + self._tensor_columns + [v.name for v in self.variables]

    @property
    def _all_column_types(self):
        return [self.COLUMN_OID_T, self.COLUMN_PROB_T, self.COLUMN_LABEL_T, self.COLUMN_TIMESTAMP_T,
                self.COLUMN_TOMBSTONE_T] + [self.ttype] * len(self._tensor_columns) + \
               [v.type_.dtype for v in self.variables]

    @_only_queryable
    def _empty_data(self):
        """
        Create an empty data frame
        :return: the data frame with columns
        :rtype: DataFrame
        """
        df = DataFrame(columns=self._all_columns)
        return df.astype(dict(zip(self._all_columns, self._all_column_types)))

    @_only_queryable
    def _load_data(self):
        """
        Load data if it exists. If the current version is not an anchor, the previous versions will be combined.
        :return: the combined data
        :rtype: DataFrame
        """
        if self.df is not None:
            return self.df

        if self.anchor:
            self.df = self._empty_data()
        elif self.cloned_from is None:
            msg = "Failed to find the anchor version. The chain is broken for {}".format(self)
            logger.error(msg)
            raise RuntimeError(msg)
        else:
            self.df = self.cloned_from._load_data().copy(False)

        from norm.models.revision import DeltaRevision
        for i in range(self.current_revision + 1):
            revision = self.revisions[i]
            if isinstance(revision, DeltaRevision):
                revision.redo()

        # Choose the rows still alive and the columns specified in schema
        self.df = self.df[self._all_columns][~self.df[self.COLUMN_TOMBSTONE]]
        return self.df

    @_only_queryable
    def _save_data(self):
        """
        Save all revisions' data
        """
        if not os.path.exists(self.folder):
            self._create_folder()

        for revision in self.revisions:
            revision.save()

    @_only_adaptable
    def _build_model(self):
        """
        Build an adaptable model
        """
        raise NotImplementedError

    @_only_adaptable
    def _load_model(self):
        """
        Load an adapted model
        :return:
        """
        raise NotImplementedError

    @_only_adaptable
    def _save_model(self):
        """
        Save an adapted model
        :return:
        """
        raise NotImplementedError

    def query(self, filters=None, projections=None):
        if projections is None:
            df = pd.read_parquet(self.data_file)
        else:
            df = pd.read_parquet(self.data_file, columns=[col[0] for col in projections])
            df = df.rename(columns=dict(projections))
        if filters:
            projections = dict(projections)
            from norm.literals import COP
            for col, op, value in filters:
                pcol = projections.get(col, col)
                df = df[df[pcol].notnull()]
                if op == COP.LK:
                    df = df[df[pcol].str.contains(value.value)]
                elif op == COP.GT:
                    df = df[df[pcol] > value.value]
                elif op == COP.GE:
                    df = df[df[pcol] >= value.value]
                elif op == COP.LT:
                    df = df[df[pcol] < value.value]
                elif op == COP.LE:
                    df = df[df[pcol] <= value.value]
                elif op == COP.EQ:
                    df = df[df[pcol] == value.value]
                elif op == COP.NE:
                    if value.value is not None:
                        df = df[df[pcol] != value.value]
                elif op == COP.IN:
                    # TODO: Wrong
                    df = df[df[pcol].isin(value.value)]
                elif op == COP.NI:
                    # TODO: Wrong
                    df = df[~df[pcol].isin(value.value)]
        return df


class GroupLambda(Lambda):

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_group'
    }

    def all(self):
        """
        Combine the groups as columns
        :return: Lambda
        """
        raise NotImplementedError

    def any(self):
        """
        Combine the groups as concatenation
        :return: Lambda
        """
        raise NotImplementedError


class KerasLambda(Lambda):

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_keras'
    }

    @lazy_property
    def keras_model(self):
        return None

    def __call__(self, *args, **kwargs):
        """
        TODO: implement
        """
        pass


def retrieve_type(namespaces, name, version, session, status=None):
    """
    Retrieving a Lambda
    :type namespaces: str, List[str] or None
    :type name: str
    :type version: int or None
    :type session: sqlalchemy.orm.Session
    :type status: Status or None
    :return: the Lambda or None
    """
    #  find the latest versions
    queries = [Lambda.name == name]
    if status is not None and isinstance(status, Status):
        queries.append(Lambda.status == status)
    if namespaces is not None:
        if isinstance(namespaces, str):
            queries.append(Lambda.namespace == namespaces)
        else:
            queries.append(Lambda.namespace.in_(namespaces))
    if version is not None and isinstance(version, int):
        queries.append(Lambda.version <= version)
    lams = session.query(with_polymorphic(Lambda, '*')) \
                  .filter(*queries) \
                  .order_by(desc(Lambda.version)) \
                  .all()
    if len(lams) == 0:
        return None

    lam = lams[0]  # type: Lambda
    if version is not None and lam.version < version:
        msg = 'The specified version {} does not exist for {}.{}'.format(version, lam.namespace, lam.name)
        raise RuntimeError(msg)

    assert(lam is None or isinstance(lam, Lambda))
    return lam
