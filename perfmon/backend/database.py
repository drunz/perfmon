import os
from sqlalchemy import create_engine
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import perfmon.settings as cfg


engine = create_engine('postgresql+psycopg2://%(user)s:%(password)s@%(host)s/%(name)s' % cfg.get("database"))
Session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()


class JSONMixin(object):
    def json(self):
        return dict((k, v) for k, v in self.__dict__.items() if not k.startswith('_'))


class Task(Base, JSONMixin):
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    timestamp_begin = Column(DateTime, index=True)
    timestamp_end = Column(DateTime, index=True)
    complex_id = Column(Integer, index=True)
    complex_name = Column(String)
    bytessent = Column(BigInteger)
    bytesreceived = Column(BigInteger)
    timetotal = Column(Float)
    completed = Column(Boolean, default=False)


class Request(Base, JSONMixin):
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    task_id = Column(String, ForeignKey('tasks.id'), index=True)
    endpoint = Column(String, index=True)
    bytessent = Column(BigInteger)
    bytesreceived = Column(BigInteger)
    timerequest = Column(Float)


Base.metadata.create_all(engine)


def install_postgres_extensions(basedir):
    files = ['logs_time_aggregate_response_func.sql', 'logs_time_aggregate_throughput_func.sql']
    for filename in files:
        print '-------- INSTALLING FUNCTION: %s --------' % filename
        sql = open(os.path.join(basedir, filename)).read()
        Session.execute(sql)
    Session.commit()