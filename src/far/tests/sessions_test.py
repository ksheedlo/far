from far.sessions import MemoryStore

def test_it_creates_and_retrieves_sessions():
    store = MemoryStore()
    store.create_session('1234', {'answer': 42})
    sess = store.lookup_by_session_id('1234')
    assert sess['answer'] == 42

def test_it_returns_none_for_nonexistent_session():
    store = MemoryStore()
    assert store.lookup_by_session_id('6789') is None

def test_it_destroys_sessions():
    store = MemoryStore()
    store.create_session('1234', {'answer': 42})
    store.destroy_session('1234')
    assert store.lookup_by_session_id('1234') is None

def test_it_adds_a_service_provider():
    store = MemoryStore()
    store.create_session('1234', {})
    store.add_service_provider_session('1234', 'spAAAA')
    assert store.logged_in_service_providers('1234') == ['spAAAA']

def test_it_removes_a_service_provider():
    store = MemoryStore()
    store.create_session('1234', {})
    store.add_service_provider_session('1234', 'spAAAA')
    store.add_service_provider_session('1234', 'spBBBB')
    store.remove_service_provider_session('1234', 'spAAAA')
    assert store.logged_in_service_providers('1234') == ['spBBBB']
