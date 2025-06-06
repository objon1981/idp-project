from pake import PAKE

def create_pake_session(username, password):
    session = PAKE(username, password)
    msg = session.start()
    return session, msg

def finalize_pake(session, message):
    return session.finish(message)
