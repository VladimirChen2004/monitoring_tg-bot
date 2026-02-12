import pytest

from bot.db.queries import (
    create_user,
    deactivate_user,
    get_all_users,
    get_task_subscribers,
    get_user,
    toggle_notification,
)


@pytest.mark.asyncio
async def test_create_and_get_user(db_session):
    user = await create_user(db_session, user_id=123, full_name="Test User", is_admin=True)
    assert user.id == 123
    assert user.is_admin is True

    fetched = await get_user(db_session, 123)
    assert fetched is not None
    assert fetched.full_name == "Test User"


@pytest.mark.asyncio
async def test_deactivate_user(db_session):
    await create_user(db_session, user_id=456, full_name="To Remove")
    removed = await deactivate_user(db_session, 456)
    assert removed is True

    fetched = await get_user(db_session, 456)
    assert fetched is None  # get_user filters inactive


@pytest.mark.asyncio
async def test_get_all_users(db_session):
    await create_user(db_session, user_id=1, full_name="User 1")
    await create_user(db_session, user_id=2, full_name="User 2")
    users = await get_all_users(db_session)
    assert len(users) == 2


@pytest.mark.asyncio
async def test_toggle_notification(db_session):
    await create_user(db_session, user_id=100, full_name="Subscriber")

    # First toggle: creates pref, enabled=True
    state = await toggle_notification(db_session, 100, "documentation")
    assert state is True

    # Second toggle: disabled
    state = await toggle_notification(db_session, 100, "documentation")
    assert state is False

    # Third toggle: enabled again
    state = await toggle_notification(db_session, 100, "documentation")
    assert state is True


@pytest.mark.asyncio
async def test_get_task_subscribers(db_session):
    await create_user(db_session, user_id=10, full_name="Sub 1")
    await create_user(db_session, user_id=20, full_name="Sub 2")
    await create_user(db_session, user_id=30, full_name="Not Sub")

    await toggle_notification(db_session, 10, "documentation")
    await toggle_notification(db_session, 20, "documentation")

    subs = await get_task_subscribers(db_session, "documentation")
    assert set(subs) == {10, 20}
