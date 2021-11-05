import requests
import time
from operator import itemgetter
from exceptions import BinanceAPIException, BinanceRequestException
import connection
import dateparser
import pytz
from datetime import datetime


class BinanceLite(object):
    API_KEY = 'appKeyHere'

    PUBLIC_API_VERSION = 'v1'
    PRIVATE_API_VERSION = 'v3'
    API_URL = 'https://api.binance.com/api'

    RECV_WINDOW = 7000

    SIDE_BUY = 'BUY'
    SIDE_SELL = 'SELL'

    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
    ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    ORDER_TYPE_LIMIT_MAKER = 'LIMIT_MAKER'

    SYMBOL_BTCUSDT = 'BTCUSDT'

    def __init__(self, log=None):
        self.log = log
        self._requests_params = None
        self.session = self._init_session()

    def ping(self):
        """Test connectivity to the Rest API.
        :returns: Empty array
        :raises: BinanceRequestException, BinanceAPIException
        """
        print('ping!')
        try:
            start = time.time()
            pong = self._get('ping')
            stop = time.time()
            if pong == {}:
                return 'pong time: {}'.format(stop - start)
            else:
                return False
        except Exception as ex:
            print(ex)
            return False

    def get_order_book(self, **params):
        """Get the Order Book for the market

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#order-book

        :param symbol: required
        :type symbol: str
        :param limit:  Default 100; max 1000
        :type limit: int

        :returns: API response

        .. code-block:: python

            {
                "lastUpdateId": 1027024,
                "bids": [
                    [
                        "4.00000000",     # PRICE
                        "431.00000000",   # QTY
                        []                # Can be ignored
                    ]
                ],
                "asks": [
                    [
                        "4.00000200",
                        "12.00000000",
                        []
                    ]
                ]
            }

        :raises: BinanceRequestException, BinanceAPIException

        """
        try:
            order_book = self._get('depth', data=params)
            if order_book:
                return [True, order_book]
            else:
                return [False, 'Empty order book.']
        except Exception as ex:
            print('get_order_book error: \'{}\''.format(ex))
            return [False, ex]

    def get_assets_balance(self,**params):
        """Get BTC and USDT assets balances

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#account-information-user_data

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: dictionary or None if not found

        .. code-block:: python

            {
            'BTC': {
                'free': 0.0016,
                'locked': 0.0
            },
            'USDT': {
                'free': 0.0,
                'locked': 0.0
            }}

        :raises: BinanceRequestException, BinanceAPIException

        """
        try:
            res = self.get_account(**params)
        except Exception as ex:
            print('get assets error: {}'.format(ex))
            return [False, ex]
        if res:
            if "balances" in res:
                balances = {}
                for balance in res['balances']:
                    if balance['asset'] == 'BTC':
                        balances['BTC'] = {}
                        balances['BTC']['free'] = float(balance['free'])
                        balances['BTC']['locked'] = float(balance['locked'])
                    elif balance['asset'] == 'USDT':
                        balances['USDT'] = {}
                        balances['USDT']['free'] = float(balance['free'])
                        balances['USDT']['locked'] = float(balance['locked'])
                return [True, balances]
        return [False, None]

    def get_open_orders(self, **params):
        """Get all open orders on a symbol.
        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#current-open-orders-user_data
        :param symbol: optional
        :type symbol: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            [
                {
                    "symbol": "LTCBTC",
                    "orderId": 1,
                    "clientOrderId": "myOrder1",
                    "price": "0.1",
                    "origQty": "1.0",
                    "executedQty": "0.0",
                    "status": "NEW",
                    "timeInForce": "GTC",
                    "type": "LIMIT",
                    "side": "BUY",
                    "stopPrice": "0.0",
                    "icebergQty": "0.0",
                    "time": 1499827319559
                }
            ]

        :raises: BinanceRequestException, BinanceAPIException

        """
        params['recvWindow'] = self.RECV_WINDOW
        return self._get('openOrders',True,data=params)

    def limit_buy(self, usd_amount, price):
        btc_amount = round(usd_amount / price, 6)
        try:
            try_result = self.create_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                           type=BinanceLite.ORDER_TYPE_LIMIT_MAKER,
                                           side=BinanceLite.SIDE_BUY,
                                           quantity=btc_amount,
                                           price=price)
            result = {'result': True,'info': try_result}
        except BinanceAPIException as ex:
            if ex.code == -1013:
                if ex.message == 'Filter failure: MIN_NOTIONAL':
                    print('min notional error!')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            elif ex.code == -2010:
                if ex.message == 'Account has insufficient balance for requested action.':
                    print('insufficient assets')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            else:
                result = {'result': False,'info': 'error code: {} msg: {}'.format(ex.code,ex.message)}
        except Exception as ex:
            result = {'result': False,'info': str(ex)}
        return result

    def limit_sell(self, btc_amount, price):
        btc_amount = round(btc_amount, 6)
        try:
            try_result = self.create_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                     type=BinanceLite.ORDER_TYPE_LIMIT_MAKER,
                                     side=BinanceLite.SIDE_SELL,
                                     quantity=btc_amount,
                                     price=price)
            result = {'result': True, 'info': try_result}
        except BinanceAPIException as ex:
            if ex.code == -1013:
                if ex.message == 'Filter failure: MIN_NOTIONAL':
                    print('min notional error!')
                    result = {'result': False, 'info': False}
                else:
                    result = {'result': False, 'info': ex.message}
            elif ex.code == -2010:
                if ex.message == 'Account has insufficient balance for requested action.':
                    print('insufficient assets')
                    result = {'result': False, 'info': False}
                else:
                    result = {'result': False, 'info': ex.message}
            else:
                result = {'result': False, 'info': 'error code: {} msg: {}'.format(ex.code, ex.message)}
        except Exception as ex:
            result = {'result': False, 'info': str(ex)}
        return result

    def market_buy(self, usd_amount):
        usd_amount = round(usd_amount, 2)
        try:
            info = self.create_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                          type=BinanceLite.ORDER_TYPE_MARKET,
                                          side=BinanceLite.SIDE_BUY,
                                            quoteOrderQty=usd_amount)
            if info:
                return {'result': True,'info': info}
            else:
                return {'result': False, 'info': 'Signing error.'}
        except Exception as ex:
            return {'result': False, 'info': str(ex)}

    def market_sell(self, btc_amount):
        try:
            btc_amount = round(btc_amount, 6)
            info = self.create_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                          type=BinanceLite.ORDER_TYPE_MARKET,
                                          side=BinanceLite.SIDE_SELL,
                                            quantity=btc_amount)
            if info:
                return {'result': True,'info': info}
            else:
                return {'result': False, 'info': 'Signing error.'}
        except Exception as ex:
            return {'result': False, 'info': str(ex)}

    def market_test_buy(self, usd_amount):
        try:
            usd_amount = round(usd_amount, 2)
            info = self.create_test_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                          type=BinanceLite.ORDER_TYPE_MARKET,
                                          side=BinanceLite.SIDE_BUY,
                                            quoteOrderQty=usd_amount)
            result = {'result': True,'info': info}
        except BinanceAPIException as ex:
            if ex.code == -1013:
                if ex.message == 'Filter failure: MIN_NOTIONAL':
                    print('min notional error!')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            elif ex.code == -2010:
                if ex.message == 'Account has insufficient balance for requested action.':
                    print('insufficient assets')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            else:
                result = {'result': False,'info': 'error code: {} msg: {}'.format(ex.code,ex.message)}
        except Exception as ex:
            result = {'result': False,'info': str(ex)}
        return result

    def market_test_sell(self, btc_amount):
        try:
            btc_amount = round(btc_amount, 6)
            info = self.create_test_order(symbol=BinanceLite.SYMBOL_BTCUSDT,
                                              type=BinanceLite.ORDER_TYPE_MARKET,
                                              side=BinanceLite.SIDE_SELL,
                                                quantity=btc_amount)
            if info:
                result = {'result': True,'info': info}
            else:
                result = {'result': False, 'info': 'Signing error.'}
        except BinanceAPIException as ex:
            if ex.code == -1013:
                if ex.message == 'Filter failure: MIN_NOTIONAL':
                    print('min notional error!')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            elif ex.code == -2010:
                if ex.message == 'Account has insufficient balance for requested action.':
                    print('insufficient assets')
                    result = {'result': False,'info': False}
                else:
                    result = {'result': False,'info': ex.message}
            else:
                result = {'result': False,'info': 'error code: {} msg: {}'.format(ex.code,ex.message)}
        except Exception as ex:
            result = {'result': False,'info': str(ex)}
        return result

    def create_order(self, **params):
        """"
        Any order with an icebergQty MUST have timeInForce set to GTC.
        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: str
        :param type: required
        :type type: str
        :param timeInForce: required if limit order
        :type timeInForce: str
        :param quantity: required
        :type quantity: decimal
        :param quoteOrderQty: amount the user wants to spend (when buying) or receive (when selling)
            of the quote asset, applicable to MARKET orders
        :type quoteOrderQty: decimal
        :param price: required
        :type price: str
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param icebergQty: Used with LIMIT, STOP_LOSS_LIMIT, and TAKE_PROFIT_LIMIT to create an iceberg order.
        :type icebergQty: decimal
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        Response ACK:

        .. code-block:: python

            {
                "symbol":"LTCBTC",
                "orderId": 1,
                "clientOrderId": "myOrder1" # Will be newClientOrderId
                "transactTime": 1499827319559
            }

        Response RESULT:

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "orderId": 28,
                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                "transactTime": 1507725176595,
                "price": "0.00000000",
                "origQty": "10.00000000",
                "executedQty": "10.00000000",
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": "MARKET",
                "side": "SELL"
            }

        Response FULL:

        .. code-block:: python

            {
                "symbol": "BTCUSDT",
                "orderId": 28,
                "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
                "transactTime": 1507725176595,
                "price": "0.00000000",
                "origQty": "10.00000000",
                "executedQty": "10.00000000",
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": "MARKET",
                "side": "SELL",
                "fills": [
                    {
                        "price": "4000.00000000",
                        "qty": "1.00000000",
                        "commission": "4.00000000",
                        "commissionAsset": "USDT"
                    },
                    {
                        "price": "3999.00000000",
                        "qty": "5.00000000",
                        "commission": "19.99500000",
                        "commissionAsset": "USDT"
                    },
                    {
                        "price": "3998.00000000",
                        "qty": "2.00000000",
                        "commission": "7.99600000",
                        "commissionAsset": "USDT"
                    },
                    {
                        "price": "3997.00000000",
                        "qty": "1.00000000",
                        "commission": "3.99700000",
                        "commissionAsset": "USDT"
                    },
                    {
                        "price": "3995.00000000",
                        "qty": "1.00000000",
                        "commission": "3.99500000",
                        "commissionAsset": "USDT"
                    }
                ]
            }

        :raises: BinanceRequestException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException

        """
        params['recvWindow'] = self.RECV_WINDOW
        params['newOrderRespType'] = 'FULL'
        return self._post('order', True, data=params)

    def create_test_order(self, **params):
        """Test new order creation and signature/recvWindow long. Creates and validates a new order but does not send it into the matching engine.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#test-new-order-trade

        :param symbol: required
        :type symbol: str
        :param side: required
        :type side: str
        :param type: required
        :type type: str
        :param timeInForce: required if limit order
        :type timeInForce: str
        :param quantity: required
        :type quantity: decimal
        :param price: required
        :type price: str
        :param newClientOrderId: A unique id for the order. Automatically generated if not sent.
        :type newClientOrderId: str
        :param icebergQty: Used with iceberg orders
        :type icebergQty: decimal
        :param newOrderRespType: Set the response JSON. ACK, RESULT, or FULL; default: RESULT.
        :type newOrderRespType: str
        :param recvWindow: The number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {}

        :raises: BinanceRequestException, BinanceAPIException, BinanceOrderException, BinanceOrderMinAmountException, BinanceOrderMinPriceException, BinanceOrderMinTotalException, BinanceOrderUnknownSymbolException, BinanceOrderInactiveSymbolException


        """
        params['newOrderRespType'] = 'FULL'
        params['recvWindow'] = self.RECV_WINDOW
        return self._post('order/test',True,data=params)

    def get_account(self, **params):
        """Get current account information.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#account-information-user_data

        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {
                "makerCommission": 15,
                "takerCommission": 15,
                "buyerCommission": 0,
                "sellerCommission": 0,
                "canTrade": true,
                "canWithdraw": true,
                "canDeposit": true,
                "balances": [
                    {
                        "asset": "BTC",
                        "free": "4723846.89208129",
                        "locked": "0.00000000"
                    },
                    {
                        "asset": "LTC",
                        "free": "4763368.68006011",
                        "locked": "0.00000000"
                    }
                ]
            }

        :raises: BinanceRequestException, BinanceAPIException

        """
        params['recvWindow'] = self.RECV_WINDOW
        return self._get('account', True, data=params)

    def cancel_order(self, **params):
        """Cancel an active order. Either orderId or origClientOrderId must be sent.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#cancel-order-trade

        :param symbol: required
        :type symbol: str
        :param orderId: The unique order id
        :type orderId: int
        :param origClientOrderId: optional
        :type origClientOrderId: str
        :param newClientOrderId: Used to uniquely identify this cancel. Automatically generated by default.
        :type newClientOrderId: str
        :param recvWindow: the number of milliseconds the request is valid for
        :type recvWindow: int

        :returns: API response

        .. code-block:: python

            {
                "symbol": "LTCBTC",
                "origClientOrderId": "myOrder1",
                "orderId": 1,
                "clientOrderId": "cancelMyOrder1"
            }

        :raises: BinanceRequestException, BinanceAPIException

        """
        params['recvWindow'] = self.RECV_WINDOW
        return self._delete('order',True,data=params)

    def cancel_all_open_orders(self, **params):
        # symbol required
        params['recvWindow'] = self.RECV_WINDOW
        return self._delete('openOrders', True, data=params)

    def get_price_line(self, start_str_or_float, interval, end_str_or_float=None):
        try:
            candles_1m = self.get_historical_klines(start_str_or_float=start_str_or_float,
                                                 end_str_or_float=end_str_or_float, interval=interval)
        except Exception as ex:
            return str(ex), False
        total_data = []
        for i in range(len(candles_1m)):
            open = float(candles_1m[i][1])
            close = float(candles_1m[i][4])
            single_input = {'time': candles_1m[i][0],
                            'open': open,
                            'high': float(candles_1m[i][2]),
                            'low': float(candles_1m[i][3]),
                            'close': close,
                            'volume': float(candles_1m[i][5]),
                            'action': None}
            total_data.append(single_input)
        return False, total_data

    def get_symbol_ticker(self, **params):
        """Latest price for a symbol or symbols.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#24hr-ticker-price-change-statistics

        :param symbol:
        :type symbol: str

        :returns: API response

        .. code-block:: python

            {
                "symbol": "LTCBTC",
                "price": "4.00000200"
            }

        OR

        .. code-block:: python

            [
                {
                    "symbol": "LTCBTC",
                    "price": "4.00000200"
                },
                {
                    "symbol": "ETHBTC",
                    "price": "0.07946600"
                }
            ]

        :raises: BinanceRequestException, BinanceAPIException

        """
        try:
            ticker = self._get('ticker/price', data=params, version=self.PUBLIC_API_VERSION)
        except Exception as ex:
            print('Error: {}'.format(ex))
            ticker = None
        return ticker

    def get_historical_klines(self,interval,start_str_or_float,end_str_or_float=None,symbol=SYMBOL_BTCUSDT,limit=1000):
        """Get Historical Klines from Binance

        See dateparser docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/

        If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

        :param symbol: Name of symbol pair e.g BNBBTC
        :type symbol: str
        :param interval: Binance Kline interval
        :type interval: str
        :param start_str_or_float: Start date string in UTC format or timestamp in milliseconds
        :type start_str_or_float: str|float
        :param end_str_or_float: optional - end date string in UTC format or timestamp in milliseconds (default will fetch everything up to now)
        :type end_str_or_float: str|float
        :param limit: Default 500; max 1000.
        :type limit: int

        :return: list of OHLCV values

        """
        # init our list
        output_data = []

        # setup the max limit
        limit = limit

        # convert interval to useful value in seconds
        timeframe = self._interval_to_milliseconds(interval)

        # convert our date strings to milliseconds
        if isinstance(start_str_or_float, float):
            start_ts = int(start_str_or_float * 1000)
        else:
            start_ts = self._date_to_milliseconds(start_str_or_float)

        # establish first available start timestamp
        first_valid_ts = self._get_earliest_valid_timestamp(symbol, interval)
        start_ts = max(start_ts, first_valid_ts)

        # if an end time was passed convert it
        end_ts = None
        if end_str_or_float:
            if isinstance(end_str_or_float, float):
                end_ts = int(end_str_or_float * 1000)
            else:
                end_ts = self._date_to_milliseconds(end_str_or_float)

        idx = 0
        while True:
            # fetch the klines from start_ts up to max 500 entries or the end_ts if set
            temp_data = self._get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_ts,
                endTime=end_ts
            )

            # handle the case where exactly the limit amount of data was returned last loop
            if not len(temp_data):
                break

            # append this loops data to our output data
            output_data += temp_data

            # set our start timestamp using the last value in the array
            start_ts = temp_data[-1][0]

            idx += 1
            # check if we received less than the required limit and exit the loop
            if len(temp_data) < limit:
                # exit the while loop
                break

            # increment next call by our timeframe
            start_ts += timeframe
            # sleep to be kind to the API
            if idx % 17 == 0:
                time.sleep(0.3)

        return output_data

    def _get_klines(self,**params):
        """Kline/candlestick bars for a symbol. Klines are uniquely identified by their open time.

        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#klinecandlestick-data

        :param symbol: required
        :type symbol: str
        :param interval: -
        :type interval: str
        :param limit: - Default 500; max 500.
        :type limit: int
        :param startTime:
        :type startTime: int
        :param endTime:
        :type endTime: int

        :returns: API response

        .. code-block:: python

            [
                [
                    1499040000000,      # Open time
                    "0.01634790",       # Open
                    "0.80000000",       # High
                    "0.01575800",       # Low
                    "0.01577100",       # Close
                    "148976.11427815",  # Volume
                    1499644799999,      # Close time
                    "2434.19055334",    # Quote asset volume
                    308,                # Number of trades
                    "1756.87402397",    # Taker buy base asset volume
                    "28.46694368",      # Taker buy quote asset volume
                    "17928899.62484339" # Can be ignored
                ]
            ]

        :raises: BinanceRequestException, BinanceAPIException

        """
        return self._get('klines', data=params)

    def _get_earliest_valid_timestamp(self, symbol, interval):
        """Get earliest valid open timestamp from Binance

        :param symbol: Name of symbol pair e.g BNBBTC
        :type symbol: str
        :param interval: Binance Kline interval
        :type interval: str

        :return: first valid timestamp

        """
        kline = self._get_klines(
            symbol=symbol,
            interval=interval,
            limit=1,
            startTime=0,
            endTime=None
        )
        return kline[0][0]

    def _init_session(self):
        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _post(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('post', path, signed, version, **kwargs)

    def _get(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('get', path, signed, version, **kwargs)

    def _delete(self, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        return self._request_api('delete', path, signed, version, **kwargs)

    def _request_api(self, method, path, signed=False, version=PUBLIC_API_VERSION, **kwargs):
        uri = self._create_api_uri(path, signed, version)

        return self._request(method, uri, signed, **kwargs)

    def _create_api_uri(self, path, signed=True, version=PUBLIC_API_VERSION):
        v = self.PRIVATE_API_VERSION if signed else version
        return self.API_URL + '/' + v + '/' + path

    def _request(self, method, uri, signed, force_params=False, **kwargs):
        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data

            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del(kwargs['data']['requests_params'])

        if signed:
            # generate signature
            kwargs['data']['timestamp'] = int(time.time() * 1000)
            signature = self._call_for_signature(kwargs['data'])
            if not signature:
                print('Signature error!')
                return None
            kwargs['data']['signature'] = signature

        # sort get and post params to match signature order
        if data:
            # sort post params
            kwargs['data'] = self._order_params(kwargs['data'])
            # Remove any arguments with values of None.
            null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
            for i in reversed(null_args):
                del kwargs['data'][i]

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or force_params):
            kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
            del(kwargs['data'])

        self.response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response()

    def _call_for_signature(self, data):
        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
        # log that
        self.log.append_specific(query_string)
        signature = connection.get_signature(query_string)
        # validate and log that too
        if signature[0]: # result positive
            signature = signature[0]
            self.log.append_specific('signature obtained.')
        else:   # error
            error = signature[1]
            self.log.append_general(error)
            signature = False
        return signature

    def _handle_response(self):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        if not str(self.response.status_code).startswith('2'):
            raise BinanceAPIException(self.response)
        try:
            return self.response.json()
        except ValueError:
            raise BinanceRequestException('Invalid Response: %s' % self.response.text)

    @staticmethod
    def _order_params(data):
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(('signature', data['signature']))
        return params

    @staticmethod
    def _interval_to_milliseconds(interval):
        """Convert a Binance interval string to milliseconds

        :param interval: Binance interval string, e.g.: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
        :type interval: str

        :return:
             int value of interval in milliseconds
             None if interval prefix is not a decimal integer
             None if interval suffix is not one of m, h, d, w

        """
        seconds_per_unit = {
            "m": 60,
            "h": 60 * 60,
            "d": 24 * 60 * 60,
            "w": 7 * 24 * 60 * 60,
        }
        try:
            return int(interval[:-1]) * seconds_per_unit[interval[-1]] * 1000
        except (ValueError,KeyError):
            return None

    @staticmethod
    def _date_to_milliseconds(date_str):
        """Convert UTC date to milliseconds

        If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"

        See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/

        :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
        :type date_str: str
        """
        # get epoch value in UTC
        epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        # parse our date string
        d = dateparser.parse(date_str)
        # if the date is not timezone aware apply UTC timezone
        if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
            d = d.replace(tzinfo=pytz.utc)

        # return the difference in time
        return int((d - epoch).total_seconds() * 1000.0)


if __name__ == '__main__':
    cl = BinanceLite()
    assets = cl.get_assets_balance()
    print(assets)
