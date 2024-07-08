import app.main

def test_page_size():
    assert app.main.db_info("sample.db").page_size == 4096
