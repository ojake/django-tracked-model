"""Test for ``control`` module"""
# pylint: disable=unexpected-keyword-arg
import pytest

from tests import models

from tracked_model.defs import ActionType
from tracked_model.models import History
from tracked_model.control import create_track_token


pytestmark = pytest.mark.django_db


def test_tracked_model_diff():
    """Test ``TrackedModelMixin._tarcked_model_diff``"""
    model = models.BasicModel.objects.create(some_num=3, some_txt='lol')
    diff = model._tracked_model_diff()

    assert diff is None


def test_tracked_model_save_and_delete_and_model_history_with_no_request():
    """Test ``TrackedModel`` saving and deleting without request"""
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save()
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save()
    assert history().count() == 1
    model.some_num = 5
    model.save()
    assert history().count() == 2
    raw_history = History.objects.filter(
        table_name=model._meta.db_table, table_id=model.pk)
    assert raw_history.count() == 2
    model.delete()
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(
        revision_author__isnull=False).exists()


def test_tracked_model_save_and_delete_and_model_history_with_request(
        rf, admin_user):
    """Test ``TrackedModel`` saving and deleting with authenticated request
    """
    request = rf.get('/')
    request.user = admin_user
    request.is_authenticated = lambda: True
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save(request=request)
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save(request=request)
    assert history().count() == 1
    model.some_num = 5
    model.save(request=request)
    assert history().count() == 2
    raw_history = History.objects.filter(
        table_name=model._meta.db_table, table_id=model.pk)
    assert raw_history.count() == 2
    model.delete(request=request)
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(revision_author__isnull=True).exists()

    assert raw_history.filter(revision_author=admin_user).count() == 3


def test_tracked_model_save_and_delete_and_model_history_with_token(
        rf, admin_user):
    """Test ``TrackedModel`` saving and deleting with authenticated request
    """
    request = rf.get('/')
    request.user = admin_user
    request.is_authenticated = lambda: True
    token = create_track_token(request)
    model = models.BasicModel(some_num=3, some_txt='lol')
    history = model.tracked_model_history
    assert history().count() == 0
    model.save(track_token=token)
    assert history().count() == 1
    assert history().first().action_type == ActionType.CREATE
    model.some_num = 3
    model.save(track_token=token)
    assert history().count() == 1
    model.some_num = 5
    model.save(track_token=token)
    assert model.tracked_model_history().count() == 2
    raw_history = History.objects.filter(
        table_name=model._meta.db_table, table_id=model.pk)
    assert raw_history.count() == 2
    model.delete(track_token=token)
    assert raw_history.count() == 3
    assert raw_history.filter(action_type=ActionType.CREATE).count() == 1
    assert raw_history.filter(action_type=ActionType.DELETE).count() == 1
    assert not History.objects.filter(revision_author__isnull=True).exists()

    assert raw_history.filter(revision_author=admin_user).count() == 3
