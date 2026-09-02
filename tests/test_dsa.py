def test_if_else(capsys):
    code = """
def check(val):
    if val > 10:
        print("large")
    else:
        print("small")

check(15)
check(5)
"""
    run_pylite(code)
    assert capsys.readouterr().out == "large\nsmall\n"