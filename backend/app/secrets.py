"""Secrets manager pattern.

The prototype reads from environment variables, but everything that needs a
secret goes through this provider — so swapping in AWS Secrets Manager,
HashiCorp Vault, or GCP Secret Manager means implementing one class here and
changing nothing else.
"""
import os


class SecretsProvider:
    def get(self, name: str, default: str | None = None) -> str | None:
        raise NotImplementedError


class EnvSecretsProvider(SecretsProvider):
    """Environment-backed secrets — fine for a prototype.

    # PRODUCTION SWAP: implement AwsSecretsManagerProvider(SecretsProvider)
    # (boto3 secretsmanager get_secret_value) or VaultProvider (hvac client),
    # and return it from get_secrets_provider() based on deployment config.
    """

    def get(self, name: str, default: str | None = None) -> str | None:
        return os.environ.get(name, default)


_provider: SecretsProvider = EnvSecretsProvider()


def get_secrets_provider() -> SecretsProvider:
    return _provider
