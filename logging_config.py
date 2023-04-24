from logging import getLogger, basicConfig, StreamHandler, Formatter
from sys import stdout

logger = getLogger(__name__)
basicConfig(filename='transactions_logs.log',
                      filemode='w',
                      level='DEBUG',
                      format='%(asctime)s, %(levelname)s, %(message)s, %(name)s')


stream_handler = StreamHandler(stream=stdout)
formatter = Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s')
logger.addHandler(stream_handler)
stream_handler.setFormatter(formatter)

