/* Creacion de usuarios remotos y asignacion de privilegios */
CREATE USER 'marco.ramirez'@'%' IDENTIFIED BY 'quwerty123';
CREATE USER 'jonathan.leal'@'%' IDENTIFIED BY '240603';
CREATE USER 'josu.oloarte'@'%' IDENTIFIED BY '240234';
/*CREATE USER 'eutiquio.cruz'@'%' IDENTIFIED BY '240046' */
CREATE USER 'jey.lara'@'%' IDENTIFIED BY '240234';
CREATE USER 'rene.david'@'%' IDENTIFIED BY '240107';
CREATE USER 'margaret.rogas'@'%' IDENTIFIED BY '240242';
/*Asignar los privilegios de superusuario*/
GRANT ALL PRIVILEGES ON *.* TO 'jonathan.leal'@'%';

/*
Asignar privilegios CRUD sobre la base db_test_7b.
*/

GRANT SELECT, INSERT, UPDATE, DELETE
ON db_test_7b.*
TO 'josu.oloarte'@'%';

/* ==========================================================================================================================================
CREACION DE ROLES PARA EL SISTEMA E-COMMERCE
   ============================================================================================================================================*/
CREATE ROLE 'superadmin'
CREATE ROLE 'admin';
CREATE ROLE 'seller';
CREATE ROLE 'buyer';
CREATE ROLE 'guest';
CREATE ROLE 'support';
CREATE ROLE 'common';

/* ============================================================
   ASIGNACIÓN DE PRIVILEGIOS A LOS ROLES
   ============================================================ */

/* SUPERADMIN */
GRANT ALL PRIVILEGES
ON *.*
TO 'superadmin';    

/* ADMIN */
GRANT ALL PRIVILEGES
ON db_test_7b.*
TO 'admin';


/* SUPPORT */
GRANT SELECT, INSERT, UPDATE
ON db_test_7b.tb_users
TO 'support';

GRANT SELECT, INSERT, UPDATE
ON db_test_7b.tb_products
TO 'support';

/* SELLER */
GRANT SELECT, INSERT, UPDATE
ON db_test_7b.tb_products
TO 'seller';

/* ============================================================
   ASIGNACIÓN DE ROLES A LOS USUARIOS
   ============================================================ */

-- Este deben ser ustedes
GRANT 'superadmin'
TO 'jonathan.leal'@'%';

-- Este debe ser el Prof. Marco
GRANT 'admin'
TO 'marco.ramirez'@'%';

-- IZQUIERDA
GRANT 'seller'
TO 'josu.oloarte'@'%';

-- DERECHA
GRANT 'seller'
TO 'jey.lara'@'%';
/*GRANT 'seller'
TO 'eutiquio.cruz'@'%';*/

GRANT 'seller'
TO 'rene.david'@'%';

/* ============================================================
   ESTABLECER ROLES PREDETERMINADOS
   ============================================================ */

/*
Esto permite que el rol se active automáticamente cuando
el usuario inicia sesión.
*/

SET DEFAULT ROLE 'admin'
TO 'marco.ramirez'@'%';

SET DEFAULT ROLE 'seller'
TO 'josu.oloarte'@'%';

SET DEFAULT ROLE 'seller'
TO 'jey.lara'@'%';
/*SET DEFAULT ROLE 'seller'
TO 'eutiquio.cruz'@'%';*/
SET DEFAULT ROLE 'seller'
TO 'rene.david'@'%';


/* ============================================================
   VERIFICACIÓN
   ============================================================ */

/* Mostrar usuarios remotos creados */
SELECT "Los usuarios y privilegios han sido creados correctamente" AS mensaje;