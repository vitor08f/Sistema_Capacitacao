CREATE DATABASE advocacia_db

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
    id_lead SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    area_assunto area_assunto_enum NOT NULL,
    formato formato_enum NOT NULL,
    data_atendimento DATE,
    horario TIME
);

CREATE TABLE agendamento(
	id_agendamento SERIAL PRIMARY KEY,
	lead_id INT NOT NULL,
    data_agendamento DATE NOT NULL,
    horario TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmado',

    CONSTRAINT fk_agendamento_lead
        FOREIGN KEY (lead_id)
        REFERENCES leads(id),

    CONSTRAINT horario_unico
        UNIQUE (data, horario)
);
	
)