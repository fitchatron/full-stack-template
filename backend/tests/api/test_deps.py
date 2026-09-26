import uuid
from datetime import UTC, timedelta

import jwt
import pytest
from fastapi import HTTPException
from faker import Faker
from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.api.deps import AuthorizeUser
from app.core.security import ALGORITHM, create_access_token

Faker.seed(settings.DEFAULT_FAKER_SEED)

fake = Faker()


@pytest.mark.parametrize(
    "required_permissions, granted_user_roles, expected_result",
    [
        pytest.param(
            [],
            [],
            True,
            id="no_required_permissions with no granted permissions",
        ),
        pytest.param(
            [],
            [
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="no_required_permissions",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS],
            [
                {
                    "permissions": [AppPermissions.CREATE__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="exact_permission_match",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS],
            [
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="required_permission_subset_of_granted_permissions",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS],
            [
                {
                    "permissions": [AppPermissions.ASTERISK__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="required_permission_granted_via_asterisk",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS],
            [
                {
                    "permissions": [AppPermissions.ASTERISK__ASTERISK],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="required_permission_granted_via_double_asterisk",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [AppPermissions.ASTERISK__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="multiple_required_permissions_granted_via_asterisk",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [AppPermissions.ASTERISK__ASTERISK],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            True,
            id="multiple_required_permissions_granted_via_double_asterisk",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.UPDATE__USERS],
            [],
            False,
            id="multiple_required_permissions_no_granted_permissions",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.UPDATE__USERS],
            [
                {
                    "permissions": [AppPermissions.READ__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            False,
            id="multiple_required_permissions_required_permission_not_granted",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [AppPermissions.CREATE__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            False,
            id="required_permission_not_fully_granted",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [AppPermissions.CREATE__USERS],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                }
            ],
            False,
            id="required_permission_not_fully_granted",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(start_date="-30d", tzinfo=UTC),
                    "end_at": fake.past_datetime(start_date="-1d", tzinfo=UTC),
                }
            ],
            False,
            id="required_permission_expired",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [
                        AppPermissions.ASTERISK__ASTERISK,
                    ],
                    "start_at": fake.past_datetime(start_date="-30d", tzinfo=UTC),
                    "end_at": fake.past_datetime(start_date="-1d", tzinfo=UTC),
                },
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                },
            ],
            True,
            id="required_permission_expired_asterisk_asterisk_valid_granted",
        ),
        pytest.param(
            [AppPermissions.CREATE__USERS, AppPermissions.READ__USERS],
            [
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(start_date="-30d", tzinfo=UTC),
                    "end_at": fake.past_datetime(start_date="-1d", tzinfo=UTC),
                },
                {
                    "permissions": [
                        AppPermissions.CREATE__USERS,
                        AppPermissions.READ__USERS,
                    ],
                    "start_at": fake.past_datetime(tzinfo=UTC),
                    "end_at": fake.future_datetime(tzinfo=UTC),
                },
            ],
            True,
            id="required_permission_expired_regranted",
        ),
    ],
)
def test_authorize_user_is_authorized(
    db_session,
    act_as_user,
    grant_permissions,
    required_permissions,
    granted_user_roles,
    expected_result,
):
    user = act_as_user
    user_roles = []
    for ur in granted_user_roles:
        user_roles.append(
            grant_permissions(
                user,
                **ur,
            )
        )

    authorize_user = AuthorizeUser(required_permissions=required_permissions)
    assert expected_result == authorize_user._is_authorized(
        session=db_session, user_id=user.user_id
    )


# def test_authN():
#     assert True == False


# MARK: _get_current_user
def test_get_current_user_returns_user_for_valid_token(db_session, act_as_user):
    token = create_access_token(act_as_user.user_id, timedelta(minutes=5))

    user = AuthorizeUser()._get_current_user(db_session, token)

    assert user.user_id == act_as_user.user_id


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(
            create_access_token(uuid.uuid4(), timedelta(seconds=-1)),
            id="expired",
        ),
        pytest.param(
            jwt.encode(
                {"sub": str(uuid.uuid4())},
                "not-the-secret-key-but-long-enough-for-hs256",
                ALGORITHM,
            ),
            id="wrong_signing_key",
        ),
        pytest.param(
            create_access_token("not-a-uuid", timedelta(minutes=5)),
            id="subject_not_a_uuid",
        ),
        pytest.param(
            jwt.encode({}, settings.SECRET_KEY, ALGORITHM),
            id="missing_subject",
        ),
        pytest.param("not-a-jwt", id="malformed"),
    ],
)
def test_get_current_user_rejects_invalid_token(db_session, token):
    with pytest.raises(HTTPException) as exc_info:
        AuthorizeUser()._get_current_user(db_session, token)

    assert exc_info.value.status_code == 403


def test_get_current_user_unknown_user(db_session):
    token = create_access_token(uuid.uuid4(), timedelta(minutes=5))

    with pytest.raises(HTTPException) as exc_info:
        AuthorizeUser()._get_current_user(db_session, token)

    assert exc_info.value.status_code == 404


def test_get_current_user_inactive_user(db_session, act_as_user):
    act_as_user.is_active = False
    db_session.flush()
    token = create_access_token(act_as_user.user_id, timedelta(minutes=5))

    with pytest.raises(HTTPException) as exc_info:
        AuthorizeUser()._get_current_user(db_session, token)

    assert exc_info.value.status_code == 400
