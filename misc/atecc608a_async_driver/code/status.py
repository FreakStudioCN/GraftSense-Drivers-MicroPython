# Static compatibility surface for source status imports.
class S:
    ATCA_SUCCESS = 0x00
    ATCA_WAKE_SUCCESS = 0x11
    ATCA_WATCHDOG_ABOUT_TO_EXPIRE = 0xEE
    def decode_error(self, error):
        return error, None

ATCA_SUCCESS = S.ATCA_SUCCESS
ATCA_WAKE_SUCCESS = S.ATCA_WAKE_SUCCESS
ATCA_WATCHDOG_ABOUT_TO_EXPIRE = S.ATCA_WATCHDOG_ABOUT_TO_EXPIRE
def decode_error(error):
    return S().decode_error(error)

