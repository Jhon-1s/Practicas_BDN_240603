CREATE DATABASE IF NOT EXISTS `db_test_7b` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */;
USE `db_test_7b`;

DROP TABLE IF EXISTS `tb_logs`;
CREATE TABLE `tb_logs` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `table_name` varchar(80) NOT NULL,
  `table_operation` enum('Create','Read','Update','Delete') DEFAULT NULL,
  `db_user` varchar(80) NOT NULL,
  `operation_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `operation_description` text NOT NULL,
  `operation_status` bit(1) DEFAULT b'1',
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ------------------------------------------------------
-- Datos de `tb_logs` (Base de Jonathan + Registros de Vanessa)
-- ------------------------------------------------------
LOCK TABLES `tb_logs` WRITE;
INSERT INTO `tb_logs` VALUES 
-- Registros originales de Jonathan
(1,'tb_users','Create','root@localhost','2026-09-10 10:30:31','Usuario creado. ID=2, email=240603@utxicotepec.edu.mx, nick=Jonathan I Leal Cruz, creation_date=2026-09-10 10:30:31, status=',_binary ''),
(2,'tb_users','Create','root@localhost','2026-09-10 10:34:14','Usuario creado. ID=3, email=240451@utxicotepec.edu.mx, nick=Oliver, creation_date=2026-09-10 10:34:14, status=',_binary ''),
(3,'tb_users','Create','root@localhost','2026-09-10 10:34:41','Usuario creado. ID=4, email=fer@utxicotepec.edu.mx, nick=Fernada, creation_date=2026-09-10 10:34:41, status=',_binary ''),
(4,'tb_users','Create','root@localhost','2026-09-10 11:28:08','Usuario creado. ID=5, email=noc@utxicotepec.edu.mx, nick=noc, creation_date=2026-09-10 11:28:08, status=',_binary ''),
-- Nuevos registros incorporados desde la otra base de datos
(5,'tb_users','Create','josu.oloarte@PC-15','2026-09-10 11:26:03','Usuario creado. ID=6, email=240272@utxicotepec.edu.mx, nick=Josue Oloarte, creation_date=2026-09-10 11:26:03, status=',_binary ''),
(6,'tb_users','Create','josu.oloarte@PC-15','2026-09-10 11:27:08','Usuario creado. ID=7, email=240383@utxicotepec.edu.mx, nick=Samuel Ramírez, creation_date=2026-09-10 11:27:08, status=',_binary ''),
(7,'tb_users','Delete','josu.oloarte@PC-15','2026-09-10 12:41:39','Usuario eliminado. ID=8, email=240234@utxicotepec.edu.mx, nick=Jeysi Lara, creation_date=2026-09-10 11:28:09, last_update=NULL, last_login=NULL, status=1',_binary ''),
(8,'tb_users','Update','josu.oloartea@PC-15','2026-09-10 12:42:25','Usuario actualizado. ID=7. Cambios: nick: Samuel Ramírez -> Sam, last_update: NULL -> 2026-09-10 12:42:25',_binary '');
UNLOCK TABLES;

-- ------------------------------------------------------
-- Estructura de la tabla `tb_users` (Base de Jonathan)
-- ------------------------------------------------------
DROP TABLE IF EXISTS `tb_users`;
CREATE TABLE `tb_users` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `nick` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `creation_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_update` datetime DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `status` bit(1) DEFAULT b'1',
  PRIMARY KEY (`ID`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `nick` (`nick`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ------------------------------------------------------
-- Datos de `tb_users` (Base de Jonathan + Usuarios adicionales)
-- ------------------------------------------------------
LOCK TABLES `tb_users` WRITE;
INSERT INTO `tb_users` VALUES 
-- Registros originales de Jonathan
(2,'240603@utxicotepec.edu.mx','Jonathan I Leal Cruz','1a6f89f86833682a7e317b024a47a95a','2026-09-10 10:30:31',NULL,NULL,_binary ''),
(3,'240451@utxicotepec.edu.mx','Oliver','7e26843d24a98c0b9df85297c46d829a','2026-09-10 10:34:14',NULL,NULL,_binary ''),
(4,'fer@utxicotepec.edu.mx','Fernada','fbc4fef99cdd459c958f92ef36c9fe2b','2026-09-10 10:34:41',NULL,NULL,_binary ''),
(5,'noc@utxicotepec.edu.mx','noc','5ff757a2a8e7b7cf273c05b7d67a6170','2026-09-10 11:28:08',NULL,NULL,_binary ''),
-- Nuevos usuarios incorporados desde la otra base de datos
(6,'240272@utxicotepec.edu.mx','Josue Oloarte','827ccb0eea8a706c4c34a16891f84e7b','2026-09-10 11:26:03',NULL,NULL,_binary ''),
(7,'240383@utxicotepec.edu.mx','Sam','827ccb0eea8a706c4c34a16891f84e7b','2026-09-10 11:27:08','2026-09-10 12:42:25',NULL,_binary '');
UNLOCK TABLES;

-- ------------------------------------------------------
-- Triggers añadidos desde la segunda base de datos
-- ------------------------------------------------------
DELIMITER ;;

CREATE TRIGGER `trg_users_after_insert` AFTER INSERT ON `tb_users` FOR EACH ROW BEGIN
    INSERT INTO tb_logs (
        table_name,
        table_operation,
        db_user,
        operation_description,
        operation_date,
        operation_status
    )
    VALUES (
        'tb_users',
        'Create',
        USER(),
        CONCAT(
            'Usuario creado. ID=', NEW.ID,
            ', email=', NEW.email,
            ', nick=', NEW.nick,
            ', creation_date=', NEW.creation_date,
            ', status=', NEW.status
        ),
        CURRENT_TIMESTAMP,
        b'1'
    );
END ;;

CREATE TRIGGER `trg_users_after_update` AFTER UPDATE ON `tb_users` FOR EACH ROW BEGIN
    DECLARE cambios TEXT;

    SET cambios = CONCAT_WS(
        ', ',
        IF(NOT (OLD.email <=> NEW.email), CONCAT('email: ', IFNULL(OLD.email, 'NULL'), ' -> ', IFNULL(NEW.email, 'NULL')), NULL),
        IF(NOT (OLD.nick <=> NEW.nick), CONCAT('nick: ', IFNULL(OLD.nick, 'NULL'), ' -> ', IFNULL(NEW.nick, 'NULL')), NULL),
        IF(NOT (OLD.password <=> NEW.password), 'password: [MODIFICADA]', NULL),
        IF(NOT (OLD.creation_date <=> NEW.creation_date), CONCAT('creation_date: ', IFNULL(OLD.creation_date, 'NULL'), ' -> ', IFNULL(NEW.creation_date, 'NULL')), NULL),
        IF(NOT (OLD.last_update <=> NEW.last_update), CONCAT('last_update: ', IFNULL(OLD.last_update, 'NULL'), ' -> ', IFNULL(NEW.last_update, 'NULL')), NULL),
        IF(NOT (OLD.last_login <=> NEW.last_login), CONCAT('last_login: ', IFNULL(OLD.last_login, 'NULL'), ' -> ', IFNULL(NEW.last_login, 'NULL')), NULL),
        IF(NOT (OLD.status <=> NEW.status), CONCAT('status: ', IFNULL(CAST(OLD.status AS UNSIGNED), 'NULL'), ' -> ', IFNULL(CAST(NEW.status AS UNSIGNED), 'NULL')), NULL)
    );

    INSERT INTO tb_logs (
        table_name,
        table_operation,
        db_user,
        operation_date,
        operation_description,
        operation_status
    )
    VALUES (
        'tb_users',
        'Update',
        USER(),
        CURRENT_TIMESTAMP,
        CONCAT(
            'Usuario actualizado. ID=', NEW.ID,
            '. Cambios: ', IFNULL(NULLIF(cambios, ''), 'Sin cambios de valor')
        ),
        b'1'
    );
END ;;

CREATE TRIGGER `trg_users_after_delete` AFTER DELETE ON `tb_users` FOR EACH ROW BEGIN
    INSERT INTO tb_logs (
        table_name,
        table_operation,
        db_user,
        operation_date,
        operation_description,
        operation_status
    )
    VALUES (
        'tb_users',
        'Delete',
        USER(),
        CURRENT_TIMESTAMP,
        CONCAT(
            'Usuario eliminado. ',
            'ID=', OLD.ID,
            ', email=', OLD.email,
            ', nick=', OLD.nick,
            ', creation_date=', OLD.creation_date,
            ', last_update=', IFNULL(OLD.last_update, 'NULL'),
            ', last_login=', IFNULL(OLD.last_login, 'NULL'),
            ', status=', IFNULL(CAST(OLD.status AS UNSIGNED), 'NULL')
        ),
        b'1'
    );
END ;;

DELIMITER ;