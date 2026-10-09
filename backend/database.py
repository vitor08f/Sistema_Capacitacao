from collections.abc import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .settings import configuracoes


class Base(DeclarativeBase):
    pass


opcoes_motor = {"pool_pre_ping": True}
if configuracoes.url_banco_dados.startswith("sqlite"):
    opcoes_motor["connect_args"] = {"check_same_thread": False, "timeout": 30}
motor_banco_dados = create_engine(configuracoes.url_banco_dados, **opcoes_motor)
fabrica_sessoes = sessionmaker(bind=motor_banco_dados, expire_on_commit=False)


def obter_sessao_banco() -> Generator[Session, None, None]:
    sessao = fabrica_sessoes()
    try:
        yield sessao
    finally:
        sessao.close()


def migrar_esquema_sqlite() -> None:
    """Renomeia a estrutura anterior em SQLite sem descartar contatos existentes."""
    if motor_banco_dados.dialect.name != "sqlite":
        return

    with motor_banco_dados.begin() as conexao:
        tabelas = set(inspect(conexao).get_table_names())
        if "leads" in tabelas:
            if "contatos" in tabelas:
                quantidade = conexao.scalar(text("SELECT COUNT(*) FROM contatos"))
                if quantidade:
                    raise RuntimeError(
                        "O SQLite contém as tabelas 'leads' e 'contatos' com dados. "
                        "Faça uma cópia de segurança e consolide-as antes de iniciar a aplicação."
                    )
                conexao.exec_driver_sql("DROP TABLE contatos")
            conexao.exec_driver_sql("ALTER TABLE leads RENAME TO contatos")
            for nome_antigo, nome_novo in (
                ("id", "id_contato"),
                ("nome", "nome_completo"),
                ("formato", "formato_atendimento"),
            ):
                colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("contatos")}
                if nome_antigo in colunas and nome_novo not in colunas:
                    conexao.exec_driver_sql(
                        f'ALTER TABLE contatos RENAME COLUMN "{nome_antigo}" TO "{nome_novo}"'
                    )

        if "agendamentos" in tabelas:
            for nome_antigo, nome_novo in (
                ("id", "id_agendamento"),
                ("lead_id", "contato_id"),
                ("inicio", "data_hora_inicio"),
                ("fim", "data_hora_fim"),
                ("status", "status_agendamento"),
            ):
                colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("agendamentos")}
                if nome_antigo in colunas and nome_novo not in colunas:
                    conexao.exec_driver_sql(
                        f'ALTER TABLE agendamentos RENAME COLUMN "{nome_antigo}" TO "{nome_novo}"'
                    )
            conexao.exec_driver_sql("DROP INDEX IF EXISTS ix_agendamentos_lead_id")

        if "bloqueios" in tabelas:
            for nome_antigo, nome_novo in (
                ("id", "id_bloqueio"),
                ("inicio", "data_hora_inicio"),
                ("fim", "data_hora_fim"),
            ):
                colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("bloqueios")}
                if nome_antigo in colunas and nome_novo not in colunas:
                    conexao.exec_driver_sql(
                        f'ALTER TABLE bloqueios RENAME COLUMN "{nome_antigo}" TO "{nome_novo}"'
                    )
