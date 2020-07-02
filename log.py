import json
import os
from datetime import datetime


LOG_DIR_PATH = 'log'


class Log:
    def __init__(self):
        # make log dir
        if not os.path.isdir(LOG_DIR_PATH):
            os.mkdir(LOG_DIR_PATH)

        # make log file path
        date_time_now = self.get_log_file_date_time()
        self.path_log = os.path.join(LOG_DIR_PATH, date_time_now + '.json')
        # make log file
        if not os.path.isfile(self.path_log):
            with open(self.path_log, 'x'):
                pass

    def append(self, data:str):
        if not isinstance(data, str):
            tp = data.__class__.__name__
            print('Log error: expected type str, got {}. try-parsing to str...'.format(tp))
            try:
                data = str(data)
                print('Success.')
            except Exception as ex:
                data = 'Parsing Error : {}'.format(ex)
                print(data)
        date_time_now = self.date_time_now()
        with open(self.path_log, 'a') as f:
            json.dump({'time': date_time_now, 'info': data}, f)
            f.write(os.linesep)

    @staticmethod
    def read_log_file(log_file_name):
        path = os.path.join(LOG_DIR_PATH, log_file_name + '.json')
        log = None
        if os.path.isfile(path):
            with open(path) as f:
                log = [json.loads(line) for line in f]
        else:
            print('Cannot find file at: {}'.format(path))
        return log

    @staticmethod
    def date_time_now():
        now = datetime.now()
        time_now_str = now.strftime("%d.%m %H:%M:%S")
        return time_now_str

    @staticmethod
    def get_log_file_date_time():
        now = datetime.now()
        time_now_str = now.strftime("%d.%m_%H-%M")
        return time_now_str