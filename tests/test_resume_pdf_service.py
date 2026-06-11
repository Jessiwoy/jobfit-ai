from services.resume_pdf_service import build_resume_autofill, make_pdf_text_readable


def test_make_pdf_text_readable_collapses_character_spaced_words() -> None:
    text = "D e s e n v o l v e d o r a  d e  S o f t w a r e\nR e a c t . j s"

    readable_text = make_pdf_text_readable(text)

    assert readable_text == "Desenvolvedora de Software\nReact.js"


def test_build_resume_autofill_extracts_score_relevant_fields() -> None:
    text = """
--- PAGE 1 ---
Desenvolvedora de software com experiência no desenvolvimento end-to-end de aplicações web.
Especializações:
Frontend: React.js, React Native, TypeScript, JavaScript, HTML5, CSS3, TailwindCSS, Vite
Backend: Node.js, Express.js, APIs REST
JESSICA
WOYTUSKI
RESUMO
Desenvolvedora de Software | Reactjs | React Native | Nodejs
Palhoça, SC - Brasil
jessica.w.dev@gmail.com
Rovaris Tech - PJ
Desenvolvedor de Software | Reactjs | React Native | Nodejs
Programa Flexível
Desenvolvimento de aplicação fullstack de nutrição, com frontend em React estruturado.
Property Sales
Desenvolvimento de aplicação web com React, TypeScript, TailwindCSS e Vite.
"""

    autofill = build_resume_autofill(user_id=1, readable_text=text)

    assert autofill.name == "Jessica Woytuski"
    assert autofill.email == "jessica.w.dev@gmail.com"
    assert autofill.current_title == "Desenvolvedora de Software | Reactjs | React Native | Nodejs"
    assert "React.js" in autofill.technologies
    assert "TypeScript" in autofill.technologies
    assert "React" in autofill.required_terms
    assert any(item.name == "Programa Flexível" for item in autofill.profile_items)
    assert any(
        item.item_type == "technology" and item.name == "React.js"
        for item in autofill.profile_items
    )
