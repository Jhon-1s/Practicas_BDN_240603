/* Creacion de usuarios remotos y asignacion de privilegios */
CREATE USER 'marco.ramirez'@'%' IDENTIFIED BY 'quwerty123';
CREATE USER 'jonathan.leal'@'%' IDENTIFIED BY '240603';
CREATE USER 'jeysi.lara'@'%' IDENTIFIED BY '240234';
CREATE USER 'margaret.rogas'@'%' IDENTIFIED BY '240242';

/*Asignar los privilegios de superusuario*/
GRANT ALL PRIVILEGES ON *.* TO 'jonathan.leal'@'%';

/*Asignar los privilegios de lectura, escritura, actualizacion y eliminacion a los usuarios remotos*/
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'marco.ramirez'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'jeysi.lara'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'margaret.rogas'@'%';

/*Creacio de roles y asignacion de privilegios a los roles*/
CREATE ROLE 'admin';
CREATE ROLE 'seller';
CREATE ROLE 'buyer';
CREATE ROLE 'guest';
CREATE ROLE 'support';
CREATE ROLE 'common';
CREATE ROLE 'user_not_registered';

/*Asignacion de privilegios a los roles*/
GRANT ALL PRIVILEGES ON db_test_7b TO 'admin';

GRANT 'admin' TO 'jonathan.leal'@'%';
GRANT 'support' TO 'jeysi.lara'@'%';