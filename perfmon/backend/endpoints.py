import cherrypy
import json
#import random
import logging
import time
import database as db
from sqlalchemy import func, desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta
from decimal import Decimal
from operator import itemgetter
from psycopg2 import OperationalError
from pprint import pprint 


class StatusResponse(object):
    def __init__(self, code='ok', message=None):
        self.code = code
        self.message = message
    
    def json(self):
        status = {'status': self.code}
        
        if self.message:
            status['message'] = self.message
        
        return json.dumps(status)


class ExtendedEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return time.mktime(obj.timetuple())
        elif isinstance(obj, Decimal):
            return str(obj);
        return super(ExtendedEncoder, self).default(obj)


class Logging(object):
    """Defines REST endpoints for logging.
    
    API for logging tasks:
        /log/task/begin/?task_id=<uuid>&complex_id=0
        /log/task/end/?task_id=<uuid>&timetotal=0.8&bytessent=1&bytesreceived=1
    
    API for logging requests:
        /log/request/?task_id=<uuid>&endpoint=test&timerequest=0.8&bytessent=1&bytesreceived=1"""
    
    @cherrypy.tools.json_in()
    @cherrypy.expose
    def index(self):
        data = cherrypy.request.json
        #pprint(data)
        status = StatusResponse()
        try:
            dt_begin = datetime.fromtimestamp(float(data['time_begin']))
            dt_end   = datetime.fromtimestamp(float(data['time_end']))
            task = db.Task(id=data['task_id'],
                        name=data['task_name'],
                        timestamp_begin=dt_begin,
                        timestamp_end=dt_end,
                        complex_id=data['complex_id'],
                        complex_name=data['complex_name'],
                        bytessent=data['sent_amount'], 
                        bytesreceived=data['response_length'], 
                        timetotal=data['all_time'],
                        completed=True)
            db.Session.add(task)
            db.Session.commit()
            
            for request_data in data['requests']:
                dt_timestamp = datetime.fromtimestamp(float(request_data['timestamp']))
                request = db.Request(timestamp=dt_timestamp,
                                  task_id=data['task_id'],
                                  endpoint=request_data['end_point'],
                                  bytessent=request_data['sent_amount'], 
                                  bytesreceived=request_data['response_length'], 
                                  timerequest=request_data['all_time'])
                db.Session.add(request)
            db.Session.commit()
        except IntegrityError, e:
            logging.error(e)
            status = StatusResponse('error', "This task ID already exists and cannot be reused!")
            db.Session.rollback()
        except KeyError, e:
            logging.error(e)
            status = StatusResponse('error', "Received invalid JSON data!")
            db.Session.rollback()
        except ValueError, e:
            logging.error(e)
            status = StatusResponse('error', "Received invalid string for timestamps: %s" % str(e))
            db.Session.rollback()
        finally:
            db.Session.close()
            return status.json()
    
    @cherrypy.expose
    def task(self, mode, task_id, complex_id=None, timetotal=0.0, bytessent=0, bytesreceived=0):
        status = StatusResponse()
        try:
            if mode == 'begin':
                if not complex_id:
                    raise Exception("Task complex_id required for mode 'begin'!")
                # Create a task instance with basic info on begin
                # This gracefully handles foreign key constraints
                task = db.Task(id=task_id, timestamp_begin=datetime.now(),
                            complex_id=complex_id,
                            bytessent=bytessent, bytesreceived=bytesreceived,
                            timetotal=timetotal)
                db.Session.add(task)
            elif mode == 'end':
                # Update the task once ended
                # TODO: Add a check constraint if task is completed
                db.Session.query(db.Task).filter(
                    db.Task.id == task_id,
                    db.Task.completed == False
                ).update({
                    db.Task.timestamp_end: datetime.now(),
                    db.Task.timetotal: timetotal,
                    db.Task.bytessent: bytessent,
                    db.Task.bytesreceived: bytesreceived,
                    db.Task.completed: True,
                })
            else:
                raise Exception("Task mode '%s' invalid (use 'begin' or 'end')!" % mode)
            
            db.Session.commit()
        except IntegrityError, e:
            status = StatusResponse('error', "Task with id '%s' already exists!" % task_id)
            db.Session.rollback()
        except Exception, e:
            status = StatusResponse('error', str(e))
            db.Session.rollback()
        finally:
            return status.json()
    
    @cherrypy.expose
    def request(self, task_id, endpoint, timerequest, bytessent=0, bytesreceived=0, complex_id=None, **kwargs):
        status = StatusResponse()
        try:
            if complex_id:
                # If the request log is called with complex_id provided
                # we create a task implicitly. Makes the API easier to use
                # (no need to bother calling /log/task/begin).
                try:
                    task = db.Task(id=task_id, timestamp_begin=datetime.now(),
                                complex_id=complex_id,
                                bytessent=0, bytesreceived=0, timetotal=0)
                    db.Session.add(task)
                    db.Session.commit()
                except IntegrityError, e:
                    # Task already exists, fine
                    db.Session.rollback()
                
            # TODO: Add a check constraint if task is completed
            request = db.Request(timestamp=datetime.now(), task_id=task_id,
                              endpoint=endpoint,
                              bytessent=bytessent, bytesreceived=bytesreceived,
                              timerequest=timerequest)
            
            db.Session.add(request)
            db.Session.commit()
        except IntegrityError, e:
            status = StatusResponse('error', "The corresponding task this request references has not yet been logged. "
                                             "To implicitly create a task for a request, provide a complex_id.")
            db.Session.rollback()
        except Exception, e:
            status = StatusResponse('error', str(e))
            db.Session.rollback()
        finally:
            return status.json()


class Timeseries(object):
    
    @cherrypy.expose
    def response(self, endpoint, start, stop, step, complex_id=None):
        """Timeseries endpoint."""
        try:
            startdt = datetime.fromtimestamp(int(start) / 1e3)
            stopdt  = datetime.fromtimestamp(int(stop) / 1e3)
            step = int(int(step) / 1e3) # cubism.js sends steps in ms, we want seconds
            
            if complex_id:
                result = db.Session.execute(
                    "select * from timeseries_rq_max(:start, :stop, :step, :endpoint, :complex_id)", {
                        "start": startdt, "stop": stopdt, "step": "%d S" % step, 
                        "endpoint": endpoint, "complex_id": complex_id
                    }
                )
            else:
                result = db.Session.execute(
                    "select * from timeseries_rq_max(:start, :stop, :step, :endpoint)",
                    {"start": startdt, "stop": stopdt, "step": "%d S" % step, "endpoint": endpoint}
                )
            
            cherrypy.response.headers['Content-Type'] = "application/json"
            return json.dumps(map(itemgetter(1), result), cls=ExtendedEncoder) 
        except OperationalError, e:
            return StatusResponse('error', str(e)).json()
    
    @cherrypy.expose
    def throughput(self, tptype, endpoint, start, stop, step, complex_id=None):
        """Timeseries endpoint."""
        try:
            startdt = datetime.fromtimestamp(int(start) / 1e3)
            stopdt  = datetime.fromtimestamp(int(stop) / 1e3)
            step = int(int(step) / 1e3) # cubism.js sends steps in ms, we want seconds
            
            if complex_id:
                result = db.Session.execute(
                    "select * from timeseries_tp_max(:start, :stop, :step, :endpoint, :complex_id)", {
                        "start": startdt, "stop": stopdt, "step": "%d S" % step, 
                        "endpoint": endpoint, "complex_id": complex_id
                    }
                )
            else:
                result = db.Session.execute(
                    "select * from timeseries_tp_max(:start, :stop, :step, :endpoint)",
                    {"start": startdt, "stop": stopdt, "step": "%d S" % step, "endpoint": endpoint}
                )
            
            item = 0
            if tptype == 'sent':
                item = 2
            elif tptype == 'received':
                item = 1
            else:
                raise OperationalError("Throughput type '%s' not supported!" % tptype)
            
            result = map(itemgetter(item), result)
            result = map(lambda v: float(v)/1024, result)
            
            cherrypy.response.headers['Content-Type'] = "application/json"
            return json.dumps(result, cls=ExtendedEncoder)
        except OperationalError, e:
            return StatusResponse('error', str(e)).json()


class Dateseries(object):
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def response(self, endpoint=None, complex_id=None):
        startdt = datetime.now() - timedelta(days=13)
        result = db.Session.query(db.Request.timestamp, db.Request.timerequest).filter(db.Request.timestamp >= startdt).all()
        
        result_dict = dict((int(time.mktime(row[0].timetuple())), row[1]) for row in result)
        return result_dict
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def throughput(self, tptype, endpoint=None, complex_id=None):
        startdt = datetime.now() - timedelta(days=13)
        if tptype == 'upstream':
            result = db.Session.query(db.Request.timestamp, db.Request.bytessent).filter(db.Request.timestamp >= startdt).all()
        elif tptype == 'downstream':
            result = db.Session.query(db.Request.timestamp, db.Request.bytesreceived).filter(db.Request.timestamp >= startdt).all()
        else:
            raise cherrypy.HTTPError(404)
        
        result_dict = dict((int(time.mktime(row[0].timetuple())), row[1]) for row in result)
        return result_dict


class Query(object):
    """Defines REST endpoints to query logged data with optional filtering."""
    ts = Timeseries()
    ds = Dateseries()
    
    @cherrypy.expose
    def requests(self, endpoint=None, complex_id=None):
        if endpoint and complex_id:
            result = db.Session.query(db.Request).join(db.Task)\
                                 .filter(db.Request.endpoint == endpoint, 
                                         db.Task.complex_id == complex_id).all()
        elif endpoint:
            result = db.Session.query(db.Request).join(db.Task)\
                                 .filter(db.Request.endpoint == endpoint).all()
        elif complex_id:
            result = db.Session.query(db.Request).join(db.Task)\
                                 .filter(db.Task.complex_id == complex_id).all()
        else:
            result = db.Session.query(db.Request).join(db.Task).all()
        
        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps(map(db.Request.json, result), cls=ExtendedEncoder)
    
    @cherrypy.expose
    def tasks(self, endpoint=None, complex_id=None):
        if endpoint and complex_id:
            result = db.Session.query(db.Task).join(db.Request)\
                                 .filter(db.Request.endpoint == endpoint, 
                                         db.Task.complex_id == complex_id).all()
        elif endpoint:
            result = db.Session.query(db.Task).join(db.Request)\
                                 .filter(db.Request.endpoint == endpoint).all()
        elif complex_id:
            result = db.Session.query(db.Task).join(db.Request)\
                                 .filter(db.Task.complex_id == complex_id).all()
        else:
            result = db.Session.query(db.Task).join(db.Request).all()
        
        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps(map(db.Task.json, result), cls=ExtendedEncoder)
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def endpoints(self):
        result = db.Session.query(db.Request.endpoint)\
                             .distinct()\
                             .filter(db.Request.endpoint != None)\
                             .order_by(db.Request.endpoint).all()
        
        return map(itemgetter(0), result)
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def complexes(self, **kwargs):
        result = db.Session.query(db.Task.complex_id, db.Task.complex_name)\
                             .distinct()\
                             .filter(db.Task.complex_name != None)\
                             .order_by(db.Task.complex_name).all()
        
        #return {'id':0, 'text':'complex'}
        return map(itemgetter(1), result)
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def throughput(self, start=None, stop=None):
        """Returns the aggregated throughput for all requests
        logged within the time range [start, stop] (including).
        If no range is specified, the throughput of the last 24 hours is returned."""
        if start and stop:
            startdt = datetime.fromtimestamp(int(start) / 1e3)
            stopdt  = datetime.fromtimestamp(int(stop) / 1e3)
        else:
            stopdt  = datetime.now()
            startdt = stopdt - timedelta(hours=24)
        
        result = db.Session.query(
                         db.Request.endpoint, 
                         func.sum(db.Request.bytessent), 
                         func.sum(db.Request.bytesreceived)
                 ).filter(db.Request.timestamp >= startdt, db.Request.timestamp <= stopdt)\
                  .group_by(db.Request.endpoint)\
                  .order_by(db.Request.endpoint).all()
        
        return [{
            "endpoint":          row[0],
            "bytessent":     int(row[1]),
            "bytesreceived": int(row[2]), 
        } for row in result]
