-- Base de datos FARO - Sistema de alerta temprana de bienestar estudiantil
-- Compatible con MySQL / MariaDB (XAMPP + phpMyAdmin)
-- Crea la base, las tablas de referencia y sus datos.
-- Los registros emocionales se importan aparte desde datos/registros_emocionales.csv

CREATE DATABASE IF NOT EXISTS faro CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE faro;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS registros_emocionales;
DROP TABLE IF EXISTS estudiantes;
DROP TABLE IF EXISTS contextos;
DROP TABLE IF EXISTS etiquetas_emocionales;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE estudiantes (
  id_estudiante INT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  edad INT, sexo CHAR(1), grupo VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO estudiantes VALUES (1, 'Ana Pérez', 12, 'F', '1ºA');
INSERT INTO estudiantes VALUES (2, 'Bruno Gómez', 12, 'M', '1ºA');
INSERT INTO estudiantes VALUES (3, 'Carla Rodríguez', 13, 'F', '1ºA');
INSERT INTO estudiantes VALUES (4, 'Diego Fernández', 13, 'M', '1ºB');
INSERT INTO estudiantes VALUES (5, 'Elena Silva', 12, 'F', '1ºB');
INSERT INTO estudiantes VALUES (6, 'Federico Martínez', 13, 'M', '1ºB');
INSERT INTO estudiantes VALUES (7, 'Gabriela López', 14, 'F', '2ºA');
INSERT INTO estudiantes VALUES (8, 'Hernán Cardozo', 14, 'M', '2ºA');
INSERT INTO estudiantes VALUES (9, 'Inés Acosta', 15, 'F', '2ºA');
INSERT INTO estudiantes VALUES (10, 'Joaquín Suárez', 14, 'M', '2ºB');
INSERT INTO estudiantes VALUES (11, 'Lucía Méndez', 15, 'F', '2ºB');
INSERT INTO estudiantes VALUES (12, 'Martín Castro', 15, 'M', '2ºB');
INSERT INTO estudiantes VALUES (13, 'Natalia Ramos', 16, 'F', '3ºA');
INSERT INTO estudiantes VALUES (14, 'Octavio Varela', 16, 'M', '3ºA');
INSERT INTO estudiantes VALUES (15, 'Paula Costa', 15, 'F', '3ºA');
INSERT INTO estudiantes VALUES (16, 'Rafael Sosa', 16, 'M', '3ºB');
INSERT INTO estudiantes VALUES (17, 'Sofía Díaz', 17, 'F', '3ºB');
INSERT INTO estudiantes VALUES (18, 'Tomás Moreira', 16, 'M', '3ºB');
INSERT INTO estudiantes VALUES (19, 'Valentina Benítez', 17, 'F', '4ºA');
INSERT INTO estudiantes VALUES (20, 'Agustín Álvarez', 17, 'M', '4ºA');
INSERT INTO estudiantes VALUES (21, 'Camila Torres', 18, 'F', '4ºA');
INSERT INTO estudiantes VALUES (22, 'Emiliano Ferreira', 17, 'M', '4ºB');
INSERT INTO estudiantes VALUES (23, 'Florencia Molina', 18, 'F', '4ºB');
INSERT INTO estudiantes VALUES (24, 'Ignacio Ríos', 17, 'M', '4ºB');
INSERT INTO estudiantes VALUES (25, 'Julieta Cabrera', 16, 'F', '3ºA');
INSERT INTO estudiantes VALUES (26, 'Leandro Morales', 15, 'M', '2ºB');
INSERT INTO estudiantes VALUES (27, 'Manuela Navarro', 14, 'F', '2ºA');
INSERT INTO estudiantes VALUES (28, 'Nicolás Ibarra', 13, 'M', '1ºB');
INSERT INTO estudiantes VALUES (29, 'Romina Perdomo', 17, 'F', '4ºA');
INSERT INTO estudiantes VALUES (30, 'Santiago Olivera', 16, 'M', '3ºB');

CREATE TABLE contextos (
  id_contexto INT PRIMARY KEY,
  ambito VARCHAR(40), situacion VARCHAR(60), descripcion VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO contextos VALUES (1, 'Aula', 'Clase regular', 'Registro tomado durante una jornada normal de clase.');
INSERT INTO contextos VALUES (2, 'Aula', 'Evaluación o prueba', 'Registro asociado a instancias de examen o entrega.');
INSERT INTO contextos VALUES (3, 'Recreo', 'Espacio social', 'Registro durante recreos o momentos de socialización.');
INSERT INTO contextos VALUES (4, 'Educación física', 'Actividad deportiva', 'Registro durante deporte o actividades físicas grupales.');
INSERT INTO contextos VALUES (5, 'Orientación', 'Entrevista con referente', 'Registro tomado en instancia con adscripto, psicólogo o asistente social.');
INSERT INTO contextos VALUES (6, 'Vínculos', 'Relaciones entre pares', 'Registro vinculado a la relación con compañeros y amistades.');
INSERT INTO contextos VALUES (7, 'Hogar', 'Situación familiar reportada', 'Registro donde el estudiante refiere su situación en casa.');
INSERT INTO contextos VALUES (8, 'Autopercepción', 'Estado general reportado', 'Registro de check-in de estado de ánimo general del día.');

CREATE TABLE etiquetas_emocionales (
  id_etiqueta INT PRIMARY KEY,
  nombre_etiqueta VARCHAR(50) NOT NULL,
  valencia_min DECIMAL(4,2) NOT NULL, valencia_max DECIMAL(4,2) NOT NULL,
  activacion_min DECIMAL(4,2) NOT NULL, activacion_max DECIMAL(4,2) NOT NULL,
  cuadrante VARCHAR(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO etiquetas_emocionales VALUES (1, 'Entusiasta', 0.3, 1.0, 0.3, 1.0, 'Positiva-Alta');
INSERT INTO etiquetas_emocionales VALUES (2, 'Calmo', 0.3, 1.0, -1.0, 0.29, 'Positiva-Baja');
INSERT INTO etiquetas_emocionales VALUES (3, 'Frustrado', -1.0, -0.3, 0.3, 1.0, 'Negativa-Alta');
INSERT INTO etiquetas_emocionales VALUES (4, 'Triste', -1.0, -0.3, -1.0, 0.29, 'Negativa-Baja');
INSERT INTO etiquetas_emocionales VALUES (5, 'Tenso', -0.29, 0.29, 0.6, 1.0, 'Neutra-Alta');
INSERT INTO etiquetas_emocionales VALUES (6, 'Alerta', -0.29, 0.29, 0.3, 0.59, 'Neutra-Media-Alta');
INSERT INTO etiquetas_emocionales VALUES (7, 'Neutro', -0.29, 0.29, -0.29, 0.29, 'Centro');
INSERT INTO etiquetas_emocionales VALUES (8, 'Cansado', -0.29, 0.29, -1.0, -0.3, 'Neutra-Baja');

-- Tabla para los registros emocionales. Importar los datos desde
-- datos/registros_emocionales.csv (phpMyAdmin > Importar), o dejar que el
-- pipeline los lea directo del CSV (comportamiento por defecto).
CREATE TABLE registros_emocionales (
  id_registro INT PRIMARY KEY,
  id_estudiante INT, id_contexto INT, fecha_hora DATETIME,
  valencia DECIMAL(4,2), activacion DECIMAL(4,2), comentario VARCHAR(255),
  FOREIGN KEY (id_estudiante) REFERENCES estudiantes(id_estudiante),
  FOREIGN KEY (id_contexto) REFERENCES contextos(id_contexto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
