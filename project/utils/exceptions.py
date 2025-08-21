class StockMarketException(Exception):
    """Base exception for stock market simulation"""
    pass

class InsufficientFundsException(StockMarketException):
    """Raised when user has insufficient funds"""
    pass

class InsufficientStocksException(StockMarketException):
    """Raised when user has insufficient stocks to sell"""
    pass

class StockNotFoundException(StockMarketException):
    """Raised when stock symbol is not found"""
    pass

class UserNotFoundException(StockMarketException):
    """Raised when user is not found"""
    pass

class ServiceUnavailableException(StockMarketException):
    """Raised when a service is unavailable"""
    pass

class TimeServerException(StockMarketException):
    """Raised when time server is unavailable"""
    pass