/* Creacion de usuarios remotos y asignacion de privilegios */
CREATE USER 'marco.ramirez'@'%' IDENTIFIED BY 'quwerty123';
CREATE USER 'jonathan.leal'@'%' IDENTIFIED BY '240603';
CREATE USER 'jeysi.lara'@'%' IDENTIFIED BY '240234';
CREATE USER 'rene.david'@'%' IDENTIFIED BY '240107';
CREATE USER 'margaret.rogas'@'%' IDENTIFIED BY '240242';

/*Asignar los privilegios de superusuario*/
GRANT ALL PRIVILEGES ON *.* TO 'jonathan.leal'@'%';

/*Asignar los privilegios de lectura, escritura, actualizacion y eliminacion a los usuarios remotos*/
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'marco.ramirez'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'jeysi.lara'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'margaret.rogas'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON `db_test_7b`.* TO 'support';

/*Creacio de roles y asignacion de privilegios a los roles*/
CREATE ROLE 'superadmin'
CREATE ROLE 'admin';
CREATE ROLE 'seller';
CREATE ROLE 'buyer';
CREATE ROLE 'guest';
CREATE ROLE 'support';
CREATE ROLE 'common';
CREATE ROLE 'user_not_registered';
/* ==========================================================================================================================================
CREACION DE ROLES PARA EL SISTEMA E-COMMERCE
   ============================================================================================================================================*/

/*Asignacion de privilegios a los roles*/
GRANT ALL PRIVILEGES ON * TO 'superadmin';

GRANT ALL PRIVILEGES ON db_test_7b TO 'admin';

/* ==========================================================================================================================================
ASIGNACION DE PRIVILEGIOS A LOS ROLES
   ============================================================================================================================================*/

GRANT 'admin' TO 'jonathan.leal'@'%';
GRANT 'support' TO 'jeysi.lara'@'%';
GRANT 'support' TO 'rene.david'@'%';