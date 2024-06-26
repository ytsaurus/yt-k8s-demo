import typing

import attr
from cryptography import fernet


@attr.s(frozen=True)
class CryptoKeysConfig:
    map_id_key: dict[str, str] = attr.ib()
    actual_key_id: str = attr.ib()


class EncryptedData(typing.TypedDict):
    key_id: str
    key_kind: str
    cypher_text: str


@attr.s
class CryptoController:
    key_kind = "local_fernet"

    _key_config: CryptoKeysConfig = attr.ib()
    _map_key_id_fernet_instance: typing.Dict[str, fernet.Fernet] = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self._map_key_id_fernet_instance = {key_id: fernet.Fernet(key_val) for key_id, key_val in self._key_config.map_id_key.items()}

    def copy(self) -> "CryptoController":
        return attr.evolve(self)

    def encrypt(self, key_id: str, plain_text: typing.Optional[str]) -> typing.Optional[EncryptedData]:
        if plain_text is None:
            return None

        encoded_plain_text = plain_text.encode()
        cypher_text = self._map_key_id_fernet_instance[key_id].encrypt(encoded_plain_text).decode()
        return dict(
            key_id=key_id,
            key_kind=self.key_kind,
            cypher_text=cypher_text,
        )

    def decrypt(self, encrypted_data: typing.Optional[EncryptedData]) -> typing.Optional[str]:
        if encrypted_data is None:
            return None

        assert encrypted_data["key_kind"] == self.key_kind
        encoded_cypher_text = encrypted_data["cypher_text"].encode()
        key_id = encrypted_data["key_id"]
        plain_text = self._map_key_id_fernet_instance[key_id].decrypt(encoded_cypher_text).decode()
        return plain_text

    def encrypt_with_actual_key(self, plain_text: typing.Optional[str]) -> typing.Optional[EncryptedData]:
        return self.encrypt(key_id=self._key_config.actual_key_id, plain_text=plain_text)

    @property
    def actual_key_id(self) -> str:
        return self._key_config.actual_key_id


def make_datalens_cypher(passsword):
    crypto_keys_config = CryptoKeysConfig(
        map_id_key={"key_1": "h1ZpilcYLYRdWp7Nk8X1M1kBPiUi8rdjz9oBfHyUKIk="},  # env: {DL_CRY_KEY_VAL_ID_{key} => value}
        actual_key_id="key_1",  # env: DL_CRY_ACTUAL_KEY_ID
    )
    crypto_controller = CryptoController(crypto_keys_config)
    return crypto_controller.encrypt_with_actual_key(passsword)["cypher_text"]
