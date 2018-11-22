from superset import db
from superset import security_manager as sm


def user_tester():
    tester = db.session.query(sm.user_model).filter(sm.user_model.username == 'tester',
                                                    sm.user_model.email == 'norm-tester@reasoned.ai').first()
    if tester is None:
        tester = sm.user_model(username='tester', first_name='tester', last_name='norm',
                               email='norm-tester@reasoned.ai', password='')
        db.session.add(tester)
        db.session.commit()
    return tester
