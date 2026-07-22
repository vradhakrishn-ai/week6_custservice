from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    app_name: str = "SecureBank Assistant"
    default_role: str = "customer"
    use_mock_backends: bool = True
