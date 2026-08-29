from app.eval import main


def test_eval_stub_prints_not_implemented(capsys):
    main()
    assert capsys.readouterr().out == "not implemented\n"
