USE fenago;

CREATE INDEX dayquote06_sector_idx ON dayquote06 (sector);

USE fenago;

SELECT symbol FROM dayquote06 WHERE sector = 'Properties';
