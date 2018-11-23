import superset
from norm.config import db, user_model


def user_tester():
    tester = db.session.query(user_model).filter(user_model.username == 'tester',
                                                 user_model.email == 'norm-tester@reasoned.ai').first()
    if tester is None:
        tester = user_model(username='tester', first_name='tester', last_name='norm',
                            email='norm-tester@reasoned.ai', password='')
        db.session.add(tester)
        db.session.commit()
    return tester
