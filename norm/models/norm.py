"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import errno

from datetime import datetime
from textwrap import dedent
import enum

from future.standard_library import install_aliases

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime, Enum, desc, UniqueConstraint
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, with_polymorphic

from norm.models.mixins import lazy_property, ParametrizedMixin, new_version
from norm.models.license import License
from norm.utils import current_user
import norm.config as config

from pandas import DataFrame
import pandas as pd
import numpy as np

import traceback
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


class RevisionMode(enum.Enum):
    NEW = 0  # a new implementation that discards all previous changes if any
    CON = 1  # a conjunction of logical revisions
    DIS = 2  # a disjunction of logical revisions
    DEL = 3  # a deletion of logical revisions
    MOD = 4  # a modification of variables, e.g., renaming or changing types
    FIT = 5  # a model update


class Revision(Model, ParametrizedMixin):
    """Revision of the Lambda. All revisions for the same version are executed in memory."""
    __tablename__ = 'revisions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(Enum(RevisionMode), default=RevisionMode.NEW, nullable=False)
    query = Column(Text, default='')

    def apply(self, lam):
        """
        Apply revision on the given Lambda
        :param lam: the Lambda function to be applied on
        :type lam: Lambda
        :return: the revised Lambda
        :rtype: Lambda
        """
        raise NotImplementedError

    def delta(self):
        """
        Delta data that can be re-applied on the data.
        :return: the delta data
        :rtype: DataFrame or None
        """
        raise NotImplementedError

    def redo(self, lam):
        """
        Re-apply revision on the given Lambda
        :param lam: the Lambda function to be applied on
        :type lam: Lambda
        :return: the revised Lambda
        :rtype: Lambda
        """
        raise NotImplementedError

    def undo(self, lam):
        """
        Revert the revision of the given Lambda
        :param lam: the Lambda function to be reverted on
        :type lam: Lambda
        :return: the reverted Lambda
        :rtype: Lambda
        """
        raise NotImplementedError


lambda_revision = Table(
    'lambda_revision', metadata,
    Column('id', Integer, primary_key=True),
    Column('lambda_id', Integer, ForeignKey('lambdas.id')),
    Column('revision_id', Integer, ForeignKey('revisions.id')),
)

lambda_variable = Table(
    'lambda_variable', metadata,
    Column('id', Integer, primary_key=True),
    Column('lambda_id', Integer, ForeignKey('lambdas.id')),
    Column('variable_id', Integer, ForeignKey('variables.id'))
)


class Status(enum.Enum):
    DRAFT = 0
    READY = 1


def default_version(context):
    params = context.get_current_parameters()
    namespace = params['namespace']
    name = params['name']
    return new_version(namespace, name)


class Lambda(Model, ParametrizedMixin):
    """Lambda model is a function"""
    __tablename__ = 'lambdas'
    category = Column(String(128))

    PARQUET_EXT = 'parq'

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
    revisions = relationship(Revision, secondary=lambda_revision)
    current_revision = Column(Integer, default=0)
    status = Column(Enum(Status), default=Status.DRAFT)
    # license
    license_id = Column(Integer, ForeignKey(License.id))
    license = relationship(License, foreign_keys=[license_id])
    # price

    __mapper_args__ = {
        'polymorphic_identity': 'lambda',
        'polymorphic_on': category
    }

    __table_args__ = tuple(UniqueConstraint('namespace', 'name', 'version', name='unique_lambda'))

    def __init__(self, namespace='', name='', description='', params='{}', variables=None, dtype=None):
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
        self.current_revision = 0
        self.df = None
        self.dtype = dtype

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

        # TODO: merge implementation
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
                raise RuntimeError(msg)
            return func(self, *args, **kwargs)
        return wrapper

    @_check_draft_status
    def conjunction(self):
        """
        Revise with conjunction (AND)
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def disjunction(self):
        """
        Revise with disjunction (OR)
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def add_variable(self, name, type_):
        """
        Add a new variable into the signature
        :type name: str
        :type type_: Lambda
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def delete_variable(self, name):
        """
        Delete a variable from the signature
        :type name: str
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def rename_variable(self, old_name, new_name):
        """
        Change the variable name
        :type old_name: str
        :type new_name: str
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def astype(self, name, new_type):
        """
        Change the type of the variable
        :type name: str
        :type new_type: Lambda
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def save(self, overwrite=False):
        """
        Save the current version and make it ready
        :param overwrite: whether to overwrite the existing object
        :type overwrite: Boolean
        :return:
        """
        raise NotImplementedError

    @_check_draft_status
    def rollback(self):
        """
        Rollback to the previous revision if it is in draft status
        """
        if 0 < self.current_revision < len(self.revisions):
            revision = self.revisions[self.current_revision]
            revision.undo(self)
            self.current_revision -= 1
        else:
            if self.current_revision == 0:
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
            revision = self.revisions[self.current_revision + 1]
            revision.redo(self)
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
                                 self.name)

    @property
    def path(self):
        return '{}/{}.{}'.format(self.folder, self.version, self.PARQUET_EXT)

    def create_folder(self):
        """
        Create the folder for the namespace.
        """
        # TODO: abstract the data storage folder creation
        try:
            # for the case of concurrent processing
            os.makedirs(self.folder)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def overwrite_with_delta(self, df):
        """
        Overwrite the existing dataframe with the delta dataframe, assuming it is the same Lambda
        with different version.
        :param df: the base DataFrame
        :type df: DataFrame
        :return: the modified DataFrame
        :rtype: DataFrame
        """
        try:
            delta = pd.read_parquet(self.path)
            df.loc[delta.index, delta.columns] = delta.values
        except FileNotFoundError:
            pass
        return df

    @property
    def _tensor_columns(self):
        return ['{}_{}'.format(self.COLUMN_TENSOR, i) for i in np.prod(self.shape)]

    @property
    def _tensor_column_types(self):
        return [('{}_{}'.format(self.COLUMN_TENSOR, i), self.ttype) for i in np.prod(self.shape)]

    def empty_data(self):
        """
        Create an empty data frame
        :return: the data frame with columns
        :rtype: DataFrame
        """
        df = DataFrame(columns=[self.COLUMN_OID, self.COLUMN_PROB, self.COLUMN_LABEL, self.COLUMN_TIMESTAMP,
                                self.COLUMN_TOMBSTONE] + self._tensor_columns + [v.name for v in self.variables])
        types = dict([(self.COLUMN_OID, self.COLUMN_OID_T),
                      (self.COLUMN_PROB, self.COLUMN_PROB_T),
                      (self.COLUMN_LABEL, self.COLUMN_LABEL_T),
                      (self.COLUMN_TIMESTAMP, self.COLUMN_TIMESTAMP_T),
                      (self.COLUMN_TOMBSTONE, self.COLUMN_TOMBSTONE_T)]
                     + self._tensor_column_types
                     + [(v.name, v.type_.dtype) for v in self.variables])
        return df.astype(types)

    def load_data(self):
        """
        Load data if it exists. If the current version is not an anchor, the previous versions will be combined.
        :return: the combined data
        :rtype: DataFrame
        """
        lam = self
        blocks = [self]
        while not lam.anchor:
            if lam.cloned_from is None:
                msg = 'The chain is broken, can not find the anchor version for {}.{}\n' \
                    .format(lam.namespace, lam.name)
                raise RuntimeError(msg)
            lam = lam.cloned_from
            blocks.append(lam)
        df = self.empty_data()
        for lam in reversed(blocks):
            df = lam.overwrite_with_delta(df)
        # Choose the rows still alive
        self.df = df[~df[self.COLUMN_TOMBSTONE]]
        return self.df

    def save_data(self):
        """
        Save data as a delta. Each revision produces a small delta, the overall delta combines all revision deltas.
        :return: the delta data
        :rtype: DataFrame
        """
        df = self.empty_data()
        for revision in self.revisions:
            delta = revision.delta()
            df.loc[delta.index, delta.columns] = delta.values
        if not os.path.exists(self.folder):
            self.create_folder()
        df.to_parquet(self.path)

    def query(self, assignments=None, filters=None, projections=None):
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


class PythonLambda(Lambda):
    APPLY_FUNC_NAME = 'apply'

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_python'
    }

    @lazy_property
    def apply_func(self):
        try:
            d = {}
            exec(dedent(self.code), d)
            return d.get(self.APPLY_FUNC_NAME)  # Should fail if the definition does not exist
        except:
            msg = 'Can not load apply function for {} : {} '.format(str(self), self.code)
            logger.error(msg)
            logger.debug(traceback.print_exc())
            raise RuntimeError(msg)

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
