DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS movimiento;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    user_type TEXT NOT NULL
);

CREATE TABLE movimiento (
    id VARCHAR(20) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(100) NOT NULL,
    destino VARCHAR(100) NOT NULL,
    comentario TEXT,
    monto DECIMAL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);