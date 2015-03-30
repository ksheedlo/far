import far.sessions as sessions
import pymongo

from far.helpers import find_where

def test_memory_creates_and_retrieves_sessions():
    store = sessions.MemorySsoStore()
    store.create_session('1234', {'answer': 42})
    sess = store.lookup_by_session_id('1234')
    assert sess['answer'] == 42

def test_memory_returns_none_for_nonexistent_session():
    store = sessions.MemorySsoStore()
    assert store.lookup_by_session_id('6789') is None

def test_memory_destroys_sessions():
    store = sessions.MemorySsoStore()
    store.create_session('1234', {'answer': 42})
    store.destroy_session('1234')
    assert store.lookup_by_session_id('1234') is None

def test_memory_adds_a_service_provider():
    store = sessions.MemorySsoStore()
    store.create_session('1234', {})
    store.add_service_provider_session('1234', 'spAAAA')
    assert store.logged_in_service_providers('1234') == ['spAAAA']

def test_memory_removes_a_service_provider():
    store = sessions.MemorySsoStore()
    store.create_session('1234', {})
    store.add_service_provider_session('1234', 'spAAAA')
    store.add_service_provider_session('1234', 'spBBBB')
    store.remove_service_provider_session('1234', 'spAAAA')
    assert store.logged_in_service_providers('1234') == ['spBBBB']
