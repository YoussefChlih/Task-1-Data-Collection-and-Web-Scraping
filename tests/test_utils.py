import pandas as pd
from app.utils import scrape_data, generate_file

def test_scrape_data():
    # Mock or use a test URL
    df = scrape_data("https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)")
    assert isinstance(df, pd.DataFrame)

def test_generate_file():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    content = generate_file(df, 'csv')
    assert b'a,b' in content
