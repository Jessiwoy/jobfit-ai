from core.models import EmailMessage
from services.parsers.glassdoor_parser import GlassdoorEmailParser
from services.parsers.indeed_parser import IndeedEmailParser
from services.parsers.linkedin_parser import LinkedInEmailParser


def test_indeed_parser_extracts_multiple_jobs_from_alert() -> None:
    message = EmailMessage(
        id=1,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
        received_at="2026-06-12T10:00:00-03:00",
        raw_text="""
Indeed Job Alert
Jobs 1-2 of 2 new jobs

21634-ANALISTA DESENVOLVEDOR JR
Hitss Brasil - Remoto
Conhecimento em desenvolvimento Java.
ha 2 dias
https://br.indeed.com/rc/clk/dl?jk=abc

Frontend Developer
Neo Credito - Sao Paulo, SP
React e TypeScript.
Recem publicada
https://br.indeed.com/rc/clk/dl?jk=def
""",
        detected_provider="indeed",
    )

    jobs = IndeedEmailParser().parse(message)

    assert [job.title for job in jobs] == [
        "21634-ANALISTA DESENVOLVEDOR JR",
        "Frontend Developer",
    ]
    assert jobs[0].company == "Hitss Brasil"
    assert jobs[0].location == "Remoto"
    assert jobs[0].posted_at == "2026-06-10"
    assert jobs[1].company == "Neo Credito"
    assert jobs[1].posted_at == "2026-06-12"


def test_linkedin_parser_extracts_multiple_jobs_from_alert() -> None:
    message = EmailMessage(
        id=1,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
        received_at="2026-06-12T10:00:00-03:00",
        raw_text="""
Resultados da nova pesquisa de vagas por IA

Frontend Engineer
Acme
Brasil
Visualizar vaga: https://www.linkedin.com/comm/jobs/view/111/?trackingId=a

---------------------------------------------------------

React Developer
Example Co
Brasil
Esta empresa esta contratando
Visualizar vaga: https://www.linkedin.com/comm/jobs/view/222/?trackingId=b
""",
        detected_provider="linkedin",
    )

    jobs = LinkedInEmailParser().parse(message)

    assert [job.title for job in jobs] == ["Frontend Engineer", "React Developer"]
    assert [job.company for job in jobs] == ["Acme", "Example Co"]
    assert jobs[0].job_url == "https://www.linkedin.com/comm/jobs/view/111/?trackingId=a"


def test_linkedin_parser_accepts_regular_jobs_view_urls() -> None:
    message = EmailMessage(
        id=1,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
        received_at="2026-06-12T10:00:00-03:00",
        raw_text="""
Resultados da nova pesquisa de vagas por IA

Desenvolvedor Fullstack
Acme
Brasil
Visualizar vaga: https://www.linkedin.com/jobs/view/4417966383/?trk=eml-email

---------------------------------------------------------

Frontend Developer
Example Co
Brasil
Visualizar vaga: https://www.linkedin.com/jobs/view/4417966384/?trk=eml-email
""",
        detected_provider="linkedin",
    )

    jobs = LinkedInEmailParser().parse(message)

    assert [job.title for job in jobs] == ["Desenvolvedor Fullstack", "Frontend Developer"]
    assert [job.company for job in jobs] == ["Acme", "Example Co"]
    assert jobs[0].job_url == "https://www.linkedin.com/jobs/view/4417966383/?trk=eml-email"


def test_glassdoor_parser_extracts_multiple_jobs_from_alert() -> None:
    message = EmailMessage(
        id=1,
        source_id=1,
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        gmail_label_name="Job Alerts",
        received_at="2026-06-12T10:00:00-03:00",
        raw_text="""
Alerta de vaga: Desenvolvedor React
Seus anuncios de vagas - 8 de junho de 2026
Desenvolvedor React
Brasil
Mazzatech
4.0 ★
Desenvolvedor(a) ReactJS
Sao Paulo, Sao Paulo
Candidatura rapida
9 dia(s)
https://www.glassdoor.com.br/job-listing/reactjs-mazzatech-JV.htm
Maxxi
4.4 ★
Desenvolvedor(a) Front-end React/Next.js Pleno
Trabalho remoto
Candidatura rapida
11 dia(s)
https://www.glassdoor.com.br/job-listing/frontend-maxxi-JV.htm
""",
        detected_provider="glassdoor",
    )

    jobs = GlassdoorEmailParser().parse(message)

    assert [job.title for job in jobs] == [
        "Desenvolvedor(a) ReactJS",
        "Desenvolvedor(a) Front-end React/Next.js Pleno",
    ]
    assert [job.company for job in jobs] == ["Mazzatech", "Maxxi"]
    assert jobs[1].location == "Trabalho remoto"
    assert jobs[0].posted_at == "2026-06-03"
    assert jobs[1].posted_at == "2026-06-01"
    assert jobs[0].job_url == "https://www.glassdoor.com.br/job-listing/reactjs-mazzatech-JV.htm"
    assert jobs[1].job_url == "https://www.glassdoor.com.br/job-listing/frontend-maxxi-JV.htm"
