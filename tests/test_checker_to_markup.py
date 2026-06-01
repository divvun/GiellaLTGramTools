import pytest

from giellaltgramtools.grammar_error_annotated_sentence import (
    divvun_checker_output_to_grammar_error_annotated_sentence,
)


@pytest.mark.parametrize(
    ("error_as_string", "wanted_sentence"),
    [
        (
            r"""{"errs":[["la",17,19,"msyn-l-not-la","Dákkir kontevstan hiehpá \"la\" sajen adnet \"l\"",["l"],"\"Liehket\": \"l\" farra gå \"la\""]],"text":"Æjgátkonferánssa la ájnas tjåhkanimsadje gå galggá aktisattjat barggat oahppe/máná hárráj."}""",  # noqa: E501
            "Æjgátkonferánssa {la}§{msyn-l-not-la|l} ájnas tjåhkanimsadje gå galggá "
            "aktisattjat barggat oahppe/máná hárráj.",
        ),
        (
            r"""{"errs":[["dáhttun",14,21,"real-DerNomActSgGen-PrfPrc","Sátni šaddá eará go oaivvilduvvo.",["dáhtton"],"Čállinmeattáhus dán oktavuođas"]],"text":"Eat lean olus dáhttun."}""",  # noqa: E501
            "Eat lean olus {dáhttun}§{real-DerNomActSgGen-PrfPrc|dáhtton}.",
        ),
        (
            r"""{"errs":[["gelddolas",0,9,"typo","Hápmi ii leat sátnelisttus.",["gelddolaš","gulddolaš","gilddolaš","guldalas","gelddolačča","gáldolaš","galddalaš","gielddalaš","gealdálas","gulddalmas"],"Čállinmeattáhus"]],"text":"gelddolas"}""",  # noqa: E501
            "{gelddolas}${typo|gelddolaš,gulddolaš,gilddolaš,guldalas,gelddolačča,gáldolaš,galddalaš,gielddalaš,gealdálas,gulddalmas}",
        ),
        (
            r"""{"errs":[["valjis",19,25,"lex-valjis-valljugas","lex-valjis-valljugas",["valljugas"],"lex-valjis-valljugas"]],"text":"Guovdageainnus lea valjis ja girjás kultureallin."}""",  # noqa: E501
            "Guovdageainnus lea {valjis}§{lex-valjis-valljugas|valljugas} ja girjás "
            "kultureallin.",
        ),
    ],
)
def test_divvun_checker_to_markup(error_as_string, wanted_sentence):
    error_data = divvun_checker_output_to_grammar_error_annotated_sentence(
        error_as_string
    )

    assert error_data.to_manual_markup() == wanted_sentence
