class OTPPurpose:
    """
        Enumeration of valid OTP purposes.
        OTP purpose validation.
    """
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    LOGIN_2FA = "login_2fa"
    PHONE_VERIFICATION = "phone_verification"
    ACCOUNT_DELETION = "account_deletion"
    
    @classmethod
    def all_purposes(cls):
        return [cls.EMAIL_VERIFICATION, cls.PASSWORD_RESET, cls.LOGIN_2FA, 
                cls.PHONE_VERIFICATION, cls.ACCOUNT_DELETION]
    
    @classmethod
    def is_valid(cls, purpose: str) -> bool:
        return purpose in cls.all_purposes()