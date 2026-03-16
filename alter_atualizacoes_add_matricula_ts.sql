-- Executar no MySQL antes de usar a nova versão da tela
ALTER TABLE `atualizacoes`
    ADD COLUMN `matricula` CHAR(8) NULL AFTER `subordinada`,
    ADD COLUMN `ts_cadastro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'quando o registro foi criado' AFTER `descricao`;

CREATE INDEX `ix_atualizacoes_matricula` ON `atualizacoes` (`matricula`);
CREATE INDEX `ix_atualizacoes_ts` ON `atualizacoes` (`ts_cadastro`);
