-- PostgreSQL 14+. Execute conectado ao banco advocacia_db.
CREATE TABLE IF NOT EXISTS leads (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL,
    telefone VARCHAR(30) NOT NULL,
    area_assunto VARCHAR(40) NOT NULL,
    formato VARCHAR(20) NOT NULL CHECK (formato IN ('Presencial', 'Remoto')),
    mensagem TEXT,
    consentimento_lgpd BOOLEAN NOT NULL CHECK (consentimento_lgpd = TRUE),
    consentido_em TIMESTAMPTZ NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lead_id BIGINT NOT NULL REFERENCES leads(id) ON DELETE RESTRICT,
    inicio TIMESTAMPTZ NOT NULL,
    fim TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'solicitado'
        CHECK (status IN ('solicitado', 'aprovado', 'cancelado')),
    criado_em TIMESTAMPTZ NOT NULL,
    CHECK (fim > inicio)
);
CREATE INDEX IF NOT EXISTS ix_agendamentos_lead_id ON agendamentos (lead_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_agendamentos_inicio_ativo
    ON agendamentos (inicio) WHERE status <> 'cancelado';

CREATE TABLE IF NOT EXISTS bloqueios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inicio TIMESTAMPTZ NOT NULL,
    fim TIMESTAMPTZ,
    motivo VARCHAR(120) NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL,
    CHECK (fim IS NULL OR fim > inicio)
);
