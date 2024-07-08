import app.main

def test_page_size():
    assert app.main.DbInfo("sample.db").page_size == 4096
