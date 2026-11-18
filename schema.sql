-- Script de referência do banco (sintaxe SQLite).
-- O banco do projeto é criado pelas MIGRATIONS (flask db upgrade);
-- para gerar o SQL exato da migration, use: flask db upgrade --sql

CREATE TABLE usuarios (
    id         INTEGER      NOT NULL PRIMARY KEY,
    nome       VARCHAR(100) NOT NULL,
    email      VARCHAR(120) NOT NULL UNIQUE,
    criado_em  DATETIME     NOT NULL
);

CREATE TABLE categorias (
    id         INTEGER      NOT NULL PRIMARY KEY,
    nome       VARCHAR(50)  NOT NULL UNIQUE,
    descricao  VARCHAR(255)
);

CREATE TABLE rotinas (
    id            INTEGER      NOT NULL PRIMARY KEY,
    usuario_id    INTEGER      NOT NULL,
    categoria_id  INTEGER,
    nome          VARCHAR(100) NOT NULL,
    descricao     VARCHAR(255),
    ativa         BOOLEAN      NOT NULL,
    criado_em     DATETIME     NOT NULL,
    FOREIGN KEY (usuario_id)   REFERENCES usuarios (id),
    FOREIGN KEY (categoria_id) REFERENCES categorias (id)
);

CREATE TABLE execucoes (
    id          INTEGER      NOT NULL PRIMARY KEY,
    rotina_id   INTEGER      NOT NULL,
    data        DATE         NOT NULL,
    observacao  VARCHAR(255),
    criado_em   DATETIME     NOT NULL,
    FOREIGN KEY (rotina_id) REFERENCES rotinas (id),
    CONSTRAINT uq_execucao_rotina_data UNIQUE (rotina_id, data)
);

CREATE TABLE logs (
    id          INTEGER      NOT NULL PRIMARY KEY,
    usuario_id  INTEGER      NOT NULL,
    rotina_id   INTEGER,
    acao        VARCHAR(30)  NOT NULL,
    descricao   VARCHAR(255) NOT NULL,
    criado_em   DATETIME     NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    FOREIGN KEY (rotina_id)  REFERENCES rotinas (id)
);
