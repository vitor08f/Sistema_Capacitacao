--DATABASE Relacional PostgreSQL 

CREATE DATABASE advocacia_db
\c advocacia_db

CREATE TYPE area_assunto_enum AS ENUM (
    'Civil',
    'Familia e Sucessoes',
    'Trabalhista',
    'Empresarial',
    'Previdenciario',
    'Consumidor',
	'Outro'
);

CREATE TYPE formato_enum AS ENUM (
    'Presencial',
    'Remoto'
);

CREATE TABLE leads (
    id_lead INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    area_assunto area_assunto_enum NOT NULL,
    formato formato_enum NOT NULL,
    data_atendimento DATE NOT NULL,
    horario TIME NOT NULL
    mensagem TEXT,
);

CREATE TABLE agendamento(
	id_agendamento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	lead_id INT NOT NULL,
    data_agendamento DATE NOT NULL,
    horario TIME NOT NULL,
    status_agendamento VARCHAR(20) DEFAULT 'confirmado',

    CONSTRAINT fk_agendamento_lead
        FOREIGN KEY (lead_id) REFERENCES leads (id_lead) ON DELETE RESTRICT,

);

CREATE INDEX idx_agendamentos_lead ON agendamentos (lead_id);
 
-- Um horário só pode ter UM agendamento ativo; cancelados liberam o horário
CREATE UNIQUE INDEX horario_unico
    ON agendamentos (data_agendamento, horario)
    WHERE status_agendamento <> 'cancelado';


	
