from dataclasses import dataclass

@dataclass
class EmailConfig:
    pop_server: str
    pop_port: int
    pop_user: str
    pop_password: str
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_ssl: bool