class BasePaymentsServiceError(Exception):
    pass


class AlreadyPurchasedError(BasePaymentsServiceError):
    pass


class AsyncAPIUnavailableError(BasePaymentsServiceError):
    pass


class YookassaUnavailableError(BasePaymentsServiceError):
    pass


class PermissionDeniedError(BasePaymentsServiceError):
    pass


class NotAvalableForRefundError(BasePaymentsServiceError):
    pass


class IncorrectTransactionStatusError(BasePaymentsServiceError):
    pass


class AlreadyWatchedError(BasePaymentsServiceError):
    pass


class YookassaRefundError(BasePaymentsServiceError):
    pass
