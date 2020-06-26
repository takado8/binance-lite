import json
import os
from datetime import datetime


LOG_DIR_PATH = 'logs'


# TO DO: log size limit info
# or save log in partition D and relax...


class Log:
    def __init__(self):
        # make log dir
        if not os.path.isdir(LOG_DIR_PATH):
            os.mkdir(LOG_DIR_PATH)
        # make log file path
        date_time_now = self.get_log_file_date_time()
        self.log_file_path = os.path.join(LOG_DIR_PATH, date_time_now + '.json')
        # make logs dicts
        self.log = {}

    def append(self,data:str):
        if not isinstance(data, str):
            tp = type(data)
            print('Log error: expected type str, got {}. parsing to str.'.format(tp))
            try:
                data = str(data)
            except Exception as ex:
                print('Error:')
                print(ex)
                return
        date_time_now = self.date_time_now()
        self.log[date_time_now] = data
        self.save_log_file()

    def save_log_file(self):
        with open(self.log_file_path, 'w+') as file:
            json.dump(self.log, file)

    @staticmethod
    def read_log_file(log_file_name):
        path = os.path.join(LOG_DIR_PATH, log_file_name + '.json')
        if os.path.isfile(path):
            with open(path, 'r') as file:
                data = json.load(file)
                for item in data:
                    print(data[item], end='\n\n')
        else:
            print('Cannot find file at: {}'.format(path))

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