"""A collection of ORM sqlalchemy models for Lambda"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from textwrap import dedent

from future.standard_library import install_aliases

from flask_appbuilder import Model

from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, exists
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy.orm import relationship

from superset import app, db
from superset.models.norm import Lambda, Variable

from superset import security_manager as sm

from superset.models.helpers import AuditMixinNullable
from superset.models.mixins import VersionedMixin, lazy_property, ParametrizedMixin
from superset.models.core import metadata

from pandas import DataFrame
import traceback
import logging
logger = logging.getLogger(__name__)

install_aliases()

config = app.config


class RegisterLambda:
    """
    A class decorator to ensure the class to be a singleton and register the class in database
    """
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
            instance = db.session.query(self.klass).filter(self.klass.signature == self.instance.signature).first()
            if not instance:
                # If the instance does not exist, commit it to the database
                db.session.add(self.instance)
                db.commit()
            else:
                # Otherwise use the one loaded from database
                self.instance = instance
        return self.instance


@RegisterLambda
class NativeLambda(Lambda):

    __mapper_args__ = {
        'polymorphic_identity': 'lambda_native'
    }

    def __init__(self, name, version, description):
        super(Lambda, self).__init__(namespace='norm.native',
                                     name=name,
                                     version=version,
                                     description=description,
                                     variables=[Variable('value', T)])


T = NativeLambda(name='Type', version=1, description='A logical function')
BO = NativeLambda(name='Boolean', version=1, description='Boolean, true/false, 1/0')
IN = NativeLambda(name='Integer', version=1, description='Integer, -inf..+inf')
ST = NativeLambda(name='String', version=1, description='String, "blahblah"')
UN = NativeLambda(name='Unicode', version=1, description='Unicode, u"blahblah"')
PA = NativeLambda(name='Pattern', version=1, description='Pattern, r"^test[0-9]+"')
UU = NativeLambda(name='UUID', version=1, description='UUID, $"sfsfsfsf"')
UR = NativeLambda(name='URL', version=1, description='URL, l"http://example.com"')
DA = NativeLambda(name='Datetime', version=1, description='Datetime, t"2018-09-01"')
Any = NativeLambda(name='Any', version=1, description='Any type')
