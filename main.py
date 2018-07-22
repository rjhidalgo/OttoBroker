from flask import Flask, request

import argparse
import configparser
import signal
import logging
from logging import handlers
import os
import json
from decimal import Decimal

from broker import OttoBroker
from jsonEncoder import CustomJSONEncoder

handler = handlers.TimedRotatingFileHandler("logs/log_broker.log", when="midnight", interval=1)
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    filename=os.devnull,
    level=logging.INFO)
_logger = logging.getLogger()
_logger.addHandler(handler)

# START CONSTANTS
# api params
SYMBOLS_KEY = 'symbols'
SYMBOL_KEY = 'symbol'
USERID_KEY = 'userid'
APIKEY_KEY = 'apikey'
DISPLAYNAME_KEY = 'displayname'
AMOUNT_KEY = 'amount'
REASON_KEY = 'reason'
QUANTITY_KEY = 'quantity'

# error messages
MISSING_PARAM_MSG = 'missing required parameter: {param}'
INVALID_TYPE_MSG = 'param \'{param}\' could not be converted to type \'{type}\''


# END CONSTANTS

def jsonify(obj):
    return json.dumps(obj, cls=CustomJSONEncoder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", 
            dest="configFile",
            help="Relative Path to config file",
            required=True)
    args = parser.parse_args()
    config = configparser.ConfigParser(delimiters=('='))
    config.read(args.configFile)

    broker = OttoBroker(
        config.get('DEFAULT', 'connection_string'),
        config.get('DEFAULT', 'broker_key'),
        config.get('DEFAULT', 'test_user_id'),
    )

    app = Flask(__name__)

    def handle_signals(self, signum, frame):
        global app
        # taken from: https://stackoverflow.com/a/17053522
        func = app.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    @app.route('/broker/hello')
    def flask_test():
        return "I am OttoBroker yes hello"
    
    @app.route('/broker/stock_info')
    def get_stock_info():
        if SYMBOLS_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=SYMBOLS_KEY)))
        return jsonify(broker.get_stock_value([s.upper() for s in request.args[SYMBOLS_KEY].split(',')]))
    
    @app.route('/broker/toggle_test')
    def toggle_test():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))

        return jsonify(broker.toggle_test_mode(request.args[APIKEY_KEY]))
    
    @app.route('/broker/user_info')
    def get_user_info():
        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))

        return jsonify(broker.get_user_info(request.args[USERID_KEY]))
    
    @app.route('/broker/register')
    def register_user():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))
        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))
        if DISPLAYNAME_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=DISPLAYNAME_KEY)))

        return jsonify(broker.register_user(request.args[USERID_KEY], request.args[DISPLAYNAME_KEY], request.args[APIKEY_KEY]))
    
    @app.route('/broker/deposit')
    def deposit():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))
        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))
        if AMOUNT_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=AMOUNT_KEY)))
        amount = request.args[AMOUNT_KEY]
        try:
            amount = Decimal(amount)
        except Exception:
            return jsonify(broker.return_failure(INVALID_TYPE_MSG.format(param=AMOUNT_KEY, type='Decimal')))
            
        if REASON_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=REASON_KEY)))

        return jsonify(broker.deposit(request.args[USERID_KEY], amount, request.args[REASON_KEY], request.args[APIKEY_KEY]))
    
    @app.route('/broker/withdraw')
    def withdraw():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))

        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))

        if AMOUNT_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=AMOUNT_KEY)))
        amount = request.args[AMOUNT_KEY]
        try:
            amount = Decimal(amount)
        except Exception:
            return jsonify(broker.return_failure(INVALID_TYPE_MSG.format(param=AMOUNT_KEY, type='Decimal')))
            
        if REASON_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=REASON_KEY)))

        return jsonify(broker.withdraw(request.args[USERID_KEY], amount, request.args[REASON_KEY], request.args[APIKEY_KEY]))
    
    @app.route('/broker/buy_stock')
    def buy_stock():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))

        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))

        if SYMBOL_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=SYMBOL_KEY)))

        if QUANTITY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=QUANTITY_KEY)))
        quantity = request.args[QUANTITY_KEY]
        try:
            quantity = int(quantity)
        except Exception:
            return jsonify(broker.return_failure(INVALID_TYPE_MSG.format(param=QUANTITY_KEY, type='int')))

        return jsonify(broker.buy_stock(request.args[SYMBOL_KEY], quantity, request.args[USERID_KEY], request.args[APIKEY_KEY]))
    
    @app.route('/broker/sell_stock')
    def sell_stock():
        if APIKEY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=APIKEY_KEY)))

        if USERID_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=USERID_KEY)))

        if SYMBOL_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=SYMBOL_KEY)))

        if QUANTITY_KEY not in request.args:
            return jsonify(broker.return_failure(MISSING_PARAM_MSG.format(param=QUANTITY_KEY)))
        quantity = request.args[QUANTITY_KEY]
        try:
            quantity = int(quantity)
        except Exception:
            return jsonify(broker.return_failure(INVALID_TYPE_MSG.format(param=QUANTITY_KEY, type='int')))

        return jsonify(broker.sell_stock(request.args[SYMBOL_KEY], quantity, request.args[USERID_KEY], request.args[APIKEY_KEY]))
    


    app.run(
        debug=False,
        port=8888
    )